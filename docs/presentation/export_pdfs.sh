#!/usr/bin/env bash
# 발표 HTML 3판 → PDF 3개 (dev-ppt-maker export-pdf.sh, 장마다 1920×1080 캡처)
# 사용: python3 docs/presentation/build.py && bash docs/presentation/export_pdfs.sh
set -euo pipefail
cd "$(dirname "$0")"
EXP="$HOME/.claude/skills/dev-ppt-maker/tools/export-pdf.sh"
bash "$EXP" index.html    "../자동화업무소개_전체.pdf"
bash "$EXP" analysis.html "../자동화업무소개_업무분석_개선설계.pdf"
bash "$EXP" run.html      "../자동화업무소개_실행방법.pdf"
