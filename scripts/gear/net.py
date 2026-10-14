"""Polite HTTP: robots.txt, per-host pacing, bounded retries, honest failures.

Every failure is raised as FetchError with a `kind`, so a source that could not
be read is reported as such instead of looking like "no deals today".
"""
from __future__ import annotations

import http.client
import json
import re
import socket
import ssl
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPSHandler, Request, build_opener

USER_AGENT = (
    "GearDealsMonitor/3.0 (personal price tracker; "
    "+https://github.com/stevembaron/projects)"
)
RETRY_STATUS = {429, 500, 502, 503, 504}
BLOCK_STATUS = {401, 403, 407, 451}
BLOCK_MARKERS = (
    "verify you are human",
    "attention required",
    "sorry, you have been blocked",
    "request blocked",
    "access denied",
    "captcha",
    "challenge-platform",
    "awswaf",
)


class FetchError(Exception):
    """kind is one of: robots, blocked, http, network, parse."""

    def __init__(self, kind: str, message: str, status: int | None = None, url: str = "") -> None:
        super().__init__(message)
        self.kind = kind
        self.status = status
        self.url = url


_ADDRESSES: dict = {}


def _connect_ipv4_first(address, timeout=None, source_address=None, **_ignored):
    """urllib tries each resolved address for the full timeout. Hosts that publish
    an unreachable IPv6 address would otherwise stall every request, so resolve
    and try IPv4 first and cap the per-address connect time."""
    host, port = address
    candidates = _ADDRESSES.get((host, port))
    if candidates is None:
        try:
            # Asking for IPv4 only avoids waiting on slow or missing AAAA answers.
            candidates = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
        except socket.gaierror:
            candidates = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
        _ADDRESSES[(host, port)] = candidates
    failure: OSError | None = None
    for family, kind, protocol, _name, target in candidates:
        sock = None
        try:
            sock = socket.socket(family, kind, protocol)
            sock.settimeout(min(timeout, 8) if isinstance(timeout, (int, float)) else 8)
            if source_address:
                sock.bind(source_address)
            sock.connect(target)
            sock.settimeout(timeout if isinstance(timeout, (int, float)) else None)
            return sock
        except OSError as error:
            failure = error
            if sock is not None:
                sock.close()
    raise failure or OSError("No address found for " + str(host))


class _Connection(http.client.HTTPSConnection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._create_connection = _connect_ipv4_first


class _Handler(HTTPSHandler):
    def __init__(self):
        self._gear_context = ssl.create_default_context()
        super().__init__(context=self._gear_context)

    def https_open(self, request):
        return self.do_open(_Connection, request, context=self._gear_context)


def default_opener():
    return build_opener(_Handler()).open


def _rule_regex(pattern: str) -> re.Pattern:
    anchored = pattern.endswith("$")
    body = pattern[:-1] if anchored else pattern
    return re.compile("".join(".*" if c == "*" else re.escape(c) for c in body) + ("$" if anchored else ""))


class Robots:
    """robots.txt matcher with the * and $ wildcards Shopify stores rely on.

    urllib.robotparser treats those characters literally, which would report
    disallowed filter and sort URLs as allowed.
    """

    def __init__(self, text: str = "", agent: str = "geardealsmonitor") -> None:
        groups: dict[str, list[tuple[bool, str]]] = {}
        current: list[str] = []
        collecting_agents = False
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            field, value = (part.strip() for part in line.split(":", 1))
            field = field.lower()
            if field == "user-agent":
                if not collecting_agents:
                    current = []
                collecting_agents = True
                current.append(value.lower())
                groups.setdefault(value.lower(), [])
            elif field in ("allow", "disallow"):
                collecting_agents = False
                if value:
                    for name in current:
                        groups[name].append((field == "allow", value))
            else:
                collecting_agents = False
        specific = [rules for name, rules in groups.items() if name != "*" and name in agent]
        self.rules = [(allow, pattern, _rule_regex(pattern)) for allow, pattern in (specific[0] if specific else groups.get("*", []))]

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        target = (parts.path or "/") + ("?" + parts.query if parts.query else "")
        best_length, verdict = -1, True
        for allow, pattern, regex in self.rules:
            if regex.match(target):
                length = len(pattern)
                # Longest rule wins; Allow wins a tie.
                if length > best_length or (length == best_length and allow):
                    best_length, verdict = length, allow
        return verdict


def looks_blocked(body: str) -> bool:
    sample = body[:6000].lower()
    return any(marker in sample for marker in BLOCK_MARKERS)


class Client:
    def __init__(
        self,
        min_delay: float = 1.5,
        timeout: float = 35,
        retries: int = 2,
        user_agent: str = USER_AGENT,
        opener: Callable[..., Any] | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
        respect_robots: bool = True,
    ) -> None:
        self.min_delay = min_delay
        self.timeout = timeout
        self.retries = retries
        self.user_agent = user_agent
        self.respect_robots = respect_robots
        self._open = opener or default_opener()
        self._sleep = sleep
        self._clock = clock
        self._last: dict[str, float] = {}
        self._robots: dict[str, Robots] = {}
        self.requests = 0
        self.bytes = 0

    def _pace(self, host: str) -> None:
        last = self._last.get(host)
        if last is not None:
            wait = self.min_delay - (self._clock() - last)
            if wait > 0:
                self._sleep(wait)
        self._last[host] = self._clock()

    def _raw(self, url: str, accept: str) -> str:
        host = urlsplit(url).netloc
        request = Request(url, headers={"User-Agent": self.user_agent, "Accept": accept, "Accept-Language": "en-US,en;q=0.8"})
        failure: FetchError | None = None
        for attempt in range(self.retries + 1):
            self._pace(host)
            self.requests += 1
            try:
                with self._open(request, timeout=self.timeout) as response:
                    data = response.read()
                    charset = response.headers.get_content_charset() or "utf-8"
                self.bytes += len(data)
                return data.decode(charset, errors="replace")
            except HTTPError as error:
                if error.code in BLOCK_STATUS:
                    raise FetchError("blocked", f"HTTP {error.code}: the retailer refused the request", error.code, url)
                failure = FetchError("http", f"HTTP {error.code}", error.code, url)
                if error.code not in RETRY_STATUS:
                    raise failure
            except (URLError, TimeoutError, OSError) as error:
                failure = FetchError("network", f"Network error: {getattr(error, 'reason', error)}", None, url)
            if attempt < self.retries:
                self._sleep(2.0 * (attempt + 1))
        assert failure is not None
        raise failure

    def robots(self, url: str) -> Robots:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._robots:
            try:
                self._robots[origin] = Robots(self._raw(origin + "/robots.txt", "text/plain"))
            except FetchError as error:
                # A missing robots.txt permits crawling. Anything else is unknown, so stay out.
                if error.status == 404:
                    self._robots[origin] = Robots("")
                else:
                    raise FetchError("robots", f"Could not read robots.txt ({error})", error.status, url)
        return self._robots[origin]

    def get_text(self, url: str, accept: str = "text/html,application/xhtml+xml") -> str:
        if self.respect_robots and not self.robots(url).allowed(url):
            raise FetchError("robots", "robots.txt disallows this URL", None, url)
        body = self._raw(url, accept)
        if looks_blocked(body) and not body.lstrip().startswith(("{", "[")):
            raise FetchError("blocked", "The retailer served a bot-challenge page", None, url)
        return body

    def get_json(self, url: str) -> Any:
        body = self.get_text(url, "application/json")
        try:
            return json.loads(body)
        except ValueError:
            raise FetchError("parse", "Expected JSON but the response was not JSON", None, url)
