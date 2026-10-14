"""Offline regression tests for the gear deal engine."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from gear import adapters, aibrief, brief, fit, history, pipeline, prefs as preferences, site, textparse as tp, valuation  # noqa: E402
from gear.net import Client, FetchError, Robots  # noqa: E402

NOW = "2026-10-14T12:00:00+00:00"
PREFS = preferences.load(ROOT / "config" / "deal_preferences.json")
ME = PREFS["profiles"][0]
GEARTRADE = {"id": "geartrade", "name": "Geartrade", "base_url": "https://geartrade.com", "seller": {"trust": 0.7}, "tag_conditions": {"RetailVendorPartner": "new"}}


def product(title, variants, tags=(), options=("Size",), body="", ptype="", vendor=""):
    return {"title": title, "handle": title.lower().replace(" ", "-")[:40], "tags": list(tags), "product_type": ptype, "vendor": vendor,
            "body_html": body, "options": [{"name": o} for o in options], "images": [{"src": "https://cdn.shopify.com/x.jpg"}],
            "published_at": NOW, "variants": [dict({"id": i + 1, "available": True}, **v) for i, v in enumerate(variants)]}


def offer(title, price, lengths=(170,), compare=None, condition="new", source="evo", year=2026, **extra):
    o = {"id": tp.model_key(title + source + str(price)).replace(" ", "")[:14], "source_id": source, "source": source, "seller": {"trust": 0.9},
         "url": f"https://{source}.example/p/{title.replace(' ', '-')}", "title": title, "brand": tp.detect_brand(title),
         "model_year": year, "gender": tp.gender(title), "kind": "ski", "condition": condition, "bindings": {"included": False},
         "image": None, "shipping": None, "price_scope": "exact", "observed_at": NOW,
         "variants": [{"vid": str(n), "label": f"{n} cm", "length_cm": n, "size": None, "price": price, "compare_at": compare, "available": True} for n in lengths]}
    o["model"] = tp.model_name(title, o["brand"])
    o["model_key"] = tp.model_key(o["model"])
    o["waist_mm"] = tp.waist_mm(o["model"])
    o.update(extra)
    return o


class TextParse(unittest.TestCase):
    def test_brand_model_year(self):
        self.assertEqual(tp.detect_brand("Völkl Mantra M6 Skis 2024"), "Volkl")
        self.assertEqual(tp.detect_brand("Black Diamond Helio Carbon 95"), "Black Diamond")
        self.assertEqual(tp.model_name("Peak Skis Peak 98 By Dav Skis 2025", "Peak"), "Peak 98 By Dav")
        self.assertEqual(tp.model_key("M-Pro 99"), "mpro 99")
        self.assertEqual(tp.model_key("Mindbender 99Ti"), "mindbender 99 ti")
        self.assertEqual(tp.model_year("24/25 MSP CC"), 2025)
        self.assertEqual(tp.model_year("Ski", ["Season: 2026"]), 2026)

    def test_length_is_never_waist(self):
        title = "Candide Skis BC 111 2026 - 181cm"
        self.assertEqual(tp.waist_mm(tp.model_name(title, "Candide")), 111)
        self.assertEqual(tp.length_cm(title, allow_bare=False), 181)
        self.assertIsNone(tp.waist_mm("Ski 2025 $450"))
        self.assertEqual(tp.length_cm("163"), 163)

    def test_bindings_condition_gender_size(self):
        self.assertTrue(tp.bindings("2026 Atomic Bent 100 w/ Atomic Strive 11 Demo Bindings")["demo"])
        self.assertEqual(tp.bindings("Sender Soul 102 + KNX12 Mens Demo Skis")["model"], "KNX12")
        self.assertFalse(tp.bindings("Faction Prodigy flat")["included"])
        self.assertEqual(tp.condition("UnNew With Tags"), "new_with_tags")
        self.assertEqual(tp.condition("Brand new-with tags / 164"), "new_with_tags")
        self.assertEqual(tp.condition("Excellent"), "excellent")
        self.assertEqual(tp.condition('ALLPLAY "X" BLEMISH'), "blem")
        self.assertEqual(tp.gender("Line Chronic 94 Skis", ["gender_mens", "gender_womens"]), "unisex")
        self.assertEqual(tp.gender("Nordica Santa Ana 93 W Skis"), "womens")
        self.assertEqual(tp.gender("Faction La Machine Grom"), "kids")
        self.assertEqual(tp.clothing_size("Estimated M"), "M")
        self.assertTrue(tp.SINGLE_SKI.search("Single Skis"))


class Net(unittest.TestCase):
    ROBOTS = "User-agent: *\nDisallow: /search\nDisallow: /collections/*sort_by*\nDisallow: */collections/*filter*&*filter*\n"

    def test_robots_wildcards(self):
        r = Robots(self.ROBOTS)
        self.assertFalse(r.allowed("https://x.com/search?q=stio"))
        self.assertFalse(r.allowed("https://x.com/collections/skis?sort_by=price"))
        self.assertTrue(r.allowed("https://x.com/collections/stio/products.json?limit=250&page=2"))
        self.assertTrue(Robots("User-agent: *\nDisallow: /a\nAllow: /a").allowed("https://x.com/a"))

    def test_client_retries_and_blocks(self):
        from urllib.error import HTTPError

        class Resp:
            def __init__(self, body): self.body, self.headers = body.encode(), type("H", (), {"get_content_charset": lambda s: "utf-8"})()
            def read(self): return self.body
            def __enter__(self): return self
            def __exit__(self, *a): return False

        calls = []

        def opener(request, timeout):
            calls.append(request.full_url)
            if request.full_url.endswith("robots.txt"):
                return Resp(self.ROBOTS)
            if len([c for c in calls if "products" in c]) == 1:
                raise HTTPError(request.full_url, 503, "busy", {}, None)
            return Resp('{"products": []}')

        client = Client(opener=opener, sleep=lambda s: None)
        self.assertEqual(client.get_json("https://x.com/collections/a/products.json"), {"products": []})
        with self.assertRaises(FetchError) as caught:
            client.get_json("https://x.com/search?q=a")
        self.assertEqual(caught.exception.kind, "robots")

        def forbidden(request, timeout):
            if request.full_url.endswith("robots.txt"):
                return Resp("")
            raise HTTPError(request.full_url, 403, "no", {}, None)
        with self.assertRaises(FetchError) as caught:
            Client(opener=forbidden, sleep=lambda s: None).get_json("https://y.com/p.json")
        self.assertEqual(caught.exception.kind, "blocked")


class Adapters(unittest.TestCase):
    def test_geartrade_gannett_peak(self):
        p = product("Stio Gannett Peak Half Zip - Men's", [{"option1": "M", "option2": "Red", "title": "M / Red", "price": "76.45", "compare_at_price": "139.00"}],
                    tags=["Brand:stio", "ConsignmentItem", "Mens"], options=("Size", "Color"),
                    body='This is in <span class="condition">UnNew With Tags</span> condition.')
        feed = {"collection": "stio", "kind": "clothing", "condition_from": "body_html", "genders": ["mens", "unisex"]}
        [o] = adapters.shopify_offers(p, GEARTRADE, feed, NOW)
        self.assertEqual((o["kind"], o["condition"], o["variants"][0]["size"], o["variants"][0]["price"]), ("clothing", "new_with_tags", "M", 76.45))

    def test_classification_and_conditions(self):
        feed = {"collection": "skis", "kind": "ski"}
        pkg = product("2026 Atomic Bent 100 w/ Atomic Strive 11 Demo Bindings", [{"option1": "172cm", "option3": "Used", "title": "172cm / Black / Used", "price": "400"}], options=("Size", "Color", "Condition"))
        [o] = adapters.shopify_offers(pkg, GEARTRADE, feed, NOW)
        self.assertEqual((o["kind"], o["condition"]), ("ski", "demo"))
        partner = product("Faction Dancer 3 Skis 2026 - 183cm", [{"option1": "183cm", "title": "183cm", "price": "500"}], tags=["RetailVendorPartner"])
        self.assertEqual(adapters.shopify_offers(partner, GEARTRADE, feed, NOW)[0]["condition"], "new")
        shirt = product("Logo Shirt", [{"option1": "Large", "title": "Large", "price": "30"}])
        self.assertEqual(adapters.shopify_offers(shirt, GEARTRADE, feed, NOW), [])
        junior = product("2025 Atomic Redster J2 70-90cm", [{"option1": "80cm", "title": "80cm", "price": "100"}])
        self.assertEqual(adapters.shopify_offers(junior, GEARTRADE, feed, NOW), [])
        binding = product("Salomon Strive 16 MN Binding", [{"title": "Default", "price": "150"}])
        self.assertEqual(adapters.shopify_offers(binding, GEARTRADE, {"collection": "b", "kind": "auto"}, NOW)[0]["kind"], "binding")
        shipped = product("Line Chronic 94 Skis", [{"option1": "171CM", "title": "171CM", "price": "300", "compare_at_price": "0.00"}], tags=["ship_fee_flatrate_19"])
        o = adapters.shopify_offers(shipped, GEARTRADE, feed, NOW)[0]
        self.assertEqual(o["shipping"]["cost"], 19.0)
        self.assertIsNone(o["variants"][0]["compare_at"])

    def test_failures_are_reported(self):
        class Fake:
            def get_json(self, url):
                raise FetchError("blocked", "HTTP 403")
        report = adapters.collect_shopify({"id": "x", "base_url": "https://x", "feeds": [{"collection": "a"}]}, Fake(), NOW)
        self.assertEqual(report.status, "blocked")
        self.assertTrue(report.error)


class History(unittest.TestCase):
    def test_changes_and_gone(self):
        h = history.empty()
        a = offer("Atomic Bent 100 Skis", 500, source="evo")
        history.update(h, [a], [{"source_id": "evo", "status": "ok"}], "2026-10-10T00:00:00+00:00")
        history.update(h, [dict(a, variants=[dict(a["variants"][0], price=420)])], [{"source_id": "evo", "status": "ok"}], "2026-10-12T00:00:00+00:00")
        entry = h["variants"][history.variant_key(a, a["variants"][0])]
        self.assertEqual(len(entry["p"]), 2)
        stats = history.variant_stats(entry, 420, NOW)
        self.assertEqual((stats["previous_price"], stats["change"], stats["low_90"]), (500, -80, 420))
        history.update(h, [], [{"source_id": "evo", "status": "failed"}], NOW)
        self.assertFalse(h["offers"][a["id"]].get("gone"), "a failed source never makes listings disappear")
        events = history.update(h, [], [{"source_id": "evo", "status": "ok"}], NOW)
        self.assertIn(a["id"], events["gone_offers"])


class Valuation(unittest.TestCase):
    def test_headline_discount_does_not_decide(self):
        now = datetime(2026, 10, 14, tzinfo=timezone.utc)
        old = offer("K2 Mindbender 99Ti Skis", 300, compare=1000, year=2023, source="a")
        new = offer("Nordica Enforcer 99 Skis", 650, compare=1000, year=2027, source="b")
        market = valuation.build_market([old, new])
        v_old = valuation.value_offer(old, market, {}, now)
        v_new = valuation.value_offer(new, market, {}, now)
        self.assertGreater(v_new["score"], v_old["score"], "35% off a current model beats 70% off a 4-season-old one")
        self.assertTrue(any("model's age" in f for f in v_old["flags"]))

    def test_no_evidence_no_fair_price(self):
        o = offer("Mystery Ski", 300, compare=None, year=None, brand=None)
        v = valuation.value_offer(o, valuation.build_market([o]), {}, datetime(2026, 10, 14, tzinfo=timezone.utc))
        self.assertIsNone(v["fmv"])
        self.assertEqual(v["confidence"], "low")

    def test_corroborated_list_price(self):
        entry = {"claims": {"a": {800.0}, "b": {799.0}, "c": {1200.0}}}
        price, basis, stores = valuation.list_price_evidence(entry, 1200.0)
        self.assertEqual((stores, round(price)), (2, 800))


class Fit(unittest.TestCase):
    def item(self, **kw):
        base = {"id": "x", "kind": "ski", "title": "Test Ski", "brand": "Atomic", "model_key": "bent 100", "gender": "unisex", "condition": "new",
                "category": "all_mountain_wide", "waist_mm": 100, "playful": 5, "demanding": 2, "level": ["intermediate", "expert"],
                "price": 400, "score": 70, "confidence": "high", "price_scope": "exact", "in_stock": True, "fresh": True,
                "variants": [{"label": "170 cm", "length_cm": 170, "price": 400, "available": True}], "bindings": {}}
        base.update(kw)
        return base

    def test_lengths_budget_gender_style(self):
        self.assertTrue(fit.evaluate(self.item(variants=[{"label": "180 cm", "length_cm": 180, "price": 400}]), ME, PREFS)["hard"])
        self.assertTrue(any("short" in c for c in fit.evaluate(self.item(variants=[{"label": "167 cm", "length_cm": 167, "price": 400}]), ME, PREFS)["cons"]))
        self.assertTrue(fit.evaluate(self.item(gender="womens"), ME, PREFS)["hard"])
        self.assertTrue(fit.evaluate(self.item(price=900, variants=[{"label": "170 cm", "length_cm": 170, "price": 900}]), ME, PREFS)["hard"])
        self.assertTrue(fit.evaluate(self.item(level=["beginner", "intermediate"]), ME, PREFS)["hard"])
        playful = fit.evaluate(self.item(), ME, PREFS)["score"]
        carver = fit.evaluate(self.item(playful=1, demanding=4), ME, PREFS)["score"]
        self.assertGreater(playful, carver + 30)

    def test_quiver_duplicate_and_verdicts(self):
        dup = fit.evaluate(self.item(brand="Rossignol", model_key="sender soul 102"), ME, PREFS)
        self.assertEqual(dup["duplicate"], "Rossignol Sender Soul 102")
        distinct = dict(category="freeride", waist_mm=108, score=82)
        good = fit.evaluate(self.item(**distinct), ME, PREFS)
        self.assertEqual(fit.verdict(self.item(**distinct), good)[0], "buy_now")
        self.assertEqual(fit.verdict(self.item(**dict(distinct, fresh=False)), good)[0], "strong")
        self.assertEqual(fit.verdict(self.item(score=82), fit.evaluate(self.item(score=82), ME, PREFS))[0], "strong", "near-duplicate needs 88 for Buy now")
        self.assertEqual(fit.verdict(self.item(score=30), good, target=450)[0], "buy_now")
        hidden = fit.evaluate(self.item(), ME, dict(PREFS, dismissed=["x"]))
        self.assertEqual(fit.verdict(self.item(), hidden), ("pass", "You dismissed this"))


class FitParity(unittest.TestCase):
    def test_python_and_browser_agree(self):
        jsc = Path("/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc")
        runner = [str(jsc)] if jsc.exists() else ([shutil.which("node")] if shutil.which("node") else None)
        if not runner:
            self.skipTest("no JavaScript runtime")
        f = Fit()
        family = PREFS["profiles"][1]
        learned = dict(PREFS, learned={"brands": {"Atomic": 2}, "categories": {"powder": 3}})
        items = [f.item(), f.item(playful=2, demanding=4), f.item(gender="womens"), f.item(variants=[{"label": "167 cm", "length_cm": 167, "price": 380}]),
                 f.item(variants=[{"label": "176.5 cm", "length_cm": 176.5, "price": 300}]), f.item(playful=None, demanding=None, category=None),
                 f.item(category="touring"), f.item(category="powder", waist_mm=115), f.item(brand="Rossignol", model_key="sender soul 102 ti"),
                 f.item(kind="clothing", variants=[{"label": "M", "size": "M", "price": 70}], price=70, condition="fair"),
                 f.item(kind="clothing", variants=[{"label": "L", "size": "L", "price": 70}], price=70), f.item(kind="binding", price=600),
                 f.item(bindings={"included": True, "demo": True}), f.item(level=["beginner", "intermediate"]), f.item(variants=[])]
        vectors = []
        for item in items:
            for profile, glob in ((ME, PREFS), (family, PREFS), (ME, learned)):
                result = fit.evaluate(item, profile, glob)
                vectors.append({"item": item, "profile": profile, "global": glob, "expected": {"fit": result, "verdict": list(fit.verdict(item, result))}})
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "v.json").write_text(json.dumps(vectors))
            script = Path(tmp, "run.js")
            body = f"const V = JSON.parse({json.dumps(json.dumps(vectors))});\n" + (ROOT / "assets" / "fit.js").read_text() + """
const F = globalThis.GearFit || module.exports;
const out = V.map(v => { const r = F.evaluate(v.item, v.profile, v.global); return {fit: r, verdict: F.verdict(v.item, r)}; });
(typeof print === 'function' ? print : console.log)(JSON.stringify(out));"""
            if runner[0].endswith("node"):
                body = "var module = {exports: {}};\n" + body
            script.write_text(body)
            output = subprocess.run(runner + [str(script)], capture_output=True, text=True, timeout=60)
        self.assertEqual(output.returncode, 0, output.stderr)
        actual = json.loads(output.stdout)
        for vector, got in zip(vectors, actual):
            self.assertEqual(got, vector["expected"])


class BriefAndSite(unittest.TestCase):
    def dataset(self):
        offers = [offer("Atomic Bent 100 Skis", 420, compare=800, source="evo", year=2026),
                  offer("Atomic Bent 100 Skis", 640, compare=800, source="shop", year=2026),
                  offer("Nordica Santa Ana 93 W Skis", 300, compare=800, lengths=(158,), source="evo", year=2026),
                  offer("Volkl Mantra M6 Skis", 900, compare=900, source="evo", year=2027)]
        h = history.empty()
        history.update(h, offers, [{"source_id": "evo", "status": "ok"}, {"source_id": "shop", "status": "ok"}], NOW)
        return pipeline.build(offers, [{"source_id": "evo", "name": "evo", "status": "ok"}, {"source_id": "shop", "name": "shop", "status": "ok"}], h, PREFS, NOW, {}, evaluated_at=NOW)

    def test_pipeline_publishes_deals_only_and_links_stores(self):
        ds = self.dataset()
        titles = [i["title"] for i in ds["items"]]
        self.assertNotIn("Volkl Mantra M6 Skis", titles, "full-price new skis are not published")
        bent = [i for i in ds["items"] if i["source_id"] == "evo" and "Bent" in i["title"]][0]
        self.assertEqual(bent["also_at"][0]["source"], "shop")
        self.assertIn("me", bent["verdict"])

    def test_brief_numbers_come_from_facts(self):
        ds = self.dataset()
        facts = brief.facts(ds, "ski", "me")
        house = brief.house_brief(facts)
        self.assertTrue(house["headline"] and house["sections"])
        allowed = json.dumps(facts)
        text = " ".join(l["text"] if isinstance(l, dict) else l for s in house["sections"] for l in s["lines"])
        for picked in facts["picks"]:
            self.assertNotEqual(picked["title"], "Nordica Santa Ana 93 W Skis")
        self.assertTrue(text)
        self.assertTrue(allowed)

    def test_ai_reply_validation(self):
        ds = self.dataset()
        pkt = aibrief.packet(ds, brief.facts(ds, "ski", "me"), brief.facts(ds, "clothing", "me"))
        ref = next(iter(pkt["listings"]))
        price = pkt["listings"][ref]["price"]
        good = {"snapshot_id": pkt["snapshot_id"], "headline": "A quiet day with one good Bent", "dek": "",
                "sections": [{"title": "Pick", "body": f"The Bent is ${price:.2f} today.", "refs": [ref]}]}
        accepted, errors = aibrief.validate(json.dumps(good), pkt)
        self.assertEqual(errors, [])
        self.assertTrue(accepted)
        for change in ({"snapshot_id": "nope"}, {"sections": [{"title": "x", "body": "Only $12,345 today.", "refs": [ref]}]},
                       {"sections": [{"title": "x", "body": "See https://evo.com", "refs": []}]},
                       {"sections": [{"title": "x", "body": "ok", "refs": ["missing"]}]}):
            self.assertIsNone(aibrief.validate(dict(good, **change), pkt)[0], change)
        self.assertEqual(aibrief.validate("not json", pkt)[1], ["The reply is not valid JSON"])

    def test_site_build_and_carry_over(self):
        ds = self.dataset()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "assets", root / "assets")
            pkt = aibrief.packet(ds, brief.facts(ds, "ski", "me"))
            site.build(root, ds, {"house": {"ski": brief.house_brief(brief.facts(ds, "ski", "me"))}, "generated_at": NOW}, pkt)
            data = (root / "ski-deals" / "data.js").read_text()
            self.assertNotIn("</script", data)
            json.loads(data[len("window.GEAR="):-2])
            import xml.dom.minidom
            xml.dom.minidom.parse(str(root / "ski-deals" / "alerts.xml"))
            self.assertIn("refresh", (root / "clothing-deals" / "index.html").read_text())
        previous = [offer("Atomic Bent 100 Skis", 420, source="gone", observed_at=(datetime(2026, 10, 14, tzinfo=timezone.utc) - timedelta(hours=10)).isoformat())]
        kept = pipeline.carry_over([], previous, [{"source_id": "gone", "status": "failed"}], NOW, 72)
        self.assertTrue(kept and kept[0]["stale"])
        self.assertEqual(pipeline.carry_over([], previous, [{"source_id": "gone", "status": "failed"}], NOW, 5), [])


class Preferences(unittest.TestCase):
    def test_v2_migration(self):
        migrated = preferences.migrate({"my_ski_sizes": [166, 172], "family_ski_sizes": [154, 160], "max_prices": {"ski": 500, "clothing": 100},
                                        "clothing_sizes": ["s", "m"], "watch_terms": ["stio"]})
        self.assertEqual(migrated["profiles"][0]["ski"]["lengths"]["ideal"], [166, 172])
        self.assertEqual(migrated["profiles"][1]["id"], "family")
        self.assertEqual(migrated["watch_terms"], ["stio"])
        self.assertEqual(preferences.validate(PREFS), [])


if __name__ == "__main__":
    unittest.main()
