"""실제 캡처(공개 웹페이지, 2026-11-10 헤드리스 Chrome)에 누를 곳 번호를 표시한다.
python3 docs/presentation/illust/mark_captures.py → mark_claude_download.png · mark_python_dl.png
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ORANGE = (216, 90, 48)
FONT = str(Path.home() / "Library/Fonts/Pretendard-Bold.otf")


def mark(src, out, crop, box, n, note):
    im = Image.open(HERE / src).convert("RGB").crop(crop)
    ox, oy = crop[:2]
    x0, y0, x1, y1 = box[0] - ox, box[1] - oy, box[2] - ox, box[3] - oy
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((x0 - 10, y0 - 10, x1 + 10, y1 + 10), radius=(y1 - y0) // 2 + 10, outline=ORANGE, width=6)
    cx, cy, r = x1 + 50, (y0 + y1) // 2, 24
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ORANGE)
    f = ImageFont.truetype(FONT, 30)
    d.text((cx, cy), str(n), font=f, fill="white", anchor="mm")
    d.text((cx + 38, cy), note, font=ImageFont.truetype(FONT, 28), fill=ORANGE, anchor="lm",
           stroke_width=4, stroke_fill="white")
    im.save(HERE / out)
    print(out, im.size)


mark("web_claude_download.png", "mark_claude_download.png", (240, 180, 1200, 520), (616, 416, 824, 456), 1, "앱 받기 → 로그인")
mark("web_python_dl.png", "mark_python_dl.png", (180, 225, 1140, 460), (251, 291, 440, 331), 2, "Python 받기 (3.10 이상)")
