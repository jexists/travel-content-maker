#!/usr/bin/env bash
# SVG → PNG (헤드리스 Chrome, 2배 해상도). 사용: bash docs/diagrams/render_png.sh
set -euo pipefail
cd "$(dirname "$0")"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
for f in asis tobe architecture; do
  read -r W H < <(python3 -c "import re,sys;s=open('$f.svg').read();m=re.search(r'width=\"(\d+)\" height=\"(\d+)\"',s);print(m.group(1),m.group(2))")
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
    --window-size="$W,$H" --screenshot="$PWD/$f.png" "file://$PWD/$f.svg" >/dev/null 2>&1
  echo "$f.png ${W}x${H} (x2)"
done
