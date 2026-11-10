#!/usr/bin/env bash
# 발표 HTML 3판 → PDF 3개 (dev-ppt-maker export-pdf.sh, 장마다 1920×1080 캡처)
# 사용: python3 docs/presentation/build.py _v2 && bash docs/presentation/export_pdfs.sh _v2   (인자 없으면 v1)
set -euo pipefail
cd "$(dirname "$0")"
V="${1:-}"
EXP="$HOME/.claude/skills/dev-ppt-maker/tools/export-pdf.sh"
bash "$EXP" "index$V.html"    "../자동화업무소개_전체$V.pdf"
bash "$EXP" "analysis$V.html" "../자동화업무소개_업무분석_개선설계$V.pdf"
bash "$EXP" "run$V.html"      "../자동화업무소개_실행방법$V.pdf"
