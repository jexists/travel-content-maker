#!/usr/bin/env bash
# 설명 그림 SVG → PNG (헤드리스 Chrome, 2배). 사용: bash docs/presentation/illust/render.sh
set -euo pipefail
cd "$(dirname "$0")"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
for f in ${@:-win_python_path put_skill use_claude env_key}; do
  read -r W H < <(python3 -c "import re;s=open('$f.svg').read();m=re.search(r'width=\"(\d+)\" height=\"(\d+)\"',s);print(m.group(1),m.group(2))")
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
    --window-size="$W,$H" --screenshot="$PWD/$f.png" "file://$PWD/$f.svg" >/dev/null 2>&1
  echo "$f.png ${W}x${H} (x2)"
done
