"""사진 선택: selection.json대로 best_insta / best_tistory에 복사 (중복 허용, EXIF·GPS 제거).

selection.json 형식
{"insta": {"cover": "P012", "body": ["P003", "P020", ...]},
 "tistory": ["P012", "P031", ...],
 "shorts": ["P012", "P003", ...],          # 선택. 없으면 인스타 순서. 복사하지 않고 best_* 파일을 참조
 "origin": {"P012": "editor", "P031": "ai"},  # 선택. 누가 고른 사진인지 (없으면 ai)
 "reasons": {"P012": "표지: 얼음 갯벌이 화면을 채움", ...}}
"""
import shutil

from common import load, open_rgb, work_paths
from contact_sheet import sheets
import usage


def _write(src, dst):
    im = open_rgb(src)
    im.thumbnail((2048, 2048))
    im.save(dst, "JPEG", quality=90)  # exif 인자를 넘기지 않으므로 GPS 등 메타데이터가 빠진다


def copy(work):
    p = work_paths(work)
    pdata = load(p["photos"])
    photos = {r["id"]: r for r in pdata["photos"]}
    curated = pdata.get("curated", False)
    cat = load(p["catalog"], {})
    sel = load(p["selection"])
    if not sel:
        raise SystemExit("selection.json이 없습니다.")
    insta = [sel["insta"]["cover"]] + [x for x in sel["insta"]["body"] if x != sel["insta"]["cover"]]
    tis = sel["tistory"]
    shorts = sel.get("shorts") or insta
    dup = [x for x in (insta, tis, shorts) if len(set(x)) != len(x)]
    if dup:
        raise SystemExit(f"selection.json 오류 — 한 목록 안에 같은 사진이 두 번 있습니다: {dup}")
    off = [x for x in shorts if x not in insta and x not in tis]
    if off:
        raise SystemExit(f"selection.json 오류 — 영상 사진은 인스타·티스토리 선택 안에서 고르세요: {off}")
    unknown = [x for x in insta + tis if x not in photos]
    excluded = [x for x in insta + tis if cat.get(x, {}).get("exclude")]
    if unknown or excluded:
        raise SystemExit(f"selection.json 오류 — 없는 ID: {unknown}, 정리에서 뺀 사진: {excluded}")
    # 이미 고른 사진(20장 이하)은 있는 만큼 쓴다. 단 인스타 카드·티스토리 사진 최소 기준은 지킨다
    i_min, t_min = (min(6, len(photos)), min(5, len(photos))) if curated else (6, 8)
    if not (i_min <= len(insta) <= 10):
        raise SystemExit(f"인스타 사진은 표지 포함 {i_min}~10장이어야 합니다 (현재 {len(insta)}장)")
    if not (t_min <= len(tis) <= 20):
        raise SystemExit(f"티스토리 사진은 {t_min}~20장이어야 합니다 (현재 {len(tis)}장)")

    result = {}
    for key, ids in (("best_insta", insta), ("best_tistory", tis)):
        d = p[key]
        if d.exists():
            shutil.rmtree(d)  # 승인 전 단계라 다시 고르면 새로 만든다 (원본 폴더는 건드리지 않음)
        d.mkdir(parents=True)
        files = []
        for i, pid in enumerate(ids, 1):
            name = f"{i:02d}_{'cover_' if key == 'best_insta' and i == 1 else ''}{pid}.jpg"
            _write(photos[pid]["use"], d / name)
            files.append(name)
        result[key] = files
        label = "인스타 (예쁜 사진)" if key == "best_insta" else "티스토리 (예쁜 + 정보 사진)"
        sheets([(pid, photos[pid]["use"], cat.get(pid, {}).get("cat", "")) for pid in ids],
               p["contact"], f"selected_{key[5:]}", f"선택: {label}")
    result["overlap"] = sorted(set(insta) & set(tis))
    result["shorts"] = shorts
    usage.write(work)
    return result
