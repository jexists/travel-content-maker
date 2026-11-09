"""사진 폴더를 읽어 흔들림·노출·연속 중복을 거르고 후보를 남긴다 (원본은 읽기만 한다)."""
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat

from common import IMG_EXT, heic_to_jpg, open_rgb, save, work_paths

CURATED_MAX = 20  # 이 장수 이하면 이미 고른 사진으로 본다

LAPLACE = ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1, offset=128)


def taken_at(path):
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            v = exif.get_ifd(0x8769).get(36867) or exif.get(306)
        return str(v) if v else ""
    except Exception:
        return ""


def dhash(gray):
    small = gray.resize((9, 8), Image.LANCZOS)
    px = list(small.getdata())
    bits = 0
    for r in range(8):
        for c in range(8):
            bits = (bits << 1) | (1 if px[r * 9 + c] > px[r * 9 + c + 1] else 0)
    return bits


def metrics(im):
    g = im.convert("L")
    g.thumbnail((512, 512))
    sharp = ImageStat.Stat(g.filter(LAPLACE)).var[0]
    st = ImageStat.Stat(g)
    return sharp, st.mean[0], st.stddev[0], dhash(g)


def scan(src, work, keep=40, dup_dist=10):
    p = work_paths(work)
    files = sorted(f for f in Path(src).rglob("*")
                   if f.is_file() and f.suffix.lower() in IMG_EXT and not f.name.startswith("."))
    if not files:
        raise SystemExit(f"사진이 없습니다: {src}")
    rows = []
    for f in files:
        use = f
        if f.suffix.lower() in (".heic", ".heif"):
            use = heic_to_jpg(f, p["cache"] / (f.stem + ".jpg"))
        try:
            im = open_rgb(use)
        except Exception as e:
            rows.append(dict(src=str(f), use=str(use), status="reject", reason=f"열 수 없음: {e}"))
            continue
        sharp, bright, contrast, h = metrics(im)
        rows.append(dict(src=str(f), use=str(use), w=im.width, h=im.height, taken=taken_at(use),
                         sharp=round(sharp, 1), bright=round(bright, 1), contrast=round(contrast, 1),
                         hash=f"{h:016x}", status="keep", reason="",
                         screenshot=f.suffix.lower() == ".png" and not taken_at(use)))
    rows.sort(key=lambda r: (r.get("taken") or "~", r["src"]))
    for i, r in enumerate(rows, 1):
        r["id"] = f"P{i:03d}"

    if len(rows) <= CURATED_MAX:
        # 20장 이하면 에디터가 이미 고른 사진으로 보고 시스템 필터를 건너뛴다
        data = {"src": str(Path(src).resolve()), "total": len(rows), "curated": True,
                "kept": sum(r["status"] == "keep" for r in rows), "photos": rows}
        save(p["photos"], data)
        return data

    ok = [r for r in rows if r["status"] == "keep"]
    sharps = sorted(r["sharp"] for r in ok) or [0]
    med = sharps[len(sharps) // 2]
    for r in ok:
        if r["screenshot"]:
            r.update(status="reject", reason="스크린샷으로 보임")
        elif r["bright"] < 35:
            r.update(status="reject", reason="너무 어두움")
        elif r["bright"] > 235:
            r.update(status="reject", reason="너무 밝음")
        elif r["sharp"] < med * 0.35:
            r.update(status="reject", reason="흔들림·초점 나감")

    # 연속 촬영 중복: 시간순으로 이웃한 사진끼리 해시가 가까우면 한 묶음, 가장 선명한 것만 남김
    groups, cur = [], []
    for r in [r for r in rows if r["status"] == "keep"]:
        if cur and bin(int(cur[-1]["hash"], 16) ^ int(r["hash"], 16)).count("1") <= dup_dist:
            cur.append(r)
        else:
            if cur:
                groups.append(cur)
            cur = [r]
    if cur:
        groups.append(cur)
    for g in groups:
        best = max(g, key=lambda r: r["sharp"] * (1 + r["contrast"] / 100))
        for r in g:
            if r is not best:
                r.update(status="reject", reason=f"{best['id']}와 거의 같은 사진")

    cands = [r for r in rows if r["status"] == "keep"]
    cands.sort(key=lambda r: r["sharp"] * (1 + r["contrast"] / 100), reverse=True)
    for r in cands[keep:]:
        r.update(status="reject", reason=f"후보 {keep}장 초과 (점수 낮음)")

    data = {"src": str(Path(src).resolve()), "total": len(rows), "curated": False,
            "kept": sum(r["status"] == "keep" for r in rows), "photos": rows}
    save(p["photos"], data)
    return data
