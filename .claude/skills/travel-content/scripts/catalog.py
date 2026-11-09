"""사진 정리: AI가 쓴 catalog.json을 검증하고 분류별 요약·썸네일을 만든다.

catalog.json 형식
{"P003": {"cat": "풍경", "exclude": false, "reason": "", "note": "얼음 갯벌 전경"}, ...}
"""
from collections import Counter

from common import load, save, work_paths
from contact_sheet import sheets

CATS = ["풍경", "음식", "메뉴판", "간판/입구", "실내", "인물", "길/주차", "기타"]
INFO_CATS = {"메뉴판", "간판/입구", "길/주차", "실내"}


def build(work):
    p = work_paths(work)
    photos = {r["id"]: r for r in load(p["photos"])["photos"]}
    cat = load(p["catalog"])
    if not cat:
        raise SystemExit("catalog.json이 없습니다. 먼저 후보 썸네일을 보고 분류를 작성하세요.")
    errs = [k for k in cat if k not in photos]
    bad = [k for k, v in cat.items() if v.get("cat") not in CATS]
    if errs or bad:
        raise SystemExit(f"catalog.json 오류 — 없는 ID: {errs}, 분류 이름 오류: {bad} (허용: {CATS})")

    kept = [k for k, v in cat.items() if not v.get("exclude")]
    cnt = Counter(cat[k]["cat"] for k in kept)
    lines = ["# 사진 정리 결과", "",
             f"- 전체 {len(photos)}장 → 시스템 1차 후보 {sum(r['status']=='keep' for r in photos.values())}장 → AI 정리 후 **{len(kept)}장**", "",
             "| 분류 | 장수 | 사진 |", "| --- | --- | --- |"]
    for c in CATS:
        ids = [k for k in kept if cat[k]["cat"] == c]
        lines.append(f"| {c} | {len(ids)} | {', '.join(ids) or '—'} |")
    lacking = [c for c in INFO_CATS if cnt[c] == 0]
    if lacking:
        lines += ["", f"> 티스토리 정보 사진이 없는 분류: **{', '.join(sorted(lacking))}** — 원본 폴더에 있으면 번호를 알려 주세요."]
    ex = [k for k, v in cat.items() if v.get("exclude")]
    lines += ["", "## AI가 뺀 사진", "", "| 사진 | 사유 |", "| --- | --- |"]
    lines += [f"| {k} | {cat[k].get('reason','')} |" for k in ex] or ["| — | — |"]
    sys_ex = [r for r in photos.values() if r["status"] == "reject"]
    lines += ["", f"## 시스템이 뺀 사진 ({len(sys_ex)}장)", "", "| 사유 | 장수 |", "| --- | --- |"]
    for reason, n in Counter(r["reason"].split(" (")[0] if "초과" in r["reason"] else
                             ("거의 같은 사진" if "같은 사진" in r["reason"] else r["reason"])
                             for r in sys_ex).most_common():
        lines.append(f"| {reason} | {n} |")
    (p["work"] / "catalog.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    outs = []
    for c in CATS:
        ids = [k for k in kept if cat[k]["cat"] == c]
        if ids:
            safe = c.replace("/", "_")
            outs += sheets([(k, photos[k]["use"], cat[k].get("note", "")) for k in ids],
                           p["contact"], f"cat_{safe}", f"분류: {c}")
    return {"kept": len(kept), "counts": dict(cnt), "lacking": lacking, "sheets": [str(o) for o in outs]}
