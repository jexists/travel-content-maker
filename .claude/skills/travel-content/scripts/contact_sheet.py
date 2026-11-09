"""번호 붙은 썸네일 모음. AI가 보고 분류·선택하고, 사람이 확인한다."""
from pathlib import Path

from PIL import Image, ImageDraw

from common import font, open_rgb

COLS, ROWS, CELL, PAD, LABEL = 5, 4, 300, 10, 34


def sheets(items, out_dir, name, title=""):
    """items: [(id, path, sub_label)] → out_dir/name_01.jpg …"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob(f"{name}_*.jpg"):
        old.unlink()
    per = COLS * ROWS
    outs = []
    f_id, f_sub, f_title = font(22), font(16, bold=False), font(26)
    for page in range(0, max(len(items), 1), per):
        chunk = items[page:page + per]
        rows = max(1, -(-len(chunk) // COLS))
        top = 50 if title else PAD
        W = COLS * (CELL + PAD) + PAD
        H = top + rows * (CELL + LABEL + PAD) + PAD
        sheet = Image.new("RGB", (W, H), (250, 249, 245))
        d = ImageDraw.Draw(sheet)
        if title:
            d.text((PAD + 4, 12), f"{title}  ({page // per + 1}/{-(-len(items) // per)})", font=f_title, fill=(44, 44, 42))
        for i, (pid, path, sub) in enumerate(chunk):
            x = PAD + (i % COLS) * (CELL + PAD)
            y = top + (i // COLS) * (CELL + LABEL + PAD)
            try:
                im = open_rgb(path)
                im.thumbnail((CELL, CELL))
                sheet.paste(im, (x + (CELL - im.width) // 2, y + (CELL - im.height) // 2))
            except Exception:
                d.rectangle([x, y, x + CELL, y + CELL], outline=(200, 0, 0))
            d.rectangle([x, y, x + 74, y + 30], fill=(226, 75, 74))
            d.text((x + 7, y + 3), pid, font=f_id, fill="white")
            if sub:
                d.text((x + 2, y + CELL + 6), sub[:22], font=f_sub, fill=(68, 68, 65))
        out = out_dir / f"{name}_{page // per + 1:02d}.jpg"
        sheet.save(out, quality=85)
        outs.append(out)
    return outs
