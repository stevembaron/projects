import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from chatgpt_brief import apply_pending
from deal_brief import snapshot_id

class ChatGPTBriefTests(unittest.TestCase):
    def test_publish_and_duplicate_do_not_repeat_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'data').mkdir()
            dataset = {'generated_at':'2026-10-03T10:30:00+00:00', 'preferences':{}, 'deals':[], 'errors':[]}
            (root/'data/tracker.json').write_text(json.dumps(dataset))
            (root/'data/chatgpt_decisions.json').write_text(json.dumps({'snapshot_id':snapshot_id(dataset),'act_now':[],'watch':[]}))
            self.assertEqual(apply_pending(root), 'published')
            self.assertEqual(json.loads((root/'data/deal_brief.json').read_text())['provider'], 'chatgpt_scheduled_task')
            self.assertIn('ChatGPT scheduled task', (root/'deal-brief/index.html').read_text())
            self.assertEqual(apply_pending(root), 'already_published')
            self.assertEqual(len(list((root/'data/briefs').glob('*.json'))), 1)

    def test_stale_decisions_preserve_last_brief(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'data').mkdir()
            (root/'data/tracker.json').write_text(json.dumps({'generated_at':'new','preferences':{},'deals':[]}))
            (root/'data/deal_brief.json').write_text('{"snapshot_id":"last-good"}')
            (root/'data/chatgpt_decisions.json').write_text('{"snapshot_id":"stale","act_now":[],"watch":[]}')
            self.assertEqual(apply_pending(root), 'rejected')
            self.assertEqual((root/'data/deal_brief.json').read_text(), '{"snapshot_id":"last-good"}')
