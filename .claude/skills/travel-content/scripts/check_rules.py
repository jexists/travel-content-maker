"""게시 규칙 점검 — 결과물을 rules.json으로 검사하고 check.md를 남긴다."""
import json
import re
import subprocess
from pathlib import Path

from common import RULES, load, settings


def _probe(mp4):
    """(너비, 높이, 영상 길이, 음성 길이) — 음성 트랙이 없으면 음성 길이 0."""
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=codec_type,width,height,duration:format=duration", "-of", "json", str(mp4)],
                         capture_output=True, text=True)
    d = json.loads(out.stdout or "{}")
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), {})
    return (v.get("width", 0), v.get("height", 0), float(v.get("duration") or d.get("format", {}).get("duration", 0)),
            float(a.get("duration", 0)))


def _sentences(text):
    return [p.strip() for p in re.split(r"(?<=[.?!…])(?!\d)\s+", text.strip()) if p.strip()]


def script_rows(script, R=None):
    """숏폼 대본(content.youtube.script) 글 규칙 — 영상을 만들기 전에 검사한다 (references/prompts/shorts.md).
    반환: [(항목, 통과, 설명)]"""
    from difflib import SequenceMatcher
    R = R or load(RULES)
    S = R["youtube"].get("script", {})
    rows = []
    scenes = script.get("scenes", [])
    n = len(scenes)
    lo, hi = S.get("scenes_min", 5), S.get("scenes_max", 8)
    rows.append(("장면 수", lo <= n <= hi, f"{n}개 (기준 {lo}~{hi})"))
    roles = [s.get("role", "body") for s in scenes]
    ok = n >= 2 and roles[0] == "hook" and roles[-1] == "cta" and all(r == "body" for r in roles[1:-1])
    rows.append(("장면 구성 (hook → body → cta)", ok, " → ".join(roles)))
    narr = [s.get("narration", "") for s in scenes]
    total = sum(len(x) for x in narr)
    tlo, thi = S.get("narration_total_min", 110), S.get("narration_total_max", 170)
    rows.append(("내레이션 합계", tlo <= total <= thi, f"{total}자 (기준 {tlo}~{thi}자 ≈ 15~25초)"))
    sents = [(i + 1, t) for i, x in enumerate(narr) for t in _sentences(x)]
    smax = S.get("sentence_max", 35)
    long_ = [f"장면{i} {len(t)}자" for i, t in sents if len(t) > smax]
    rows.append(("한 문장 길이", not long_, f"모두 {smax}자 이하" if not long_ else ", ".join(long_)))
    formal = [f"장면{i}: {t}" for i, t in sents if re.search(r"(니다|니까)[.?!…]?$", t)]
    rows.append(("해요체 (합니다체 금지)", not formal, "모두 해요체" if not formal else " / ".join(formal)))
    badq = [f"장면{i}: {t}" for i, t in sents if t.endswith("?") and not re.search(r"(죠|까요|나요)\?$", t)]
    rows.append(("질문 어미 (~죠?·~까요?·~나요?)", not badq, "문제 없음" if not badq else " / ".join(badq)))
    marks = [f"장면{i}" for i, t in sents if "!" in t]
    rows.append(("느낌표 없음 (TTS 어색)", not marks, "없음" if not marks else ", ".join(marks)))
    hook = script.get("hook_text", "")
    if hook:
        hl = [l for l in hook.split("\n") if l.strip()]
        hmax = S.get("hook_max", 20)
        hn = len("".join(hl))
        rows.append(("훅 문구 길이", hn <= hmax and len(hl) <= 2, f"{hn}자 {len(hl)}줄 (기준 {hmax}자·2줄 이내)"))
        sq = lambda s: re.sub(r"[\s.,?!…]", "", s)
        first = _sentences(narr[0])[0] if narr and narr[0] else ""
        sim = SequenceMatcher(None, sq(hook), sq(first)).ratio() if first else 0
        rows.append(("훅 문구 ≠ 첫 문장", sim < 0.6, f"비슷한 정도 {sim:.0%} (60% 미만)"))
    words = S.get("filler_words", []) + R["common"].get("banned_words", [])
    alltext = hook + " " + " ".join(narr)
    hit = [w for w in words if w in alltext]
    rows.append(("빈말·금지어 없음", not hit, "없음" if not hit else ", ".join(hit)))
    if narr:
        ends = [w for w in S.get("cta_endings_banned", []) if w in narr[-1]]
        rows.append(("마지막 장면 인사·응원·구독 요청 없음", not ends, "없음" if not ends else ", ".join(ends)))
    return rows


def check(ch, content, out_dir, best_dir=None, cfg=None):
    cfg = cfg or settings()
    R = load(RULES)
    C, r = R["common"], R[ch]
    place, main = content["place"], content["seo"]["main"]
    sponsored = content.get("sponsored", False)
    rows = []

    notes = []

    def add(item, ok, detail):
        rows.append((item, bool(ok), detail))

    def warn(text):
        notes.append(text)

    if ch == "instagram":
        ig = content["instagram"]
        text = ig["caption"] + " " + " ".join(ig["hashtags"]) + " " + " ".join(c.get("text", "") for c in ig["cards"])
        n = len(ig["cards"])
        add("카드 장수", r["cards_min"] <= n <= r["cards_max"], f"{n}장 (기준 {r['cards_min']}~{r['cards_max']})")
        add("표지 지역 태그", len(content["region"]) == r["cover_tags"], " ".join("#" + x for x in content["region"]))
        cap = len(ig["caption"]) + len(" ".join(ig["hashtags"]))
        add("캡션 길이 (플랫폼 제한)", cap <= r["caption_max"], f"{cap}자 / {r['caption_max']}자")
        h = len(ig["hashtags"])
        add("해시태그 개수", r["hashtags_min"] <= h <= r["hashtags_max"], f"{h}개 (팀 기준 {r['hashtags_min']}~{r['hashtags_max']}, 플랫폼 {r['hashtags_platform_max']})")
        add("해시태그 형식", all(t.startswith("#") and " " not in t for t in ig["hashtags"]), "모두 #으로 시작, 공백 없음")
        add("장소명 포함", place in text, place)
        add("SEO 메인 키워드", main.replace(" ", "") in text.replace(" ", ""), main)
        files = sorted(Path(out_dir).glob("card_*.jpg"))
        add("카드 파일 생성", len(files) == n and all(f.stat().st_size > 0 for f in files), f"{len(files)}개 파일")
        best = sorted(x.name for x in Path(best_dir).glob("*.jpg")) if best_dir else []
        used = [c["photo"] for c in ig["cards"]]
        if best:
            add("사진 순서 유지", used == best[:len(used)], "선택 순서 그대로" if used == best[:len(used)] else f"카드 {used} ≠ 선택 {best}")
        S = cfg.get("instagram", {})
        if not S.get("text_on_other_images"):
            extra = [i + 2 for i, c in enumerate(ig["cards"][1:]) if c.get("text") and not c.get("force_text")]
            add("표지 외 카드 문구 없음", True, "2장부터 원본 사진만" + (f" (카드 {extra}의 text는 무시됨)" if extra else ""))
        if files:
            from PIL import Image
            sizes = {Image.open(f).size for f in files}
            ratios = {round(h / w, 3) for w, h in sizes}
            warn(f"카드 비율 {', '.join(f'{w}×{h}' for w, h in sorted(sizes))}"
                 + (" — 비율이 서로 달라 인스타가 첫 장 비율로 잘라 보여 줌" if len(ratios) > 1 else "")
                 + (" — 4:5보다 세로가 길면 피드에서 위아래가 잘릴 수 있음" if max(ratios) > 1.25 else ""))
        if sponsored:
            add("광고 표시 (첫 장 안)", True, f"표지에 '{C['sponsor_label']}' 표시 렌더링")
    elif ch == "youtube":
        yt = content["youtube"]
        text = yt["title"] + " " + yt["description"] + " " + " ".join(yt["tags"])
        add("제목 길이 (플랫폼 제한)", len(yt["title"]) <= r["title_max"], f"{len(yt['title'])}자 / {r['title_max']}자")
        add("SEO 메인 키워드 (제목)", main.replace(" ", "") in yt["title"].replace(" ", ""), main)
        add("장소명 포함", place in text, place)
        add("태그 개수", len(yt["tags"]) >= r["tags_min"], f"{len(yt['tags'])}개 (최소 {r['tags_min']})")
        if yt.get("script"):
            for row in script_rows(yt["script"], R):
                add("대본 · " + row[0], row[1], row[2])
        mp4 = Path(out_dir) / "shorts.mp4"
        tl = load(Path(out_dir) / "timeline.json")
        if mp4.exists() and mp4.stat().st_size:
            w, h, dur, a_dur = _probe(mp4)
            add("영상 비율", (w, h) == (r["width"], r["height"]), f"{w}×{h}")
            add("영상 길이", r["duration_min"] <= dur <= r["duration_max"], f"{dur:.1f}초 (기준 {r['duration_min']}~{r['duration_max']})")
            if tl:
                add("음성 트랙", a_dur > 0, f"{a_dur:.1f}초" if a_dur else "소리 없음")
                last_speech = max(s["speech_end"] for s in tl["scenes"])
                add("음성이 끝까지 들어감", last_speech + 0.3 <= dur and a_dur + 0.1 >= dur,
                    f"마지막 말 끝 {last_speech:.1f}초 · 영상 {dur:.1f}초 · 음성 {a_dur:.1f}초")
                add("마지막 장면 여유", dur - last_speech >= 0.5, f"말이 끝난 뒤 {dur - last_speech:.1f}초 (기준 0.5초 이상)")
                pages = [pg for s in tl["scenes"] for pg in s["pages"]]
                srt = (Path(out_dir) / "subtitles.srt").read_text(encoding="utf-8") if (Path(out_dir) / "subtitles.srt").exists() else ""
                cues = re.findall(r"--> (\d+):(\d+):(\d+),(\d+)", srt)
                end = max((int(a) * 3600 + int(b) * 60 + int(c) + int(d) / 1000 for a, b, c, d in cues), default=0)
                add("자막 파일", cues and len(cues) == len(pages) and end <= dur + 0.05, f"{len(cues)}개 자막 · 마지막 {end:.1f}초")
                SS = cfg.get("shorts", {}).get("subtitle", {})
                side = SS.get("safe_side", 90)
                bad = [pg["lines"] for s in tl["scenes"] for pg in s["pages"]
                       if pg["box"][0] < side or pg["box"][2] > r["width"] - side
                       or (not s["contain"] and not (SS.get("safe_top", 0) <= pg["box"][1] and pg["box"][3] <= SS.get("safe_bottom", r["height"])))]
                add("자막 안전 영역", not bad, f"{len(pages)}개 모두 화면 안 (좌우 {side}px 여백)" if not bad else f"벗어남: {bad}")
                add("자막 줄 수", all(len(pg["lines"]) <= SS.get("max_lines", 2) for pg in pages), f"한 화면 최대 {max(len(pg['lines']) for pg in pages)}줄")
                ids = [s["id"] for s in tl["scenes"] if s["id"] != "cover"]
                if best_dir:
                    ok = ids == [x for x in best_dir if x in ids]
                    add("사진 순서 유지", ok, "영상 사진 선택 순서 그대로" if ok else f"장면 {ids} ≠ 선택 {best_dir}")
                for name in ("voice.m4a", "subtitles.srt", "script.txt"):
                    f = Path(out_dir) / name
                    add(f"{name} 생성", f.exists() and f.stat().st_size > 0, "있음" if f.exists() else "없음")
                if tl.get("hook_box"):
                    hb = tl["hook_box"]
                    first_sub = min((pg["box"][1] for s in tl["scenes"] for pg in s["pages"] if not s["contain"]), default=r["height"])
                    add("훅 문구 위치", hb[0] >= side and hb[2] <= r["width"] - side and hb[3] < first_sub,
                        f"「{tl['hook']}」 화면 위 고정, 자막과 안 겹침")
                if tl.get("engine") != "openai":
                    warn(f"TTS: {tl.get('voice')} — OpenAI 키가 없어 예비 엔진으로 만들었어요 (.env에 OPENAI_API_KEY)")
                manual = ["TTS 발음·억양이 자연스러운지", "장면 전환이 어색하지 않은지", "자막과 말이 같은 순간에 바뀌는지 (문장 단위로 맞춤, 문장 안 페이지는 글자 수 비율)"]
                for m in manual:
                    warn("수동 확인 필요: " + m)
        else:
            add("영상 파일 생성", False, "shorts.mp4 없음")
        if sponsored:
            add("광고 표시 (제목)", C["sponsor_label"] in yt["title"] or "광고" in yt["title"], yt["title"])
    elif ch == "tistory":
        ts = content["tistory"]
        html = (Path(out_dir) / "post.html").read_text(encoding="utf-8") if (Path(out_dir) / "post.html").exists() else ""
        body = re.sub(r"<[^>]+>", " ", html)
        imgs = re.findall(r"<img [^>]*>", html)
        tmin = r.get("title_min", 0)
        add("제목 길이", tmin <= len(ts["title"]) <= r["title_max"], f"{len(ts['title'])}자 (기준 {tmin}~{r['title_max']}자)")
        add("제목이 메인 키워드로 시작", ts["title"].replace(" ", "").startswith(main.replace(" ", "")), main)
        from build_blog import layout as _lay
        body_txt = " ".join(it[1] for it in _lay(content) if it[0] == "text") + " " + ts.get("outro", "")
        if r.get("body_min_chars"):
            n_chars = len(body_txt.strip())
            add("본문 분량", n_chars >= r["body_min_chars"], f"{n_chars}자 (최소 {r['body_min_chars']}자)")
        if r.get("main_keyword_min"):
            kc = body_txt.replace(" ", "").count(main.replace(" ", ""))
            add("메인 키워드 횟수 (본문)", r["main_keyword_min"] <= kc <= r["main_keyword_max"],
                f"{kc}회 (기준 {r['main_keyword_min']}~{r['main_keyword_max']}회)")
        if ts.get("title_candidates") is not None:
            add("제목 후보", len(ts["title_candidates"]) >= 5, f"{len(ts['title_candidates'])}개 (기준 5개, 사용자 확인용)")
        md_hits = [x for x in ("**", "##", "# ") if x in body_txt]
        add("본문 마크다운 기호 없음", not md_hits, "없음" if not md_hits else ", ".join(md_hits))
        add("SEO 메인 키워드 (제목)", main.replace(" ", "") in ts["title"].replace(" ", ""), main)
        first = ts["intro"]
        add("SEO 메인 키워드 (첫 문단)", main.replace(" ", "") in first.replace(" ", ""), first[:40] + "…")
        add("사진 수", len(imgs) >= r["photos_min"], f"{len(imgs)}장 (최소 {r['photos_min']})")
        add("사진 대체 텍스트(alt)", imgs and all(re.search(r'alt="[^"]+"', i) for i in imgs), "모든 사진에 alt")
        h2 = html.count("<h2")
        add("소제목 수", h2 >= r["h2_min"], f"{h2}개 (최소 {r['h2_min']})")
        add("태그 개수", r["tags_min"] <= len(ts["tags"]) <= r["tags_max"], f"{len(ts['tags'])}개 (기준 {r['tags_min']}~{r['tags_max']})")
        add("유튜브 링크", True, "삽입됨" if "youtube.com/embed" in html else "없음 (선택 항목)")
        from build_blog import layout
        seq = layout(content)
        used = [it[1] for it in seq if it[0] == "photo"]
        B = cfg.get("blog", {})
        files = re.findall(r'<img src="(images/[^"]+)"', html)
        missing = [f for f in files if not (Path(out_dir) / f).exists() or not (Path(out_dir) / f).stat().st_size]
        add("본문 사진 파일 존재", files and not missing, f"{len(files)}장 모두 images/에 있음" if not missing else f"없음: {missing}")
        best = sorted(x.name for x in Path(best_dir).glob("*.jpg")) if best_dir else []
        if best:
            dup = sorted({u for u in used if used.count(u) > 1})
            left = [b for b in best if b not in used]
            add("선택 사진 모두 사용", not left and not dup, "best_tistory 전부 1번씩" if not left and not dup else f"빠짐 {left} · 중복 {dup}")
            if B.get("preserve_image_order", True):
                ok = used == [b for b in best if b in used]
                add("사진 순서 유지", ok, "선택 순서 그대로" if ok else f"본문 {used}")
        run, worst = 0, 0
        for it in seq:
            run = run + 1 if it[0] == "photo" else 0
            worst = max(worst, run)
        mx = B.get("max_consecutive_photos", 2)
        add("글·사진 교차 배치", worst <= mx, f"사진 연속 최대 {worst}장 (기준 {mx}장 이하)")
        bare = [it[1] for i, it in enumerate(seq) if it[0] == "h2" and not any(
            x[0] == "text" for x in seq[i + 1:next((j for j in range(i + 1, len(seq)) if seq[j][0] == "h2"), len(seq))])]
        add("소제목마다 글 있음", not bare, "모든 소제목 아래 문단 있음" if not bare else f"사진만 있는 소제목: {bare}")
        text = body
        if sponsored:
            add("광고 표시 (본문 첫 줄)", C["sponsor_notice"][:10] in body[:400], "본문 맨 앞")
    else:
        raise ValueError(ch)

    full = json.dumps(content.get(ch, {}), ensure_ascii=False)
    hits = [w for w in C["banned_words"] if w in full]
    add("금지 표현", not hits, ", ".join(hits) if hits else "없음")
    if not sponsored:
        add("협찬 여부", True, "협찬 아님 — 광고 표시 불필요")

    passed = all(ok for _, ok, _ in rows)
    md = [f"# 게시 규칙 점검 — {ch}", "", f"결과: **{'통과' if passed else '실패'}**", "",
          "| 항목 | 결과 | 내용 |", "| --- | --- | --- |"]
    md += [f"| {i} | {'✅' if ok else '❌'} | {d} |" for i, ok, d in rows]
    if notes:
        md += ["", "## 참고 (실패 아님)", ""] + [f"- ⚠️ {t}" for t in notes]
    (Path(out_dir) / "check.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return passed, rows
