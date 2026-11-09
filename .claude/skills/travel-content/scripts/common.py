"""공통 경로·JSON·폰트·이미지 유틸."""
import json
import subprocess
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageFont, ImageOps

SKILL_DIR = Path(__file__).resolve().parent.parent
FONT_BOLD = SKILL_DIR / "assets/fonts/Pretendard-Bold.ttf"
FONT_REG = SKILL_DIR / "assets/fonts/Pretendard-Regular.ttf"
RULES = SKILL_DIR / "references/rules.json"
SETTINGS = SKILL_DIR / "references/settings.json"
FONT_DIR = SKILL_DIR / "assets/fonts"
CHANNELS = ["instagram", "youtube", "tistory"]
CHANNEL_KO = {"instagram": "인스타", "youtube": "유튜브", "tistory": "티스토리", "plan": "기획안", "photos": "사진"}
IMG_EXT = {".jpg", ".jpeg", ".png", ".heic", ".heif"}


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load(path, default=None):
    p = Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def save(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


def font(size, bold=True):
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REG), size)


def font_file(name, size):
    """assets/fonts 안의 폰트 파일 이름으로 연다 (브랜드 폰트용)."""
    return ImageFont.truetype(str(FONT_DIR / name), size)


def settings(work=None):
    """references/settings.json 기본값 + 작업폴더 settings.json(있으면) 덮어쓰기."""
    base = load(SETTINGS, {})
    if work:
        over = load(Path(work) / "settings.json", {})
        for k, v in over.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                base[k] = {**base[k], **v}
            else:
                base[k] = v
    return base


def open_rgb(path):
    """EXIF 회전을 적용해 RGB로 연다. HEIC는 scan 단계에서 만든 JPG 캐시를 쓴다."""
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    return im.convert("RGB")


def heic_to_jpg(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        subprocess.run(["sips", "-s", "format", "jpeg", str(src), "--out", str(dst)],
                       check=True, capture_output=True)
    return dst


def cover_crop(im, w, h):
    """비율을 유지한 채 (w, h)를 꽉 채우도록 가운데를 자른다."""
    return ImageOps.fit(im, (w, h), method=Image.LANCZOS, centering=(0.5, 0.5))


def wrap(draw, text, fnt, max_w):
    """한국어는 글자 단위, 공백이 있으면 단어 단위로 줄바꿈."""
    lines = []
    for para in text.split("\n"):
        cur = ""
        tokens = para.split(" ")
        for i, tok in enumerate(tokens):
            cand = (cur + " " + tok).strip() if cur else tok
            if draw.textlength(cand, font=fnt) <= max_w:
                cur = cand
                continue
            if cur:
                lines.append(cur)
            cur = ""
            for ch in tok:
                if draw.textlength(cur + ch, font=fnt) <= max_w:
                    cur += ch
                else:
                    lines.append(cur)
                    cur = ch
        lines.append(cur)
    return [l for l in lines if l != ""] or [""]


def work_paths(work):
    w = Path(work)
    return {
        "work": w,
        "state": w / "state.json",
        "photos": w / "photos.json",
        "catalog": w / "catalog.json",
        "selection": w / "selection.json",
        "content": w / "content.json",
        "contact": w / "contact",
        "cache": w / "_cache",
        "best_insta": w / "best_insta",
        "best_tistory": w / "best_tistory",
        "usage": w / "usage.json",
        "outputs": w / "OUTPUTS.md",
        "ledger": w.parent / "ledger.xlsx",
    }
