import * as pdfjsLib from "./vendor/pdf.mjs";

pdfjsLib.GlobalWorkerOptions.workerSrc = "./vendor/pdf.worker.mjs";

const STORAGE_KEY = "whs-calendar-events-v1";
const SETTINGS_KEY = "whs-calendar-google-settings-v1";
const MONTHS = [
  "JANUARY",
  "FEBRUARY",
  "MARCH",
  "APRIL",
  "MAY",
  "JUNE",
  "JULY",
  "AUGUST",
  "SEPTEMBER",
  "OCTOBER",
  "NOVEMBER",
  "DECEMBER",
];

const state = {
  events: loadEvents(),
  activeMonth: "all",
  search: "",
  googleReady: false,
  tokenClient: null,
  accessToken: null,
};

const els = {
  pdfInput: document.querySelector("#pdfInput"),
  fileName: document.querySelector("#fileName"),
  importStatus: document.querySelector("#importStatus"),
  googleStatus: document.querySelector("#googleStatus"),
  clientIdInput: document.querySelector("#clientIdInput"),
  calendarIdInput: document.querySelector("#calendarIdInput"),
  calendarSelect: document.querySelector("#calendarSelect"),
  saveGoogleButton: document.querySelector("#saveGoogleButton"),
  connectButton: document.querySelector("#connectButton"),
  syncButton: document.querySelector("#syncButton"),
  icsButton: document.querySelector("#icsButton"),
  sampleButton: document.querySelector("#sampleButton"),
  clearButton: document.querySelector("#clearButton"),
  searchInput: document.querySelector("#searchInput"),
  selectAllInput: document.querySelector("#selectAllInput"),
  monthTabs: document.querySelector("#monthTabs"),
  eventList: document.querySelector("#eventList"),
  eventTemplate: document.querySelector("#eventTemplate"),
  eventCount: document.querySelector("#eventCount"),
  syncedCount: document.querySelector("#syncedCount"),
  rangeLabel: document.querySelector("#rangeLabel"),
};

hydrateSettings();
bindEvents();
render();

function bindEvents() {
  els.pdfInput.addEventListener("change", handlePdfUpload);
  els.saveGoogleButton.addEventListener("click", saveSettings);
  els.calendarSelect.addEventListener("change", chooseCalendar);
  els.connectButton.addEventListener("click", connectGoogle);
  els.syncButton.addEventListener("click", syncSelectedEvents);
  els.icsButton.addEventListener("click", downloadIcs);
  els.sampleButton.addEventListener("click", render);
  els.clearButton.addEventListener("click", clearEvents);
  els.searchInput.addEventListener("input", () => {
    state.search = els.searchInput.value.trim().toLowerCase();
    renderEvents();
  });
  els.selectAllInput.addEventListener("change", toggleVisibleSelection);
}

async function handlePdfUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;

  els.fileName.textContent = file.name;
  els.importStatus.textContent = "Reading PDF...";

  try {
    const parsed = await parsePdf(file);
    const existingByKey = new Map(state.events.map((item) => [item.key, item]));
    let added = 0;
    let updated = 0;

    parsed.forEach((item) => {
      const previous = existingByKey.get(item.key);
      if (previous) {
        Object.assign(previous, item, {
          selected: previous.selected,
          googleEventId: previous.googleEventId,
          syncedAt: previous.syncedAt,
        });
        updated += 1;
      } else {
        state.events.push(item);
        added += 1;
      }
    });

    sortEvents();
    saveEvents();
    els.importStatus.textContent = `Imported ${added} new event${added === 1 ? "" : "s"} and refreshed ${updated}.`;
    render();
  } catch (error) {
    console.error(error);
    els.importStatus.textContent = `Could not read this PDF: ${error.message}`;
  }
}

async function parsePdf(file) {
  const bytes = new Uint8Array(await file.arrayBuffer());
  const pdf = await pdfjsLib.getDocument({ data: bytes }).promise;
  const events = [];

  for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
    const page = await pdf.getPage(pageNumber);
    const content = await page.getTextContent();
    const items = content.items
      .map((item) => ({
        text: normalizeText(item.str),
        x: item.transform[4],
        centerX: item.transform[4] + (item.width || 0) / 2,
        y: item.transform[5],
      }))
      .filter((item) => item.text);

    events.push(...parseCalendarPage(items, pageNumber));
  }

  return events;
}

function parseCalendarPage(items, pageNumber) {
  const monthItem = items.find((item) => MONTHS.includes(item.text.toUpperCase()));
  const year = getPageYear(items);
  if (!monthItem || !year) return [];

  const monthIndex = MONTHS.indexOf(monthItem.text.toUpperCase());
  const dateItems = items
    .filter((item) => /^\d{2}$/.test(item.text) && item.y < 630 && item.x > 40)
    .map((item) => ({
      ...item,
      day: Number(item.text),
    }));

  const rows = uniqueNumbers(dateItems.map((item) => Math.round(item.y))).sort((a, b) => b - a);
  const cols = uniqueNumbers(dateItems.map((item) => Math.round(item.centerX))).sort((a, b) => a - b);
  const rowBounds = makeBounds(rows, "descending");
  const colBounds = makeBounds(cols, "ascending");
  const dateByCell = new Map();

  dateItems.forEach((item) => {
    const row = indexForValue(item.y, rowBounds);
    const col = indexForValue(item.centerX, colBounds);
    if (row >= 0 && col >= 0) {
      dateByCell.set(`${row}:${col}`, item.day);
    }
  });

  const grouped = new Map();
  items.forEach((item) => {
    const text = item.text.trim();
    const upper = text.toUpperCase();
    if (MONTHS.includes(upper) || upper === "SUNDAY" || upper === "MONDAY" || upper === "TUESDAY" || upper === "WEDNESDAY" || upper === "THURSDAY" || upper === "FRIDAY" || upper === "SATURDAY") return;
    if (/^\d{2}$/.test(text)) return;
    if (item.y > 650 || item.y < 35) return;

    const row = indexForValue(item.y, rowBounds);
    const col = indexForValue(item.centerX, colBounds);
    const day = dateByCell.get(`${row}:${col}`);
    if (!day) return;

    const key = `${year}-${pad(monthIndex + 1)}-${pad(day)}`;
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key).push(item);
  });

  return [...grouped.entries()].map(([date, group]) => {
    const lines = group
      .sort((a, b) => b.y - a.y || a.x - b.x)
      .map((item) => item.text);
    const rawText = joinCalendarLines(lines);
    const time = parseTimeRange(rawText);
    const title = cleanTitle(rawText, time?.matchedText);

    return {
      id: crypto.randomUUID(),
      key: `${date}|${title.toLowerCase()}`,
      sourcePage: pageNumber,
      date,
      title,
      startTime: time?.start ?? "",
      endTime: time?.end ?? "",
      notes: `Imported from ${MONTHS[monthIndex]} ${year} WHS calendar.`,
      selected: true,
      googleEventId: "",
      syncedAt: "",
    };
  });
}

function getPageYear(items) {
  const monthItem = items.find((item) => MONTHS.includes(item.text.toUpperCase()));
  const yearDigits = items
    .filter((item) => /^\d{2}$/.test(item.text) && item.y > 660 && item.x > 1250)
    .sort((a, b) => b.y - a.y)
    .map((item) => item.text)
    .join("");

  if (/^20\d{2}$/.test(yearDigits)) return Number(yearDigits);
  if (!monthItem) return null;

  const pageMonth = MONTHS.indexOf(monthItem.text.toUpperCase());
  const currentYear = new Date().getFullYear();
  return pageMonth < 2 ? currentYear + 1 : currentYear;
}

function joinCalendarLines(lines) {
  return lines
    .join(" ")
    .replace(/\s+([),])/g, "$1")
    .replace(/\(\s+/g, "(")
    .replace(/\s+/g, " ")
    .trim();
}

function cleanTitle(text, timeText) {
  const withoutTime = timeText ? text.replace(timeText, "") : text;
  return withoutTime.replace(/\s+/g, " ").trim() || "WHS Event";
}

function parseTimeRange(text) {
  const match = text.match(/\b(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?\s*[-–]\s*(\d{1,2})(?::(\d{2}))?\s*(AM|PM)\b/i);
  if (!match) return null;

  const [, startHourRaw, startMinuteRaw, startPeriodRaw, endHourRaw, endMinuteRaw, endPeriodRaw] = match;
  const endPeriod = endPeriodRaw.toUpperCase();
  const startPeriod = (startPeriodRaw || endPeriod).toUpperCase();
  return {
    matchedText: match[0],
    start: toTimeValue(Number(startHourRaw), Number(startMinuteRaw || 0), startPeriod),
    end: toTimeValue(Number(endHourRaw), Number(endMinuteRaw || 0), endPeriod),
  };
}

function toTimeValue(hour, minute, period) {
  let normalized = hour % 12;
  if (period === "PM") normalized += 12;
  return `${pad(normalized)}:${pad(minute)}`;
}

function uniqueNumbers(numbers) {
  return [...new Set(numbers)];
}

function makeBounds(values, direction) {
  if (!values.length) return [];
  const bounds = values.map((value, index) => {
    const previous = values[index - 1];
    const next = values[index + 1];
    if (direction === "ascending") {
      return {
        min: previous == null ? value - 170 : (previous + value) / 2,
        max: next == null ? value + 170 : (value + next) / 2,
      };
    }
    return {
      min: next == null ? value - 90 : (value + next) / 2,
      max: previous == null ? value + 70 : (previous + value) / 2,
    };
  });
  return bounds;
}

function indexForValue(value, bounds) {
  return bounds.findIndex((bound) => value >= bound.min && value < bound.max);
}

function normalizeText(text) {
  return text.replace(/\s+/g, " ").trim();
}

function render() {
  sortEvents();
  renderSummary();
  renderTabs();
  renderEvents();
}

function renderSummary() {
  const synced = state.events.filter((event) => event.googleEventId).length;
  els.eventCount.textContent = state.events.length;
  els.syncedCount.textContent = synced;

  if (!state.events.length) {
    els.rangeLabel.textContent = "No PDF yet";
    return;
  }

  const first = formatShortDate(state.events[0].date);
  const last = formatShortDate(state.events[state.events.length - 1].date);
  els.rangeLabel.textContent = `${first} to ${last}`;
}

function renderTabs() {
  const months = new Map();
  state.events.forEach((event) => {
    const monthKey = event.date.slice(0, 7);
    if (!months.has(monthKey)) months.set(monthKey, formatMonthLabel(event.date));
  });

  els.monthTabs.innerHTML = "";
  const allButton = makeMonthButton("all", `All (${state.events.length})`);
  els.monthTabs.append(allButton);

  months.forEach((label, key) => {
    const count = state.events.filter((event) => event.date.startsWith(key)).length;
    els.monthTabs.append(makeMonthButton(key, `${label} (${count})`));
  });
}

function makeMonthButton(key, label) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `month-tab${state.activeMonth === key ? " active" : ""}`;
  button.textContent = label;
  button.addEventListener("click", () => {
    state.activeMonth = key;
    renderTabs();
    renderEvents();
  });
  return button;
}

function renderEvents() {
  const visible = getVisibleEvents();
  els.eventList.innerHTML = "";

  if (!visible.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = state.events.length ? "No events match that view." : "Upload the WHS PDF to start tracking events.";
    els.eventList.append(empty);
    return;
  }

  visible.forEach((eventItem) => {
    const node = els.eventTemplate.content.firstElementChild.cloneNode(true);
    const selected = node.querySelector(".event-select input");
    const title = node.querySelector(".title-input");
    const date = node.querySelector(".date-input");
    const start = node.querySelector(".start-input");
    const end = node.querySelector(".end-input");
    const notes = node.querySelector(".notes-input");
    const syncState = node.querySelector(".sync-state");

    node.querySelector(".month").textContent = formatMonthLabel(eventItem.date, "short");
    node.querySelector(".day").textContent = String(Number(eventItem.date.slice(8, 10)));
    selected.checked = eventItem.selected;
    title.value = eventItem.title;
    date.value = eventItem.date;
    start.value = eventItem.startTime;
    end.value = eventItem.endTime;
    notes.value = eventItem.notes;
    syncState.textContent = eventItem.googleEventId ? "Synced" : "";

    selected.addEventListener("change", () => updateEvent(eventItem.id, { selected: selected.checked }));
    title.addEventListener("change", () => updateEvent(eventItem.id, { title: title.value.trim() || "WHS Event" }));
    date.addEventListener("change", () => updateEvent(eventItem.id, { date: date.value }));
    start.addEventListener("change", () => updateEvent(eventItem.id, { startTime: start.value }));
    end.addEventListener("change", () => updateEvent(eventItem.id, { endTime: end.value }));
    notes.addEventListener("change", () => updateEvent(eventItem.id, { notes: notes.value }));
    node.querySelector(".delete-button").addEventListener("click", () => removeEvent(eventItem.id));

    els.eventList.append(node);
  });
}

function getVisibleEvents() {
  return state.events.filter((event) => {
    const monthMatches = state.activeMonth === "all" || event.date.startsWith(state.activeMonth);
    const searchText = `${event.title} ${event.notes} ${event.date}`.toLowerCase();
    return monthMatches && (!state.search || searchText.includes(state.search));
  });
}

function updateEvent(id, patch) {
  const eventItem = state.events.find((item) => item.id === id);
  if (!eventItem) return;
  const onlySelectionChanged = Object.keys(patch).every((key) => key === "selected");
  Object.assign(eventItem, patch);
  if (!onlySelectionChanged) {
    eventItem.googleEventId = "";
    eventItem.syncedAt = "";
  }
  eventItem.key = `${eventItem.date}|${eventItem.title.toLowerCase()}`;
  sortEvents();
  saveEvents();
  render();
}

function removeEvent(id) {
  state.events = state.events.filter((event) => event.id !== id);
  saveEvents();
  render();
}

function toggleVisibleSelection() {
  const visibleIds = new Set(getVisibleEvents().map((event) => event.id));
  state.events.forEach((event) => {
    if (visibleIds.has(event.id)) event.selected = els.selectAllInput.checked;
  });
  saveEvents();
  renderEvents();
}

function clearEvents() {
  state.events = [];
  saveEvents();
  render();
  els.importStatus.textContent = "Events cleared.";
}

function hydrateSettings() {
  const settings = loadSettings();
  els.clientIdInput.value = settings.clientId || "";
  els.calendarIdInput.value = settings.calendarId || "primary";
}

function saveSettings() {
  localStorage.setItem(
    SETTINGS_KEY,
    JSON.stringify({
      clientId: els.clientIdInput.value.trim(),
      calendarId: els.calendarIdInput.value.trim() || "primary",
    }),
  );
  state.googleReady = false;
  state.tokenClient = null;
  state.accessToken = null;
  els.googleStatus.textContent = "Settings saved.";
}

function chooseCalendar() {
  if (!els.calendarSelect.value) return;
  els.calendarIdInput.value = els.calendarSelect.value;
  saveSettings();
  els.googleStatus.textContent = `Using ${els.calendarSelect.selectedOptions[0].textContent}.`;
}

async function connectGoogle() {
  const { clientId } = loadSettings();
  if (!clientId) {
    els.googleStatus.textContent = "Add your OAuth Client ID first.";
    return;
  }

  try {
    await waitForGoogleScripts();
    await new Promise((resolve, reject) => {
      window.gapi.load("client", {
        callback: resolve,
        onerror: () => reject(new Error("Google API client failed to load.")),
      });
    });
    await window.gapi.client.init({
      discoveryDocs: ["https://www.googleapis.com/discovery/v1/apis/calendar/v3/rest"],
    });
    state.tokenClient = window.google.accounts.oauth2.initTokenClient({
      client_id: clientId,
      scope: "https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/calendar.calendarlist.readonly",
      callback: async (response) => {
        if (response.error) {
          els.googleStatus.textContent = response.error;
          return;
        }
        state.accessToken = response.access_token;
        window.gapi.client.setToken(response);
        state.googleReady = true;
        els.googleStatus.textContent = "Connected to Google Calendar.";
        await loadGoogleCalendars();
      },
    });
    state.tokenClient.requestAccessToken({ prompt: "consent" });
  } catch (error) {
    console.error(error);
    els.googleStatus.textContent = error.message;
  }
}

async function loadGoogleCalendars() {
  try {
    const response = await window.gapi.client.calendar.calendarList.list({
      minAccessRole: "writer",
      showHidden: true,
    });
    const calendars = response.result.items || [];
    const savedCalendarId = loadSettings().calendarId || "primary";

    els.calendarSelect.innerHTML = "";
    if (!calendars.length) {
      els.calendarSelect.append(new Option("No writable calendars found", ""));
      return;
    }

    calendars.forEach((calendar) => {
      const label = calendar.primary ? `${calendar.summary} (Primary)` : calendar.summary;
      const option = new Option(label, calendar.id);
      option.selected = calendar.id === savedCalendarId;
      els.calendarSelect.append(option);
    });

    if (!calendars.some((calendar) => calendar.id === savedCalendarId)) {
      els.calendarSelect.prepend(new Option(`Current ID: ${savedCalendarId}`, savedCalendarId, true, true));
    }
    els.googleStatus.textContent = "Connected. Choose the family calendar, then sync selected events.";
  } catch (error) {
    console.error(error);
    els.googleStatus.textContent = "Connected, but calendar list could not be loaded. Paste the family calendar ID manually.";
  }
}

async function syncSelectedEvents() {
  const selected = state.events.filter((event) => event.selected);
  const { calendarId } = loadSettings();
  if (!selected.length) {
    els.googleStatus.textContent = "Select at least one event to sync.";
    return;
  }
  if (!state.googleReady) {
    els.googleStatus.textContent = "Connect to Google Calendar first.";
    return;
  }

  els.syncButton.disabled = true;
  let synced = 0;
  try {
    for (const eventItem of selected) {
      const resource = toGoogleResource(eventItem);
      const response = eventItem.googleEventId
        ? await window.gapi.client.calendar.events.update({
            calendarId,
            eventId: eventItem.googleEventId,
            resource,
          })
        : await window.gapi.client.calendar.events.insert({
            calendarId,
            resource,
          });
      eventItem.googleEventId = response.result.id;
      eventItem.syncedAt = new Date().toISOString();
      synced += 1;
      els.googleStatus.textContent = `Synced ${synced} of ${selected.length}...`;
    }
    saveEvents();
    render();
    els.googleStatus.textContent = `Synced ${synced} event${synced === 1 ? "" : "s"} to Google Calendar.`;
  } catch (error) {
    console.error(error);
    els.googleStatus.textContent = error.result?.error?.message || error.message || "Google sync failed.";
  } finally {
    els.syncButton.disabled = false;
  }
}

function toGoogleResource(eventItem) {
  const description = `${eventItem.notes || ""}\n\nManaged from WHS Calendar Tracker.`.trim();
  if (!eventItem.startTime) {
    return {
      summary: eventItem.title,
      description,
      start: { date: eventItem.date },
      end: { date: addDays(eventItem.date, 1) },
    };
  }

  const start = `${eventItem.date}T${eventItem.startTime}:00`;
  const endTime = eventItem.endTime || eventItem.startTime;
  const endDate = endTime <= eventItem.startTime ? addDays(eventItem.date, 1) : eventItem.date;
  return {
    summary: eventItem.title,
    description,
    start: { dateTime: `${start}`, timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone },
    end: { dateTime: `${endDate}T${endTime}:00`, timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone },
  };
}

function downloadIcs() {
  const selected = state.events.filter((event) => event.selected);
  if (!selected.length) {
    els.googleStatus.textContent = "Select at least one event for the ICS file.";
    return;
  }
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//WHS Calendar Tracker//EN",
    "CALSCALE:GREGORIAN",
    ...selected.flatMap(toIcsEvent),
    "END:VCALENDAR",
  ];
  const blob = new Blob([lines.join("\r\n")], { type: "text/calendar" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "whs-calendar-events.ics";
  link.click();
  URL.revokeObjectURL(url);
}

function toIcsEvent(eventItem) {
  const uid = `${eventItem.key.replace(/[^a-z0-9]/gi, "-")}@whs-calendar`;
  const stamp = formatIcsDateTime(new Date());
  const lines = ["BEGIN:VEVENT", `UID:${uid}`, `DTSTAMP:${stamp}`, `SUMMARY:${escapeIcs(eventItem.title)}`, `DESCRIPTION:${escapeIcs(eventItem.notes || "")}`];

  if (eventItem.startTime) {
    const endTime = eventItem.endTime || eventItem.startTime;
    const endDate = endTime <= eventItem.startTime ? addDays(eventItem.date, 1) : eventItem.date;
    lines.push(`DTSTART:${eventItem.date.replaceAll("-", "")}T${eventItem.startTime.replace(":", "")}00`);
    lines.push(`DTEND:${endDate.replaceAll("-", "")}T${endTime.replace(":", "")}00`);
  } else {
    lines.push(`DTSTART;VALUE=DATE:${eventItem.date.replaceAll("-", "")}`);
    lines.push(`DTEND;VALUE=DATE:${addDays(eventItem.date, 1).replaceAll("-", "")}`);
  }

  lines.push("END:VEVENT");
  return lines;
}

function waitForGoogleScripts() {
  return new Promise((resolve, reject) => {
    const started = Date.now();
    const timer = window.setInterval(() => {
      if (window.google?.accounts?.oauth2 && window.gapi) {
        window.clearInterval(timer);
        resolve();
      } else if (Date.now() - started > 10000) {
        window.clearInterval(timer);
        reject(new Error("Google scripts are not available yet."));
      }
    }, 100);
  });
}

function loadSettings() {
  try {
    return JSON.parse(localStorage.getItem(SETTINGS_KEY)) || {};
  } catch {
    return {};
  }
}

function loadEvents() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  } catch {
    return [];
  }
}

function saveEvents() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state.events));
}

function sortEvents() {
  state.events.sort((a, b) => `${a.date} ${a.startTime}`.localeCompare(`${b.date} ${b.startTime}`));
}

function formatMonthLabel(date, style = "long") {
  return new Date(`${date}T12:00:00`).toLocaleDateString(undefined, {
    month: style,
    year: style === "long" ? "numeric" : undefined,
  });
}

function formatShortDate(date) {
  return new Date(`${date}T12:00:00`).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

function formatIcsDateTime(date) {
  return date.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
}

function addDays(date, days) {
  const value = new Date(`${date}T12:00:00`);
  value.setDate(value.getDate() + days);
  return value.toISOString().slice(0, 10);
}

function escapeIcs(value) {
  return String(value).replace(/\\/g, "\\\\").replace(/\n/g, "\\n").replace(/,/g, "\\,").replace(/;/g, "\\;");
}

function pad(value) {
  return String(value).padStart(2, "0");
}
