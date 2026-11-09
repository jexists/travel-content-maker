"""인스타 카드 JPG (원본 비율 유지, 너비 1080).

- 1장(표지): instpic 앱 첫 장 디자인 — '#지역 #동네'(손글씨·밑줄) + 장소명(몬소리체), 흰 글자 + 그림자.
- 2장부터: 원본 사진만. settings.instagram.text_on_other_images가 true이거나 카드에 force_text가 있을 때만 문구를 얹는다.
"""
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from common import RULES, font, font_file, load, open_rgb, settings, wrap

M = 70
SET = settings()


def _shade(im, top_ratio=0.45, strength=200):
    """아래쪽을 어둡게 해 흰 글씨가 읽히게 한다 (본문 문구를 켰을 때만 사용)."""
    W, H = im.size
    grad = Image.new("L", (1, H))
    start = int(H * (1 - top_ratio))
    for y in range(H):
        grad.putpixel((0, y), 0 if y < start else int(strength * ((y - start) / (H - start)) ** 1.3))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.composite(black, im, grad.resize((W, H)))


def _text(d, xy, text, fnt, fill="white", shadow=4):
    x, y = xy
    d.text((x + shadow, y + shadow), text, font=fnt, fill=(0, 0, 0, 140))
    d.text((x, y), text, font=fnt, fill=fill)


def _underline_metrics(path):
    """폰트 post 표의 밑줄 위치·두께(em 비율). 안드로이드(Skia)도 이 값을 쓴다."""
    b = Path(path).read_bytes()
    n = struct.unpack(">H", b[4:6])[0]
    tables = {}
    for i in range(n):
        tag, _, off, _ = struct.unpack(">4sIII", b[12 + 16 * i:28 + 16 * i])
        tables[tag] = off
    upem = struct.unpack(">H", b[tables[b"head"] + 18:tables[b"head"] + 20])[0]
    pos, th = struct.unpack(">hh", b[tables[b"post"] + 8:tables[b"post"] + 12])
    return -pos / upem, th / upem


def _brand_text(im, text, fnt, x, y_base, shadow, underline=False, px_scale=1.0):
    """instpic(ImageSaver)과 같은 방식: 흰 글자 + 흐린 그림자, y는 글자 기준선.

    px_scale: instpic은 원본 해상도 사진에 그림자 오프셋을 픽셀 고정값(2·3px)으로 그린다.
    여기서는 너비 1080으로 줄인 사진에 그리므로 (1080 / 원본 너비)를 곱해 같은 비율로 맞춘다.
    """
    B = SET["instagram"]["brand"]
    size = fnt.size
    color = tuple(B["color"])
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh)
    dx, dy = (v * px_scale for v in shadow["offset"])
    upos, uth = _underline_metrics(fnt.path)
    ul_off, ul_th = round(size * upos), max(1, round(size * uth))
    tw = ds.textlength(text, font=fnt)
    a = shadow["alpha"]
    ds.text((x + dx, y_base + dy), text, font=fnt, fill=(0, 0, 0, a), anchor="ls")
    if underline:
        ds.rectangle([x + dx, y_base + ul_off + dy, x + tw + dx, y_base + ul_off + ul_th + dy], fill=(0, 0, 0, a))
    # 안드로이드 setShadowLayer(radius) → Skia convertRadiusToSigma: sigma = 0.57735·r + 0.5
    sh = sh.filter(ImageFilter.GaussianBlur(0.57735 * size * shadow["radius"] + 0.5))
    im = Image.alpha_composite(im, sh)
    d = ImageDraw.Draw(im)
    d.text((x, y_base), text, font=fnt, fill=color + (255,), anchor="ls")
    if underline:
        d.rectangle([x, y_base + ul_off, x + tw, y_base + ul_off + ul_th], fill=color + (255,))
    return im


def _cover(im, region, title, sponsored, label, px_scale=1.0):
    """instpic 첫 장 디자인: 위 '#지역 #동네'(밑줄, 손글씨) + 아래 장소명. 그라데이션 없음, 한 줄."""
    B = SET["instagram"]["brand"]
    w, h = im.size
    im = im.convert("RGBA")
    f_head = font_file(B["header_font"], round(h * B["header_size"]))
    f_foot = font_file(B["footer_font"], round(h * B["footer_size"]))
    x = round(w * B["margin_left"])
    header = " ".join("#" + r for r in region)
    if header:
        y = h - h * B["header_bottom"] - f_head.getmetrics()[1]
        im = _brand_text(im, header, f_head, x, y, B["header_shadow"], underline=B.get("header_underline", True), px_scale=px_scale)
    if title:
        y = h - h * B["footer_bottom"] - f_foot.getmetrics()[1]
        im = _brand_text(im, title, f_foot, x, y, B["footer_shadow"], px_scale=px_scale)
    if sponsored:
        d = ImageDraw.Draw(im)
        m = round(w * B["margin_left"])
        d.rounded_rectangle([m, m, m + 150, m + 66], 14, fill=(226, 75, 74, 235))
        d.text((m + 28, m + 9), label, font=font(40), fill="white")
    return im.convert("RGB")


def _body(im, text):
    """선택 기능: 본문 카드에 짧은 문구 (기본은 쓰지 않음)."""
    W, H = im.size
    im = _shade(im, 0.42, 200)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(56)
    lines = wrap(d, text, f, W - 2 * M)[:3]
    y = H - M - len(lines) * 76
    for i, line in enumerate(lines):
        _text(d, (M, y + i * 76), line, f)
    return Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")


def _fit_width(im, width):
    """자르지 않고 너비만 맞춘다 (원본 비율 유지)."""
    if im.width == width:
        return im
    return im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)


def render(content, best_dir, out_dir, cfg=None, orig_widths=None):
    """orig_widths: {파일명: 원본 사진 너비} — 그림자 오프셋을 instpic과 같은 비율로 맞추는 데 쓴다."""
    global SET
    if cfg:
        SET = cfg
    label = load(RULES)["common"]["sponsor_label"]
    ig = content["instagram"]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("card_*.jpg"):
        old.unlink()
    files = []
    S = SET["instagram"]
    for i, card in enumerate(ig["cards"], 1):
        src = Path(best_dir) / card["photo"]
        if not src.exists():
            raise SystemExit(f"카드 {i}의 사진이 best_insta에 없습니다: {card['photo']}")
        im = _fit_width(open_rgb(src), S.get("width", 1080))
        if i == 1:
            ow = (orig_widths or {}).get(card["photo"])
            im = _cover(im, content["region"], ig.get("cover_title") or content["place"], content.get("sponsored"), label,
                        px_scale=im.width / ow if ow else 1.0)
        elif card.get("text") and (S.get("text_on_other_images") or card.get("force_text")):
            im = _body(im, card["text"])
        out = out_dir / f"card_{i:02d}.jpg"
        im.save(out, "JPEG", quality=92)
        files.append(out.name)
    tags = " ".join(ig["hashtags"])
    (out_dir / "caption.txt").write_text(ig["caption"].rstrip() + "\n\n" + tags + "\n", encoding="utf-8")
    return files
