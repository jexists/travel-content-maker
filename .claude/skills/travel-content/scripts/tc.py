"""travel-content 명령 모음.

  tc.py init     --work W --id C-001 --place 동막해변
  tc.py scan     --work W --src 사진폴더 [--keep 40]
  tc.py catalog  --work W                      # catalog.json → catalog.md + 분류별 썸네일
  tc.py select   --work W                      # selection.json → best_insta / best_tistory
  tc.py plan     --work W --approve | --reject --reason "…" [--by 대표]
  tc.py build    --work W --ch instagram|youtube|tistory
  tc.py confirm  --work W --ch … [--by 매니저]
  tc.py reject   --work W --ch … --reason "…" [--by 매니저]
  tc.py publish  --work W --ch … --url URL [--by 에디터]
  tc.py status   --work W                      # 진행 상황 + 결과물 위치(✅/❌) → OUTPUTS.md
  tc.py review   --work W --stage photos|plan|instagram|youtube|tistory   # 컨펌 카드

  인스타 사진 과정 (사용자가 고르는 흐름)
  tc.py insta-pick  --work W --src 사진폴더 [--ids P001,P002,…]   # 20장 이하는 전부, 넘으면 AI가 고른 20장 → insta_pick/
  tc.py insta-mine  --work W                    # 사용자 폴더 insta_mine/ 생성
  tc.py insta-use   --work W --dir insta_pick|insta_mine   # 사진 확정 → best_insta/
  tc.py insta-cover --work W --photo 3 --region 전남,강진 --title 가우도   # 표지 미리보기
  tc.py insta-order --work W --order 3,1,2,4    # 올라가는 순서 (표지는 항상 1번)
  tc.py tistory-photos --work W [--extra P007,…]   # 티스토리 = 인스타 사진 + 정보 사진
  tc.py ceo     --work W --ch … --approve | --reject --reason "…"   # 배포 직전 대표 승인
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import catalog as catalog_mod  # noqa: E402
import copy_best  # noqa: E402
import ledger  # noqa: E402
import state  # noqa: E402
import usage  # noqa: E402
from build_blog import build as build_blog  # noqa: E402
from check_rules import check  # noqa: E402
from common import CHANNEL_KO, load, save, settings, work_paths  # noqa: E402
from contact_sheet import sheets  # noqa: E402
from make_shorts import make as make_shorts, make_slideshow  # noqa: E402
from render_cards import render as render_cards  # noqa: E402


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def cmd_init(a):
    out(state.init(a.work, a.id, a.place))


def cmd_scan(a):
    state.get(a.work)
    d = __import__("scan_photos").scan(a.src, a.work, a.keep)
    p = work_paths(a.work)
    cands = [r for r in d["photos"] if r["status"] == "keep"]
    files = sheets([(r["id"], r["use"], r.get("taken", "")[5:16]) for r in cands], p["contact"], "candidates", "1차 후보 (시스템 필터 후)")
    state.photos_step(a.work, "scanned", memo=f"전체 {d['total']}장 → 후보 {d['kept']}장")
    reasons = {}
    for r in d["photos"]:
        if r["status"] == "reject":
            k = "거의 같은 사진" if "같은 사진" in r["reason"] else ("점수 낮음" if "초과" in r["reason"] else r["reason"])
            reasons[k] = reasons.get(k, 0) + 1
    out({"total": d["total"], "candidates": d["kept"], "rejected": reasons, "sheets": [str(f) for f in files]})


def cmd_catalog(a):
    res = catalog_mod.build(a.work)
    state.photos_step(a.work, "cataloged", actor="AI", memo=f"정리 후 {res['kept']}장 {res['counts']}")
    out(res)


def cmd_select(a):
    res = copy_best.copy(a.work)
    state.photos_step(a.work, "selected", actor="AI·에디터",
                      memo=f"인스타 {len(res['best_insta'])}장, 티스토리 {len(res['best_tistory'])}장, 중복 {len(res['overlap'])}장")
    out(res)


def cmd_plan(a):
    if a.reject and not a.reason:
        raise state.Refused("기획안을 반려할 때는 사유를 적어야 합니다.")
    state.plan(a.work, not a.reject, a.by or "대표", a.reason or "")
    out(state.get(a.work)["plan"])


def cmd_build(a):
    p = work_paths(a.work)
    ch = a.ch
    if ch == "tistory" and not p["best_tistory"].exists():
        raise state.Refused("티스토리 사진이 없습니다 (tistory-photos 먼저).")
    if ch == "instagram" and not load(p["content"]):
        raise state.Refused("content.json이 없습니다 (표지·순서·캡션을 먼저 정하세요).")
    v = state.start_build(a.work, ch)
    content = load(p["content"])
    st = state.get(a.work)
    out_dir = p["work"] / ch / f"v{v}"
    out_dir.mkdir(parents=True, exist_ok=True)
    save(out_dir / "content_snapshot.json", content)  # 이 버전을 만들 때의 문구를 그대로 보관
    cfg = settings(a.work)
    try:
        best_dir = _render(a, p, ch, content, st, out_dir, cfg)
    except SystemExit as e:  # 만들다 실패하면 '점검 실패'로 남기고 같은 버전으로 다시 만들 수 있게
        if isinstance(e, state.Refused):
            raise
        state.built(a.work, ch, v, False, str(out_dir.relative_to(p["work"].parent)))
        raise state.Refused(f"{CHANNEL_KO[ch]} 생성 실패: {e}")
    if ch == "youtube":
        best_dir = load(p["usage"], {}).get("shorts") or None  # 영상 사진 선택 순서 (ID 목록)
    passed, rows = check(ch, content, out_dir, best_dir, cfg)
    usage.write(a.work)
    state.built(a.work, ch, v, passed, str(out_dir.relative_to(p["work"].parent)))
    confirmed = False
    if getattr(a, "confirm", False) and passed:  # 확인 지점(A·B·C)에서 승인한 내용으로 만든 것 → 바로 에디터 컨펌
        state.confirm(a.work, ch, True, "에디터", "확인 지점에서 승인한 내용으로 제작")
        confirmed = True
    out({"channel": ch, "version": f"v{v}", "passed": passed, "confirmed": confirmed, "dir": str(out_dir),
         "failed": [f"{i}: {d}" for i, ok, d in rows if not ok]})


def _render(a, p, ch, content, st, out_dir, cfg):
    best_dir = None
    if ch == "instagram":
        import insta
        ow = insta.widths(a.work)
        if not ow:
            ph = {r["id"]: r for r in load(p["photos"])["photos"]}
            ow = {f.name: ph[f.stem.split("_")[-1]]["w"] for f in p["best_insta"].glob("*.jpg") if f.stem.split("_")[-1] in ph}
        render_cards(content, p["best_insta"], out_dir, cfg, ow)
        best_dir = p["best_insta"]
    elif ch == "youtube":
        ig = st["channels"]["instagram"]
        ig_dir = p["work"] / "instagram" / f"v{ig['version']}"
        script = content["youtube"].get("script")
        if script:
            scenes = []
            for sc in script["scenes"]:
                if sc["photo"] == "cover":  # 표지 사진을 화면 가득 (릴스는 첫 프레임이 가장 강해야 함)
                    cov = sorted(p["best_insta"].glob("01_*.jpg"))
                    scenes.append({**sc, "id": "cover", "src": cov[0] if cov else ig_dir / "card_01.jpg", "contain": not cov})
                else:
                    scenes.append({**sc, "id": sc["photo"], "src": usage.shorts_file(a.work, sc["photo"])})
            sh = {**cfg["shorts"], "pronounce": {**cfg["shorts"].get("pronounce", {}), **script.get("pronounce", {})}}
            make_shorts(scenes, out_dir, content["youtube"], sh, script.get("hook_text"), p["cache"] / "tts")
        else:
            make_slideshow(sorted(ig_dir.glob("card_*.jpg")), out_dir, content["youtube"])
    elif ch == "tistory":
        yt = st["channels"]["youtube"]
        url = yt.get("url") or content["youtube"].get("url")
        build_blog(content, p["best_tistory"], out_dir, url, cfg)
        best_dir = p["best_tistory"]
    return best_dir


def cmd_confirm(a):
    state.confirm(a.work, a.ch, True, a.by or "에디터")
    out(state.get(a.work)["channels"][a.ch])


def cmd_reject(a):
    state.confirm(a.work, a.ch, False, a.by or "에디터", a.reason or "")
    out(state.get(a.work)["channels"][a.ch])


def cmd_publish(a):
    state.published(a.work, a.ch, a.url, a.by or "에디터")
    if a.ch == "youtube":
        p = work_paths(a.work)
        c = load(p["content"])
        c["youtube"]["url"] = a.url
        save(p["content"], c)
    out(state.get(a.work)["channels"][a.ch])


def cmd_status(a):
    st = state.get(a.work)
    p = work_paths(a.work)
    if st.get("flow") == 2:
        lines = [f"{st['id']} {st['place']} · 인스타 사진: {st.get('insta_photos')} · 승인: 단계마다 에디터, 배포 직전 대표"]
    else:
        lines = [f"{st['id']} {st['place']} · 사진: {st['photos']} · 기획안: {st['plan']['status']}"]
    for ch, c in st["channels"].items():
        lines.append(f"  {CHANNEL_KO[ch]}: v{c['version']} {c['status']}" + (f" {c['url']}" if c.get("url") else ""))
    rows = [r for r in ledger.rows(p["ledger"]) if r["콘텐츠ID"] == st["id"]]
    lines.append(f"  대장 기록 {len(rows)}줄 → {p['ledger']}")
    if load(p["selection"]) or (p["work"] / "insta.json").exists():
        usage.write(a.work)
        lines.append(f"  사진 사용표 → {(p['work'] / 'usage.md').resolve()}")
    lines.append("")
    lines.append("결과물 (✅ 실제 파일 있음 · ❌ 없음)")
    for ch, v, status, items in usage.outputs(a.work):
        if not v:
            continue
        lines.append(f"  [{CHANNEL_KO[ch]} v{v}]")
        for label, paths, ok in items:
            where = paths[0] if len(paths) == 1 else (f"{len(paths)}개 · {Path(paths[0]).parent}" if paths else "없음")
            lines.append(f"    {'✅' if ok else '❌'} {label}: {where}")
    lines.append(f"  → {usage.write_outputs(a.work).resolve()}")
    print("\n".join(lines))


def _ids(v):
    return [x.strip() for x in v.split(",") if x.strip()] if v else []


def cmd_insta_pick(a):
    import insta
    res = insta.pick(a.work, a.src, _ids(a.ids))
    state.insta_step(a.work, "picked", "AI" if not res["auto"] else "시스템",
                     f"원본 {res['total']}장 → 후보 {res['count']}장" + (" (20장 이하라 전부)" if res["auto"] else ""))
    out(res)


def cmd_insta_mine(a):
    import insta
    res = insta.mine(a.work)
    state.insta_step(a.work, "mine_waiting", "에디터", "사용자가 직접 고르기로 함")
    out(res)


def cmd_insta_use(a):
    import insta
    res = insta.use(a.work, a.dir)
    state.insta_step(a.work, "fixed", "에디터", f"{a.dir} {res['count']}장 확정")
    out(res)


def cmd_insta_cover(a):
    import insta
    out(insta.cover(a.work, a.photo, _ids(a.region), a.title))


def cmd_insta_order(a):
    import insta
    out(insta.order(a.work, [int(x) for x in _ids(a.order)]))


def cmd_tistory_photos(a):
    import insta
    out(insta.tistory_extra(a.work, _ids(a.extra)))


def _channels(v):
    chs = ["instagram", "youtube", "tistory"] if v == "all" else _ids(v)
    bad = [c for c in chs if c not in ("instagram", "youtube", "tistory")]
    if bad or not chs:
        raise state.Refused(f"채널 이름 오류: {bad or v} (instagram, youtube, tistory, all)")
    return chs


def cmd_ceo(a):
    """대표 승인·반려. --ch all 이나 instagram,youtube 처럼 여러 채널을 한 번에."""
    if a.reject and not a.reason:
        raise state.Refused("대표 반려에는 사유를 적어야 합니다.")
    chs = _channels(a.ch)
    st = state.get(a.work)
    not_ready = [c for c in chs if st["channels"][c]["status"] != "confirmed"]
    if not_ready:  # 하나라도 컨펌 전이면 아무것도 바꾸지 않는다
        raise state.Refused("에디터 컨펌 전인 채널이 있어 대표 결정을 기록하지 않았습니다: "
                            + ", ".join(f"{CHANNEL_KO[c]}({st['channels'][c]['status']})" for c in not_ready))
    for c in chs:
        state.ceo(a.work, c, not a.reject, "대표", a.reason or "")
    st = state.get(a.work)
    out({c: st["channels"][c]["status"] for c in chs})


LINK_RULES = {"instagram": r"instagram\.com/(p|reel)/[\w-]+", "youtube": r"(youtube\.com/(shorts/|watch\?v=)|youtu\.be/)[\w-]{6,}",
              "tistory": r"\.tistory\.com/(\d+|entry/[^/\s]+)"}


def cmd_publish_all(a):
    """게시 링크를 한 번에 기록. 준 채널만, 링크 형식이 틀리면 아무것도 기록하지 않는다."""
    import re
    links = {c: getattr(a, c) for c in ("instagram", "youtube", "tistory") if getattr(a, c)}
    if not links:
        raise state.Refused("링크가 없습니다 (--instagram / --youtube / --tistory).")
    bad = [f"{CHANNEL_KO[c]}: {u}" for c, u in links.items() if not re.search(LINK_RULES[c], u)]
    if bad:
        raise state.Refused("게시물 링크가 아닙니다 (메인 주소가 아닌 게시물 주소를 주세요): " + " / ".join(bad))
    st = state.get(a.work)
    need = ("approved", "published") if st.get("flow") == 2 else ("confirmed", "published")
    early = [CHANNEL_KO[c] for c in links if st["channels"][c]["status"] not in need]
    if early:
        raise state.Refused("대표 승인 전 채널이 있어 기록하지 않았습니다: " + ", ".join(early))
    for c, u in links.items():
        state.published(a.work, c, u, "에디터")
        if c == "youtube":
            p = work_paths(a.work)
            cont = load(p["content"])
            cont["youtube"]["url"] = u
            save(p["content"], cont)
    usage.write_outputs(a.work)
    st = state.get(a.work)
    out({c: {"status": st["channels"][c]["status"], "url": st["channels"][c]["url"]} for c in links})


def cmd_review(a):
    import review
    print(review.card(a.work, a.stage))


def main():
    ap = argparse.ArgumentParser(description="여행 콘텐츠 3채널 제작")
    sub = ap.add_subparsers(dest="cmd", required=True)
    def sp(name, f, *args):
        s = sub.add_parser(name)
        s.add_argument("--work", required=True)
        for arg in args:
            s.add_argument(*arg[0], **arg[1])
        s.set_defaults(f=f)
    CH = (["--ch"], dict(required=True, choices=["instagram", "youtube", "tistory"]))
    BY = (["--by"], dict(default=None))
    sp("init", cmd_init, (["--id"], dict(required=True)), (["--place"], dict(required=True)))
    sp("scan", cmd_scan, (["--src"], dict(required=True)), (["--keep"], dict(type=int, default=40)))
    sp("catalog", cmd_catalog)
    sp("select", cmd_select)
    sp("plan", cmd_plan, (["--approve"], dict(action="store_true")), (["--reject"], dict(action="store_true")),
       (["--reason"], dict(default="")), BY)
    sp("build", cmd_build, CH, (["--confirm"], dict(action="store_true")))
    sp("confirm", cmd_confirm, CH, BY)
    sp("reject", cmd_reject, CH, (["--reason"], dict(required=True)), BY)
    sp("publish", cmd_publish, CH, (["--url"], dict(required=True)), BY)
    sp("status", cmd_status)
    sp("insta-pick", cmd_insta_pick, (["--src"], dict(required=True)), (["--ids"], dict(default="")))
    sp("insta-mine", cmd_insta_mine)
    sp("insta-use", cmd_insta_use, (["--dir"], dict(required=True)))
    sp("insta-cover", cmd_insta_cover, (["--photo"], dict(type=int, required=True)), (["--region"], dict(required=True)),
       (["--title"], dict(required=True)))
    sp("insta-order", cmd_insta_order, (["--order"], dict(required=True)))
    sp("tistory-photos", cmd_tistory_photos, (["--extra"], dict(default="")))
    sp("ceo", cmd_ceo, (["--ch"], dict(required=True)), (["--approve"], dict(action="store_true")),
       (["--reject"], dict(action="store_true")), (["--reason"], dict(default="")))
    sp("publish-all", cmd_publish_all, (["--instagram"], dict(default="")), (["--youtube"], dict(default="")),
       (["--tistory"], dict(default="")))
    sp("review", cmd_review, (["--stage"], dict(required=True, choices=[
        "brief", "script", "blog", "final", "photos", "plan", "instagram", "youtube", "tistory"])))
    a = ap.parse_args()
    try:
        a.f(a)
    except state.Refused as e:
        print(f"거절: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
