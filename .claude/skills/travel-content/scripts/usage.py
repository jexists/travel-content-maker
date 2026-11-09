"""사진 사용표(usage.json·usage.md)와 결과물 위치(OUTPUTS.md).

사진은 best_insta·best_tistory에만 물리 복사하고, 영상·썸네일은 그 파일을 참조한다.
이 표 하나로 "어떤 사진이 어디에 몇 번째로 쓰이는지"와 "최종 파일이 어디 있는지"를 본다.
"""
from pathlib import Path

from common import CHANNELS, CHANNEL_KO, load, save, work_paths


def _best_name(d, pid):
    hits = sorted(Path(d).glob(f"*_{pid}.jpg")) if Path(d).exists() else []
    return hits[0].name if hits else None


def shorts_ids(sel):
    insta = [sel["insta"]["cover"]] + [x for x in sel["insta"]["body"] if x != sel["insta"]["cover"]]
    return sel.get("shorts") or insta


def shorts_file(work, pid):
    """영상 장면 사진: best_insta 우선, 없으면 best_tistory 파일을 참조한다."""
    p = work_paths(work)
    for key in ("best_insta", "best_tistory"):
        n = _best_name(p[key], pid)
        if n:
            return p[key] / n
    raise SystemExit(f"영상 사진 {pid}가 best_insta·best_tistory에 없습니다. select를 먼저 실행하세요.")


def build_v2(work):
    """사용자가 고른 인스타 폴더 기준 (insta.json). 영상 = 인스타 순서, 티스토리 = 인스타 + 정보 사진."""
    p = work_paths(work)
    meta = load(p["work"] / "insta.json", {})
    if "fixed" not in meta:
        return None
    insta = [f.stem.split("_")[-1] for f in sorted(p["best_insta"].glob("*.jpg"))]
    tis = [f.stem.split("_")[-1] for f in sorted(p["best_tistory"].glob("*.jpg"))] if p["best_tistory"].exists() else []
    src = {r["id"]: r for r in meta["fixed"]["photos"]}
    # 사용자 폴더(insta_mine)이거나 20장 이하라 전부 쓴 경우 = 에디터가 고른 사진, AI가 20장을 고른 경우 = ai
    mine_dir = meta["fixed"]["folder"].endswith("insta_mine")
    insta_origin = "editor" if mine_dir or meta.get("pick", {}).get("auto", True) else "ai"
    photos = {r["id"]: r for r in load(p["photos"], {"photos": []})["photos"]}
    rows = []
    for pid in dict.fromkeys(insta + tis):
        rows.append({"id": pid, "original": src.get(pid, {}).get("from") or photos.get(pid, {}).get("src", ""),
                     "category": "", "selected": True,
                     "origin": insta_origin if pid in insta else "ai",
                     "excluded": False,
                     "blog_order": tis.index(pid) + 1 if pid in tis else None,
                     "insta_order": insta.index(pid) + 1 if pid in insta else None,
                     "insta_cover": bool(insta) and pid == insta[0],
                     "shorts_order": insta.index(pid) + 1 if pid in insta else None,
                     "blog_file": None, "insta_file": None,
                     "reason": "티스토리 정보 사진" if pid not in insta else ""})
    data = {"cover": insta[0] if insta else None, "blog": tis, "instagram": insta, "shorts": insta, "photos": rows}
    save(p["usage"], data)
    return data


def build(work):
    p = work_paths(work)
    if (p["work"] / "insta.json").exists():
        return build_v2(work)
    photos = load(p["photos"], {"photos": []})
    sel = load(p["selection"])
    if not sel:
        return None
    cat = load(p["catalog"], {})
    origin = sel.get("origin", {})
    insta = [sel["insta"]["cover"]] + [x for x in sel["insta"]["body"] if x != sel["insta"]["cover"]]
    tis, shorts = sel["tistory"], shorts_ids(sel)
    rows = []
    for r in photos["photos"]:
        pid = r["id"]
        selected = pid in insta or pid in tis or pid in shorts
        rows.append({
            "id": pid,
            "original": r["src"],
            "category": cat.get(pid, {}).get("cat", ""),
            "selected": selected,
            "origin": origin.get(pid, "ai") if selected else "",
            "excluded": cat.get(pid, {}).get("exclude", False) or r.get("status") == "reject",
            "blog_order": tis.index(pid) + 1 if pid in tis else None,
            "insta_order": insta.index(pid) + 1 if pid in insta else None,
            "insta_cover": pid == insta[0],
            "shorts_order": shorts.index(pid) + 1 if pid in shorts else None,
            "blog_file": f"best_tistory/{_best_name(p['best_tistory'], pid)}" if pid in tis else None,
            "insta_file": f"best_insta/{_best_name(p['best_insta'], pid)}" if pid in insta else None,
            "reason": sel.get("reasons", {}).get(pid, ""),
        })
    data = {"cover": insta[0], "blog": tis, "instagram": insta, "shorts": shorts, "photos": rows}
    save(p["usage"], data)
    return data


def write(work):
    data = build(work)
    if not data:
        return None
    p = work_paths(work)
    sel_rows = [r for r in data["photos"] if r["selected"]]
    o = lambda v: str(v) if v else "—"
    lines = ["# 사진 사용표", "",
             f"- 원본 {len(data['photos'])}장 → 선택 {len(sel_rows)}장 · 블로그 {len(data['blog'])}장 · "
             f"인스타 {len(data['instagram'])}장 · 영상 {len(data['shorts'])}장 · 대표(표지) **{data['cover']}**",
             "- 순서는 확정한 사진 순서 그대로이며, 채널 결과물은 이 순서를 바꾸지 않는다 (점검 항목).",
             "- 사진 파일은 `best_insta/`·`best_tistory/`에만 복사된다. 영상은 그 파일을 참조한다.", "",
             "| 사진 | 분류 | 고른 쪽 | 블로그 | 인스타 | 영상 | 이유 |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in sel_rows:
        ig = ("표지" if r["insta_cover"] else o(r["insta_order"])) if r["insta_order"] else "—"
        who = {"editor": "에디터", "ai": "AI"}.get(r["origin"], r["origin"])
        lines.append(f"| {r['id']} | {r['category'] or '—'} | {who} | {o(r['blog_order'])} | {ig} | {o(r['shorts_order'])} | {r['reason']} |")
    rest = [r["id"] for r in data["photos"] if not r["selected"]]
    lines += ["", f"선택 안 한 사진: {', '.join(rest) or '없음'}", "",
              "원본 위치: " + (str(Path(data['photos'][0]['original']).parent) if data["photos"] and data["photos"][0]["original"] else "—")]
    (p["work"] / "usage.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return data


# 채널별 최종 결과물 (vN 폴더 기준 상대경로). 끝이 /면 폴더 안 파일 수를 센다.
EXPECTED = {
    "instagram": [("카드 이미지", "card_*.jpg"), ("표지(썸네일)", "card_01.jpg"), ("캡션", "caption.txt")],
    "youtube": [("최종 MP4", "shorts.mp4"), ("영상 대본", "script.txt"), ("TTS 음성", "voice.m4a"),
                ("자막", "subtitles.srt"), ("제목·설명·태그", "meta.txt")],
    "tistory": [("블로그 글(HTML)", "post.html"), ("블로그 글(Markdown)", "article.md"), ("미리보기", "preview.html"),
                ("블로그 이미지", "images/*.jpg"), ("제목", "title.txt"), ("태그", "tags.txt")],
}


def outputs(work):
    """채널별 최신 버전 폴더에서 결과 파일을 실제로 찾아 [(채널, 버전, 상태, [(이름, 경로들, 있음?)])]을 돌려준다."""
    p = work_paths(work)
    st = load(p["state"])
    res = []
    for ch in CHANNELS:
        c = st["channels"][ch]
        if not c["version"]:
            res.append((ch, 0, c["status"], []))
            continue
        d = (p["work"] / ch / f"v{c['version']}").resolve()
        items = []
        for label, pat in EXPECTED[ch]:
            hits = sorted(d.glob(pat))
            items.append((label, [str(h) for h in hits], bool(hits) and all(h.stat().st_size > 0 for h in hits)))
        res.append((ch, c["version"], c["status"], items))
    return res


def write_outputs(work):
    p = work_paths(work)
    st = load(p["state"])
    lines = [f"# 결과물 위치 — {st['id']} {st['place']}", "",
             "✅ = 파일이 실제로 있음 · ❌ = 없음(성공으로 보지 않음). 경로를 누르면 열린다.", "",
             f"- 사진 사용표: [usage.md]({(p['work'] / 'usage.md').resolve().as_uri()})",
             f"- 콘텐츠대장: [ledger.xlsx]({p['ledger'].resolve().as_uri()})", ""]
    for ch, v, status, items in outputs(work):
        lines.append(f"## {CHANNEL_KO[ch]} — " + (f"v{v} ({status})" if v else "아직 없음"))
        for label, paths, ok in items:
            if not paths:
                lines.append(f"- ❌ {label}: 없음")
            elif len(paths) == 1:
                lines.append(f"- {'✅' if ok else '❌'} {label}: [{paths[0]}]({Path(paths[0]).as_uri()})")
            else:
                lines.append(f"- {'✅' if ok else '❌'} {label}: {len(paths)}개 — [{Path(paths[0]).parent}]({Path(paths[0]).parent.as_uri()})")
        lines.append("")
    p["outputs"].write_text("\n".join(lines), encoding="utf-8")
    return p["outputs"]
