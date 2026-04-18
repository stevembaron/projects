#!/bin/zsh
set -e

cd "$(dirname "$0")"

python3 scripts/deal_monitor.py

echo
echo "Opening data/deals.html..."
open data/deals.html

echo
echo "Done. Press any key to close this window."
read -k 1
