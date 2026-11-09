"""인스타 사진 과정 (사용자가 사진을 고르는 흐름).

1. pick  : 원본이 20장 이하면 전부, 넘으면 AI가 고른 20장을 insta_pick/에 복사 → 폴더 위치를 보여 주고 진행 여부를 묻는다.
2. mine  : 사용자가 싫다고 하면 insta_mine/ 빈 폴더를 만들고 "여기에 넣어 주세요".
3. use   : 확정한 폴더(insta_pick 또는 insta_mine)를 best_insta/로 정리 (번호순, GPS 제거).
4. cover : 표지 미리보기 (사용자가 고른 사진 번호 + 지역·장소명).
5. order : 올라가는 순서 확정 (표지는 항상 1번) → best_insta 파일 이름을 그 순서로 다시 매긴다.
6. tistory_extra : 티스토리 = 인스타 사진 + 원본에서 고른 정보 사진.

insta.json 에 각 사진의 출처를 남긴다.
"""
import shutil
from pathlib import Path

from common import IMG_EXT, heic_to_jpg, load, open_rgb, save, work_paths
from contact_sheet import sheets
from copy_best import _write

MAX = 20


def _imgs(d):
    return sorted(f for f in Path(d).iterdir()
                  if f.is_file() and f.suffix.lower() in IMG_EXT and not f.name.startswith("."))


def _meta(work):
    return work_paths(work)["work"] / "insta.json"


def pick(work, src, ids=None):
    """insta_pick/ 만들기. 반환: {"folder", "count", "total", "sheet", "auto"}"""
    import scan_photos
    p = work_paths(work)
    data = load(p["photos"])
    if not data or Path(data["src"]) != Path(src).resolve():
        data = scan_photos.scan(src, work)
    photos = {r["id"]: r for r in data["photos"]}
    keep = [r["id"] for r in data["photos"] if r["status"] == "keep"]
    if data["total"] <= MAX:
        chosen, auto = [r["id"] for r in data["photos"]], True  # 20장 이하: 고르지 않고 전부
    else:
        if not ids:
            raise SystemExit(f"사진이 {data['total']}장이라 20장을 골라야 합니다. 후보 시트를 보고 --ids 로 20장 이하를 지정하세요.")
        bad = [x for x in ids if x not in photos]
        if bad:
            raise SystemExit(f"없는 사진 ID: {bad}")
        if len(ids) > MAX:
            raise SystemExit(f"{len(ids)}장 — 인스타는 최대 {MAX}장입니다.")
        chosen, auto = ids, False
    d = p["work"] / "insta_pick"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    rows = []
    for i, pid in enumerate(chosen, 1):
        name = f"{i:02d}_{pid}.jpg"
        _write(photos[pid]["use"], d / name)
        rows.append({"file": name, "id": pid, "src": photos[pid]["src"], "w": photos[pid].get("w")})
    sheet = sheets([(f"{i}", d / r["file"], r["id"]) for i, r in enumerate(rows, 1)], p["contact"], "insta_pick",
                   f"인스타 사진 후보 ({'전체' if auto else 'AI가 고른 20장'})")
    meta = load(_meta(work), {})
    meta.update(pick={"auto": auto, "total": data["total"], "candidates": len(keep), "photos": rows})
    save(_meta(work), meta)
    return {"folder": str(d.resolve()), "count": len(rows), "total": data["total"], "auto": auto,
            "sheet": [str(s) for s in sheet]}


def mine(work):
    d = work_paths(work)["work"] / "insta_mine"
    d.mkdir(parents=True, exist_ok=True)
    return {"folder": str(d.resolve()), "count": len(_imgs(d))}


def use(work, folder):
    """확정한 폴더 → best_insta/ (01_…, 02_…). 사용자 폴더 사진도 GPS를 지우고 긴 변 2048로."""
    p = work_paths(work)
    d = p["work"] / folder if not Path(folder).is_absolute() else Path(folder)
    files = _imgs(d) if d.exists() else []
    if not files:
        raise SystemExit(f"{d} 에 사진이 없습니다. 사진을 넣은 뒤 다시 알려 주세요.")
    if len(files) > MAX:
        raise SystemExit(f"{len(files)}장 — 인스타는 최대 {MAX}장입니다. {MAX}장 이하로 줄여 주세요.")
    meta = load(_meta(work), {})
    picked = {r["file"]: r for r in meta.get("pick", {}).get("photos", [])}
    out = p["best_insta"]
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    rows = []
    for i, f in enumerate(files, 1):
        src = f
        if f.suffix.lower() in (".heic", ".heif"):
            src = heic_to_jpg(f, p["cache"] / (f.stem + ".jpg"))
        w = open_rgb(src).width
        pid = picked[f.name]["id"] if f.name in picked else f"U{i:02d}"
        name = f"{i:02d}_{pid}.jpg"
        _write(src, out / name)
        rows.append({"n": i, "file": name, "id": pid, "from": str(f.resolve()),
                     "w": picked.get(f.name, {}).get("w") or w})
    sheet = sheets([(f"{r['n']}", out / r["file"], r["id"]) for r in rows], p["contact"], "insta_fixed",
                   f"인스타 사진 확정 ({folder})")
    meta["fixed"] = {"folder": str(d.resolve()), "photos": rows}
    meta.pop("cover", None)
    meta.pop("order", None)
    save(_meta(work), meta)
    return {"folder": str(d.resolve()), "count": len(rows), "best_insta": str(out.resolve()),
            "sheet": [str(s) for s in sheet], "photos": [r["file"] for r in rows]}


def _fixed(work):
    meta = load(_meta(work), {})
    if "fixed" not in meta:
        raise SystemExit("인스타 사진이 확정되지 않았습니다 (insta-use 먼저).")
    return meta


def _content(work, region=None, title=None):
    p = work_paths(work)
    st = load(p["state"])
    c = load(p["content"]) or {"id": st["id"], "place": st["place"], "region": [], "sponsored": False,
                               "seo": {"main": "", "sub": [], "longtail": []}, "info": {},
                               "instagram": {"cards": [], "caption": "", "hashtags": []}}
    if region:
        c["region"] = region
    if title:
        c.setdefault("instagram", {})["cover_title"] = title
    return c


def cover(work, n, region, title):
    """표지 미리보기: n번 사진에 instpic 디자인 (아직 최종 아님)."""
    import render_cards
    from common import settings
    p = work_paths(work)
    meta = _fixed(work)
    rows = meta["fixed"]["photos"]
    if not 1 <= n <= len(rows):
        raise SystemExit(f"사진 번호는 1~{len(rows)} 입니다.")
    r = rows[n - 1]
    render_cards.SET = settings(work)
    im = render_cards._fit_width(open_rgb(p["best_insta"] / r["file"]), render_cards.SET["instagram"].get("width", 1080))
    im = render_cards._cover(im, region, title, False, "", px_scale=im.width / r["w"] if r.get("w") else 1.0)
    out = p["work"] / "instagram" / "cover_preview.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, "JPEG", quality=92)
    meta["cover"] = {"n": n, "file": r["file"], "id": r["id"], "region": region, "title": title}
    save(_meta(work), meta)
    c = _content(work, region, title)
    save(p["content"], c)
    return {"preview": str(out.resolve()), "photo": r["file"], "region": region, "title": title}


def order(work, nums):
    """올라가는 순서 확정. nums: 확정 폴더 기준 번호 목록 (빠진 번호는 올리지 않음). 표지는 맨 앞으로."""
    p = work_paths(work)
    meta = _fixed(work)
    if "cover" not in meta:
        raise SystemExit("표지를 먼저 정하세요 (insta-cover).")
    rows = meta["fixed"]["photos"]
    if len(set(nums)) != len(nums) or any(not 1 <= x <= len(rows) for x in nums):
        raise SystemExit(f"번호는 1~{len(rows)} 사이, 중복 없이 적어 주세요: {nums}")
    cn = meta["cover"]["n"]
    nums = [cn] + [x for x in nums if x != cn]
    tmp = p["work"] / "_order_tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    new = []
    for i, x in enumerate(nums, 1):
        r = rows[x - 1]
        name = f"{i:02d}_{'cover_' if i == 1 else ''}{r['id']}.jpg"
        shutil.copy2(p["best_insta"] / r["file"], tmp / name)
        new.append({**r, "n": i, "file": name, "was": x})
    shutil.rmtree(p["best_insta"])
    tmp.rename(p["best_insta"])
    meta["order"] = {"nums": nums, "photos": new}
    meta["fixed"]["photos"] = [{**r, "n": i} for i, r in enumerate(new, 1)]  # 이후 번호는 새 순서 기준
    meta["cover"].update(n=1, file=new[0]["file"])
    save(_meta(work), meta)
    c = _content(work)
    c["instagram"]["cards"] = [{"photo": r["file"]} for r in new]
    save(p["content"], c)
    sheet = sheets([(f"{i}", p["best_insta"] / r["file"], "표지" if i == 1 else r["id"]) for i, r in enumerate(new, 1)],
                   p["contact"], "insta_order", "인스타 올라가는 순서")
    return {"order": [r["file"] for r in new], "dropped": [x for x in range(1, len(rows) + 1) if x not in nums],
            "sheet": [str(s) for s in sheet]}


def widths(work):
    """render_cards 에 넘길 {파일명: 원본 너비} (그림자 오프셋 비율용)."""
    meta = load(_meta(work), {})
    return {r["file"]: r["w"] for r in meta.get("fixed", {}).get("photos", []) if r.get("w")}


def tistory_extra(work, extra_ids):
    """best_tistory = 인스타 순서 사진 + 원본에서 고른 정보 사진(뒤에 붙임)."""
    p = work_paths(work)
    meta = _fixed(work)
    photos = {r["id"]: r for r in load(p["photos"], {"photos": []})["photos"]}
    bad = [x for x in extra_ids if x not in photos]
    if bad:
        raise SystemExit(f"원본에 없는 사진 ID: {bad}")
    insta_ids = [r["id"] for r in meta["fixed"]["photos"]]
    out = p["best_tistory"]
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    files = []
    for i, f in enumerate(sorted(p["best_insta"].glob("*.jpg")), 1):
        pid = f.stem.split("_")[-1]
        name = f"{i:02d}_{pid}.jpg"
        shutil.copy2(f, out / name)
        files.append(name)
    for pid in [x for x in extra_ids if x not in insta_ids]:
        name = f"{len(files) + 1:02d}_{pid}.jpg"
        _write(photos[pid]["use"], out / name)
        files.append(name)
    meta["tistory"] = {"extra": extra_ids, "photos": files}
    save(_meta(work), meta)
    sheets([(f"{i}", out / n, n.split("_")[-1][:-4]) for i, n in enumerate(files, 1)], p["contact"], "selected_tistory",
           "티스토리 사진 (인스타 + 정보 사진)")
    return {"best_tistory": str(out.resolve()), "photos": files}
