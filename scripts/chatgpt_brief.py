"""Exchange brief data with a ChatGPT scheduled task. No model API calls."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from deal_analyst import build_user_prompt, SYSTEM_PROMPT
from deal_brief import publish, snapshot_id

ROOT = Path(__file__).resolve().parents[1]


def export_input(root=ROOT):
    prompt, _ = build_user_prompt(60)
    payload = json.loads(prompt)
    fields = ('id', 'title', 'category', 'source', 'url', 'current_price', 'sizes',
              'condition', 'price_scope', 'stock_status', 'last_verified_at',
              'is_cached', 'is_fresh', 'act_now_eligible', 'meaningful_drop',
              'price_change', 'price_change_percent', 'observation_count',
              'lowest_price', 'highest_price', 'history_start', 'is_watchlist', 'comparison')
    payload['deals'] = [{k: d.get(k) for k in fields} for d in payload['deals']]
    payload['instructions'] = SYSTEM_PROMPT
    payload['exported_at'] = datetime.now(timezone.utc).isoformat()
    (root/'data/chatgpt_brief_input.json').write_text(json.dumps(payload, indent=2)+'\n')


def apply_pending(root=ROOT):
    path = root/'data/chatgpt_decisions.json'
    if not path.exists():
        return 'waiting_for_chatgpt'
    dataset = json.loads((root/'data/tracker.json').read_text())
    result = json.loads(path.read_text())
    previous = root/'data/deal_brief.json'
    if previous.exists():
        prior = json.loads(previous.read_text())
        if prior.get('snapshot_id') == result.get('snapshot_id') == snapshot_id(dataset) and prior.get('provider') == 'chatgpt_scheduled_task':
            return 'already_published'
    try:
        brief = publish(result, dataset, root)
    except (ValueError, TypeError, KeyError) as error:
        status = {'status': 'rejected', 'snapshot_id': result.get('snapshot_id'), 'error': str(error)}
    else:
        status = {'status': 'published', 'snapshot_id': brief['snapshot_id'], 'generated_at': brief['generated_at']}
    (root/'data/chatgpt_brief_status.json').write_text(json.dumps(status, indent=2)+'\n')
    print(json.dumps(status))
    return status['status']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', action='store_true')
    args = parser.parse_args()
    if args.export:
        export_input()
    else:
        apply_pending()
