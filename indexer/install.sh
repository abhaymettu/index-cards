#!/bin/sh
# Install the index-card indexer as a per-minute cron poll. Idempotent.
# Usage: install.sh [CONFIG]  (instance config JSON; default ~/.config/index-cards/config.json)
# Kill: crontab -l | grep -v 'index-cards/indexer/indexer.py' | crontab -
set -e
here=$(cd "$(dirname "$0")" && pwd)
config=${1:-$HOME/.config/index-cards/config.json}
line="* * * * * INDEX_CONFIG=$config /usr/bin/python3 $here/indexer.py --if-changed >> $HOME/.cache/index-cards/index-cards.log 2>> $HOME/.cache/index-cards/index-cards.err"
mkdir -p "$HOME/.cache/index-cards"
crontab -l > "$HOME/.cache/index-cards/crontab.bak-index-cards" 2>/dev/null || true
if grep -qF "$here/indexer.py" "$HOME/.cache/index-cards/crontab.bak-index-cards"; then
  echo "already installed"
else
  { cat "$HOME/.cache/index-cards/crontab.bak-index-cards"; echo "$line"; } | crontab -
  echo "installed"
fi
crontab -l | grep -F "$here/indexer.py"
