"""컨펌 카드 — 지금 무엇을, 왜, 어떤 선택지로 승인하는지 한 화면에 정리한다.

tc.py review --work W --stage photos|plan|instagram|youtube|tistory
AI는 이 출력을 그대로(또는 거의 그대로) 사용자에게 보여 주고 선택지 중 하나를 받는다.
"""
import re
from pathlib import Path

from common import CHANNEL_KO, load, work_paths

STEP = {"photos": 1, "plan": 2, "instagram": 3, "youtube": 4, "tistory": 5}
TITLE = {"photos": "사진 선택 확인", "plan": "대표 기획안 승인", "instagram": "인스타그램 카드 확인",
         "youtube": "유튜브 숏폼 확인", "tistory": "티스토리 블로그 확인"}


def _uri(p):
    return Path(p).resolve().as_uri()


def _link(label, p):
    return f"[{label}]({_uri(p)})" if Path(p).exists() else f"{label} (❌ 파일 없음)"


def _check_summary(d):
    f = Path(d) / "check.md"
    if not f.exists():
        return "점검 결과 없음", []
    t = f.read_text(encoding="utf-8")
    fails = re.findall(r"\| (.+?) \| ❌ \| (.+?) \|", t)
    manual = re.findall(r"수동 확인 필요: (.+)", t)
    head = "자동 점검 통과" if "**통과**" in t else f"자동 점검 실패 {len(fails)}건"
    return head, [f"❌ {a}: {b}" for a, b in fails] + [f"👀 직접 확인: {m}" for m in manual]


def card(work, stage):
    p = work_paths(work)
    st = load(p["state"])
    c = load(p["content"], {})
    u = load(p["usage"], {})
    L = [f"## [{STEP[stage]}/5] {TITLE[stage]} — {st['id']} {st['place']}", ""]
    status, done = None, False

    v2 = st.get("flow") == 2
    meta = load(p["work"] / "insta.json", {})
    if stage == "photos" and v2:
        ip = st.get("insta_photos", "none")
        done = ip == "fixed"
        pk = meta.get("pick", {})
        n = len(pk.get("photos", []))
        L += ["**지금 하는 일**: 인스타에 올릴 사진 폴더를 정합니다.", "",
              f"- 원본 {pk.get('total', '—')}장 → " + ("20장 이하라 **전부** 넣었어요." if pk.get("auto") else f"AI가 **{n}장**을 골랐어요."),
              f"- 폴더: `{(p['work'] / 'insta_pick').resolve()}`",
              f"- 미리보기: {_link('번호 시트', p['contact'] / 'insta_pick_01.jpg')}", "",
              "**선택**: `이대로 진행` · `싫어요 (내가 고를게요)`", "",
              "**진행하면**: 이 사진들로 표지 1장을 추천합니다.",
              "**싫다고 하면**: 빈 폴더 `insta_mine/`을 만들어 드려요. 거기에 사진을 넣고 알려 주세요."]
        if ip == "mine_waiting":
            L += ["", f"> ⏸ 사진을 기다리는 중: `{(p['work'] / 'insta_mine').resolve()}`"]
    elif stage == "photos":
        done = st["plan"]["status"] == "approved"
        cover = u.get("cover")
        L += ["**지금 하는 일**: 콘텐츠에 쓸 사진과 순서를 정합니다.", "",
              "| 용도 | 장수 | 순서 |", "| --- | --- | --- |",
              f"| 블로그 | {len(u.get('blog', []))} | {' → '.join(u.get('blog', []))} |",
              f"| 인스타 | {len(u.get('instagram', []))} | {' → '.join(u.get('instagram', []))} |",
              f"| 영상 | {len(u.get('shorts', []))} | {' → '.join(u.get('shorts', []))} |", "",
              f"- 대표 이미지(인스타 표지): **{cover}** · 블로그 대표: **{(u.get('blog') or ['—'])[0]}**",
              f"- 미리보기: {_link('선택 시트(인스타)', p['contact'] / 'selected_insta_01.jpg')} · "
              f"{_link('선택 시트(블로그)', p['contact'] / 'selected_tistory_01.jpg')} · {_link('사진 사용표', p['work'] / 'usage.md')}", "",
              "**확인할 것**", "- 빠진 사진·뺄 사진이 있나요?", "- 대표 이미지가 맞나요?", "- 순서를 바꿀 곳이 있나요?", "",
              "**선택**: `승인` · `사진 변경: P00x 빼기/넣기` · `순서 변경: …` · `대표 변경: P00x`", "",
              "**승인하면**: 여행지 정보·SEO 키워드를 정리해 대표 기획안을 만듭니다. 대표 승인 뒤에는 사진을 바꿀 수 없습니다."]
    elif stage == "plan":
        done = st["plan"]["status"] == "approved"
        seo, info = c.get("seo", {}), c.get("info", {})
        unver = info.get("unverified", [])
        L += ["**지금 하는 일**: 3채널 제작 전에 방향을 한 번 승인받습니다 (처음 1회).", "",
              f"- 표지: **{u.get('cover')}** · 지역 태그: {' '.join('#' + r for r in c.get('region', []))} · 협찬: {'예' if c.get('sponsored') else '아니오'}",
              f"- SEO 메인: **{seo.get('main')}** · 보조: {', '.join(seo.get('sub', []))} (AI 추천 키워드, 검색량 데이터 없음)",
              f"- 채널 제목(초안): 유튜브 「{c.get('youtube', {}).get('title', '')}」 · 티스토리 「{c.get('tistory', {}).get('title', '')}」",
              f"- 여행지 정보 출처 {len(info.get('sources', []))}곳 · **방문 전 확인 필요**: {', '.join(unver) or '없음'}", "",
              "**확인할 것**", "- 표지와 키워드 방향이 맞나요?", "- 확인 필요 정보를 이대로 '방문 전 확인'으로 둘까요?", "",
              "**선택**: `대표 승인` · `대표 반려: 사유`", "",
              "**승인하면**: 인스타 카드 → 유튜브 숏폼 → 티스토리 순서로 만듭니다. 반려되면 사유대로 사진·정보를 고쳐 다시 올립니다."]
    else:
        ch = stage
        cs = st["channels"][ch]
        status = cs["status"]
        done = status in ("confirmed", "published")
        d = p["work"] / ch / f"v{cs['version']}"
        head, issues = _check_summary(d)
        kind = {"approved": "최종 (대표 승인됨 — 배포 가능)", "published": "게시 완료",
                "confirmed": "에디터 컨펌됨 — 대표 승인 대기"}.get(status, "미리보기 (컨펌 전 — 아직 게시용 아님)")
        done = status in ("approved", "published") if v2 else done
        L += [f"**버전**: v{cs['version']} · {kind} · {head}", ""]
        if ch == "instagram":
            ig = c["instagram"]
            L += ["**지금 하는 일**: 인스타 캐러셀(첫 장만 표지 디자인, 나머지는 원본 사진)을 확인합니다.", "",
                  f"- 표지: {_link('card_01.jpg', d / 'card_01.jpg')} — `{' '.join('#' + r for r in c['region'])}` / `{ig.get('cover_title') or c['place']}`",
                  f"- 카드 {len(ig["cards"])}장 · 해시태그 {len(ig['hashtags'])}개",
                  f"- 캡션 첫 줄: 「{ig['caption'].splitlines()[0]}」 → {_link('caption.txt', d / 'caption.txt')}", "",
                  "**확인할 것**", "- 표지 문구(지역·장소명)가 맞나요?", "- 캡션 톤이 계정과 맞나요?", "",
                  "**선택**: `컨펌` · `반려: 표지 문구 …` · `반려: 캡션 …`", "",
                  "**고치면 바뀌는 범위**: 반려 사유에 해당하는 부분(표지 문구 또는 캡션·해시태그)만 고쳐 v다음 버전을 만듭니다. 사진은 그대로.",
                  "**컨펌하면**: 이 표지 카드와 사진으로 유튜브 숏폼을 만듭니다."]
        elif ch == "youtube":
            tl = load(d / "timeline.json", {})
            sc = tl.get("scenes", [])
            L += ["**지금 하는 일**: 숏폼 영상(대본·TTS·자막)을 확인합니다.", "",
                  f"- 길이 {tl.get('total', 0):.1f}초 · 장면 {len(sc)}개 · 목소리 {tl.get('voice', '—')} (속도 {tl.get('rate', '—')}) · 자막 흰 글자+검은 테두리 2줄 이하",
                  f"- 장면: " + " → ".join(f"{s['id']}({s['duration']:.1f}초)" for s in sc),
                  f"- 첫 문장(훅): 「{(c['youtube'].get('script') or {}).get('scenes', [{}])[0].get('narration', '')}」",
                  f"- 파일: {_link('shorts.mp4', d / 'shorts.mp4')} · {_link('대본', d / 'script.txt')} · {_link('자막', d / 'subtitles.srt')} · {_link('음성', d / 'voice.m4a')}", "",
                  "**확인할 것**", "- 대본이 자연스럽게 들리나요?", "- 장면과 말이 맞나요?", "",
                  "**선택**: `컨펌` · `반려: 대본 …` · `반려: 음성 …` · `반려: 장면 …`", "",
                  "**고치면 바뀌는 범위**: 대본·음성(settings 목소리·속도)·장면 사진 중 사유에 해당하는 것만 바꿔 영상을 다시 만듭니다.",
                  "**컨펌하면**: 티스토리 글을 만듭니다 (유튜브 링크가 있으면 글에 넣음)."]
        else:
            ts = c["tistory"]
            L += ["**지금 하는 일**: 티스토리 글(글·사진 교차 배치)을 확인합니다.", "",
                  f"- 제목: 「{ts['title']}」" + (f" (후보 {len(ts['title_candidates'])}개 중 선택)" if ts.get("title_candidates") else ""),
                  f"- 첫 문단: 「{ts['intro'][:70]}…」",
                  f"- 구성: 도입 → " + " → ".join(s["h2"] for s in ts["sections"]) + " → 기본 정보 → 마무리",
                  f"- 사진 {len(list((d / 'images').glob('*.jpg')))}장 · 대표 이미지 {(d / 'cover.txt').read_text(encoding='utf-8').strip() if (d / 'cover.txt').exists() else '—'}",
                  f"- 미리보기: {_link('preview.html', d / 'preview.html')} · {_link('article.md', d / 'article.md')}", "",
                  "**확인할 것**", "- 제목이 괜찮나요?", "- 본문이 실제로 다녀온 글처럼 읽히나요?", "",
                  "**선택**: `컨펌` · `반려: 제목 …` · `반려: 본문 …` · `다시 생성`", "",
                  "**고치면 바뀌는 범위**: 제목 반려는 제목만, 본문 반려는 해당 소제목의 문단만 고칩니다. 사진 배치는 그대로.",
                  "**컨펌하면**: 업로드 단계로 넘어갑니다. 실제 게시 직전에 다시 확인을 받습니다."]
        if issues:
            L += ["", "**점검 메모**"] + [f"- {x}" for x in issues]
        if v2 and status == "confirmed":
            L += ["", "---", f"### 배포 전 대표 승인 — {CHANNEL_KO[ch]} v{cs['version']}",
                  "에디터 컨펌이 끝났습니다. 대표가 승인하면 업로드합니다 (인스타 공유 버튼은 사용자가 누름).", "",
                  "**선택**: `대표 승인` · `대표 반려: 사유`"]
        if status == "check_failed":
            L += ["", "> ⚠️ 자동 점검을 통과하지 못해 아직 컨펌을 요청하지 않습니다. 위 ❌ 항목을 고친 뒤 다시 만듭니다."]
    if done:
        L = L[:2] + ["✅ 이미 승인된 단계입니다 — 다시 묻지 않습니다.", ""] + L[2:]
    if v2 and stage == "plan":
        L = [f"## 기획안 승인 단계는 없습니다 — {st['id']}", "", "대표 승인은 각 채널 배포 직전에 받습니다 (`tc.py ceo`)."]
    return "\n".join(L)
