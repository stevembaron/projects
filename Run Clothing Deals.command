#!/bin/zsh
# Double-click to refresh every store and open the dashboard on this Mac.
# Nothing is pushed to GitHub; the site keeps updating on its own schedule.
set -e
cd "$(dirname "$0")"
python3 scripts/gear_run.py
echo
echo "Opening the dashboard..."
open "ski-deals/index.html?category=clothing"
echo
echo "Done. Press any key to close this window."
read -k 1
