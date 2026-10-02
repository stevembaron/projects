"""Record operational outcomes separately from product observations."""
import argparse
import json
from datetime import datetime,timezone
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--ski',required=True);p.add_argument('--clothing',required=True);p.add_argument('--brief',required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[1]
(root/'data/run_status.json').write_text(json.dumps({'recorded_at':datetime.now(timezone.utc).isoformat(),'ski':a.ski,'clothing':a.clothing,'brief':a.brief},indent=2)+'\n')
