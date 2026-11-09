"""콘텐츠대장 ledger.xlsx — 줄을 추가만 하고, 같은 (콘텐츠ID·채널·버전·사건)은 다시 쓰지 않는다."""
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

from common import now

COLS = ["기록ID", "일시", "콘텐츠ID", "장소", "채널", "버전", "사건", "담당", "사유·메모", "결과 경로", "링크"]
WIDTH = [9, 19, 9, 14, 9, 6, 12, 9, 40, 34, 40]


def _open(path):
    path = Path(path)
    if path.exists():
        wb = load_workbook(path)
        return wb, wb.active
    wb = Workbook()
    ws = wb.active
    ws.title = "콘텐츠대장"
    ws.append(COLS)
    for i, w in enumerate(WIDTH, 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = w
        c = ws.cell(1, i)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="0F6E56")
        c.alignment = Alignment(horizontal="center")
    ws.freeze_panes = "A2"
    return wb, ws


def append(path, content_id, place, channel, version, event, actor, memo="", result="", link=""):
    wb, ws = _open(path)
    key = (content_id, channel, f"v{version}" if version else "", event)
    for row in ws.iter_rows(min_row=2, values_only=True):
        if (row[2], row[4], row[5] or "", row[6]) == key:
            return False  # 중복: 같은 사건은 한 번만 기록
    n = ws.max_row  # 머리글 포함이므로 다음 번호
    ws.append([f"L-{n:04d}", now(), content_id, place, channel, key[2], event, actor, memo, result, link])
    wb.save(path)
    return True


def rows(path):
    if not Path(path).exists():
        return []
    ws = load_workbook(path).active
    return [dict(zip(COLS, r)) for r in ws.iter_rows(min_row=2, values_only=True)]
