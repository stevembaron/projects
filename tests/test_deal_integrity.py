"""Regression tests for household eligibility, stale data and offer identity."""
import copy
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import deal_monitor as monitor
from deal_rules import enrich, comparisons, offer_key
from deal_history import update, cached_deals
from deal_dataset import build_dataset
from deal_brief import snapshot_id, validate_decisions
from build_public import build

NOW = datetime(2026,10,2,12,tzinfo=timezone.utc)
PREFS = {'my_ski_sizes':list(range(166,173)), 'family_ski_sizes':list(range(154,161)), 'clothing_sizes':['s','m'],
    'max_prices':{'ski':500,'clothing':100}, 'watch_terms':[], 'muted_terms':[], 'owned_terms':[]}

def offer(**overrides):
    d={'title':'Atomic Bent 90 Skis 2026','source':'Evo','url':'https://evo.com/bent-90', 'category':'ski',
       'current_price':300,'sizes':['168 cm'],'stock_status':'in_stock','condition':'new','price_scope':'exact',
       'last_verified_at':'2026-10-02T11:00:00+00:00','observation_count':4,'lowest_price':300,'highest_price':400,
       'price_change':-100,'price_change_percent':-25}
    d.update(overrides);return d

class Eligibility(unittest.TestCase):
    def test_verified_match(self):
        d=offer();enrich([d],PREFS,NOW);self.assertTrue(d['act_now_eligible'])
    def test_clothing_wrong_size(self):
        d=offer(category='clothing',current_price=50,sizes=['XL'],discount_percent=70)
        enrich([d],PREFS,NOW);self.assertFalse(d['act_now_eligible']);self.assertFalse(monitor.is_sweet_spot(d))
    def test_unsafe_recommendation_inputs(self):
        for changes in [{'stock_status':None},{'is_cached':True},{'price_scope':'from'},{'current_price':501},{'last_verified_at':'2026-09-29T00:00:00Z'},{'sizes':[]}]:
            with self.subTest(changes=changes):
                d=offer(**changes);enrich([d],PREFS,NOW);self.assertFalse(d['act_now_eligible'])
    def test_configured_caps_not_hardcoded(self):
        p=copy.deepcopy(PREFS);p['max_prices']['ski']=200;d=offer();enrich([d],p,NOW);self.assertFalse(d['matches_price'])
    def test_owned_and_muted(self):
        for key in ['owned_terms','muted_terms']:
            p=copy.deepcopy(PREFS);p[key]=['bent'];d=offer();enrich([d],p,NOW);self.assertFalse(d['act_now_eligible'])
    def test_new_lengths(self):
        for size in [167,169]:
            d=offer(sizes=[str(size)]);enrich([d],PREFS,NOW);self.assertTrue(d['matches_my_size'])
    def test_small_drop_not_meaningful(self):
        d=offer(price_change=-5,price_change_percent=-1,lowest_price=250);enrich([d],PREFS,NOW);self.assertFalse(d['meaningful_drop']);self.assertFalse(d['act_now_eligible'])

class Identity(unittest.TestCase):
    def test_width_year_condition_size_stock_and_scope_are_not_equivalent(self):
        a=offer()
        for changes in [{'title':'Atomic Bent 100 Skis 2026'},{'title':'Atomic Bent 90 Skis 2025'},{'condition':'demo'},{'sizes':['172 cm']},{'stock_status':None},{'price_scope':'from'},{'condition':None}]:
            b=offer(source='Other',url='https://other.test/item',**changes)
            with self.subTest(changes=changes):self.assertEqual(comparisons([a,b]),{})
    def test_equal_offers_compared(self):
        a=offer();b=offer(source='Other',url='https://other.test/item',current_price=350)
        self.assertTrue(comparisons([a,b])[id(a)]['best'])
    def test_two_stores_not_deduped(self):
        args=('Atomic Bent 90','https://test/item')
        a=monitor.make_deal(*args,'A',300,400,'2026-10-02');b=monitor.make_deal(*args,'B',300,400,'2026-10-02')
        self.assertEqual(len(monitor.dedupe([a,b])),2)
    def test_variants_keep_exact_price(self):
        payload={'products':[{'title':'Test ski','handle':'test','variants':[{'id':1,'title':'168 cm','price':'300','available':True},{'id':2,'title':'172 cm','price':'400','available':True}]}]}
        ds=monitor.shopify_products_json_candidates(json.dumps(payload),'https://shop.test','Shop','2026-10-02')
        ds=monitor.consolidate_size_variants(ds)
        self.assertEqual([(d.sizes,d.current_price) for d in ds],[(['168cm'],300),(['172cm'],400)])
        self.assertTrue(all(d.price_scope=='exact' and d.stock_status=='in_stock' for d in ds))
        self.assertNotEqual(offer_key(ds[0]),offer_key(ds[1]))

class History(unittest.TestCase):
    def test_cache_does_not_create_observation_or_refresh_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.json';d=monitor.make_deal('Ski','https://shop.test/ski','Shop',100,200,'2026-10-01T10:00:00Z',sizes=['168'],price_scope='exact')
            update([d],path,'2026-10-01T10:00:00Z');before=path.read_text();cached=cached_deals(json.loads(before),'Shop','2026-10-02T10:00:00Z',10)
            self.assertEqual(len(cached),1);h=update(cached,path,'2026-10-02T10:00:00Z');item=h['items'][offer_key(d)]
            self.assertEqual(len(item['observations']),1);self.assertEqual(item['last_verified_at'],'2026-10-01T10:00:00Z')
            self.assertEqual(cached_deals(h,'Shop','2026-10-06T10:00:00Z',10),[])
    def test_legacy_cache_never_invented(self):
        h={'items':{'old':{'source':'Shop','current_price':100,'last_seen_at':'2026-10-02T10:00:00Z'}}}
        self.assertEqual(cached_deals(h,'Shop','2026-10-02T11:00:00Z',10),[])
    def test_calendar_cutoff_and_intraday(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.json';d=monitor.make_deal('Ski','https://shop.test/ski','Shop',400,500,'2026-01-01T10:00:00Z')
            update([d],path,'2026-01-01T10:00:00Z');d.current_price=300
            update([d],path,'2026-10-02T10:00:00Z');d.current_price=250
            h=update([d],path,'2026-10-02T12:00:00Z');obs=h['items'][offer_key(d)]['observations']
            self.assertEqual(len(obs),2);self.assertEqual(d.highest_price,300);self.assertEqual(d.price_change,-50)

class Brief(unittest.TestCase):
    def dataset(self):
        return build_dataset({'generated_at':'2026-10-02T11:00:00Z','deals':[offer()],'errors':[]},None,PREFS,now=NOW)
    def test_valid_decisions(self):
        ds=self.dataset();result={'snapshot_id':snapshot_id(ds),'act_now':[{'id':ds['deals'][0]['id'],'reason':'Verified drop at your length.'}],'watch':[]}
        self.assertEqual(len(validate_decisions(result,ds,NOW)['decisions']),1)
    def test_invalid_decisions_rejected(self):
        ds=self.dataset();base={'snapshot_id':snapshot_id(ds),'act_now':[],'watch':[]}
        for bad in [dict(base,snapshot_id='old'),dict(base,act_now=[{'id':'fake','reason':'Good.'}]),dict(base,watch=[{'id':ds['deals'][0]['id'],'reason':'Buy for $10'}])]:
            with self.assertRaises(ValueError):validate_decisions(bad,ds,NOW)
    def test_pref_change_changes_snapshot(self):
        ds=self.dataset();identity=snapshot_id(ds);ds['preferences']=dict(ds['preferences'],my_ski_sizes=[172]);self.assertNotEqual(identity,snapshot_id(ds))
    def test_cache_filtered_and_missing_shared(self):
        bad=offer(is_cached=True,last_verified_at=None);ds=build_dataset({'generated_at':'2026-10-02','deals':[bad],'errors':[]},None,PREFS,now=NOW)
        self.assertEqual(ds['deals'],[])
    def test_disappeared_not_from_failed_sources(self):
        h={'items':{'v2|gone':{'source':'Store','last_verified_at':'2026-10-01T10:00:00Z','title':'Missing','current_price':100,'url':'https://store.test'}}}
        p={'generated_at':'2026-10-02','deals':[],'errors':[{'source':'Store','error':'403'}]}
        self.assertEqual(build_dataset(p,None,PREFS,h,NOW)['disappeared_deals'],[])
        p['errors']=[];self.assertEqual(len(build_dataset(p,None,PREFS,h,NOW)['disappeared_deals']),1)

class PublicFiles(unittest.TestCase):
    def test_stage_only_public_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for p in ['other/index.html','other/app.js','other/data.json','other/secret.py','config/preferences.json','data/private.json','assets/deals.js']:
                f=root/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('test')
            target=build(root)
            self.assertTrue((target/'other/data.json').exists());self.assertFalse((target/'other/secret.py').exists());self.assertFalse((target/'data').exists());self.assertTrue((target/'assets/deals.js').exists())

if __name__=='__main__':unittest.main()
