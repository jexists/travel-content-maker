"""발표 HTML 3판 만들기 — dev-ppt-maker template.html + slides.src.html

python3 docs/presentation/build.py [_v2]
  index.html     전체 (발표용)
  analysis.html  업무 분석 · 개선 설계 (구현물·한계 포함)
  run.html       실행 방법
PDF는 export_pdfs.sh.
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TPL = Path.home() / ".claude/skills/dev-ppt-maker/assets/template.html"

TOKENS_LIGHT = {"--accent": "#0F6E56", "--accent-ink": "#0B5A46", "--accent-c": "#E3F2EC"}
TOKENS_DARK = {"--accent": "#3CC39A", "--accent-ink": "#6FD9B5", "--accent-c": "#10261F"}
EXTRA_CSS = """
/* travel-content 추가 */
.fit { background: #fff; border: 1.5px solid var(--shot-line); border-radius: 14px; overflow: hidden; display: flex; align-items: center; justify-content: center; }
.fit img { width: 100%; height: 100%; object-fit: contain; display: block; }
.need-cap { border: 3px dashed var(--subtle); border-radius: 14px; background: var(--card2); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 14px; text-align: center; padding: 30px; color: var(--muted); }
.need-cap b { font-size: 30px; color: var(--ink); }
.need-cap span { font-size: 22px; line-height: 1.5; }
pre.code-out { font: 500 22px/1.55 var(--font-mono); background: var(--card2); border: 1.5px solid var(--line); border-radius: 12px; padding: 20px 24px; white-space: pre; overflow: hidden; color: var(--ink); }
ol.nums { padding-left: 34px; display: flex; flex-direction: column; gap: 10px; font-size: 25px; }
ol.nums li::marker { font-family: var(--font-mono); color: var(--accent); font-weight: 700; }
code { font-family: var(--font-mono); font-size: .9em; }
/* 표지: 초록 막대가 kicker~발표자까지 감싸도록, 버튼·안내 간격 */
.cover .bar { display: none; }
.cover .inner { max-width: 1500px; }
.cover .ctext { display: flex; flex-direction: column; gap: 28px; border-left: 14px solid var(--accent); margin-left: -64px; padding: 6px 0 6px 50px; }
.cover .keyhint { margin-top: 18px; }
.toc-grid { grid-template-columns: repeat(4, 1fr); gap: 0 44px; }

"""
VARIANTS = {
    "index.html": dict(parts=None, kicker="AX Campus 1기 · 4회차 개인 과제",
                       title="여행 콘텐츠 3채널 자동화", h1="여행 콘텐츠<br>3채널 자동화", sub="사진 폴더 하나로 인스타 카드뉴스 · 유튜브 숏폼 · 티스토리 블로그"),
    "analysis.html": dict(parts={"intro", "asis", "tobe", "impl", "end"}, kicker="제출물 ①·② · 현재 업무 분석과 개선 설계",
                          title="여행 콘텐츠 3채널 자동화", h1="여행 콘텐츠<br>3채널 자동화", sub="As-Is 분석 · To-Be 설계 · 구현 결과"),
    "run.html": dict(parts={"run"}, kicker="제출물 ③ · 실행 방법",
                     title="travel-content 실행 방법", h1="travel-content<br>실행 방법", sub="설치부터 결과 확인까지 8단계"),
}
WHO = "정주애 · 2026.11.11"


def tokens(css, block_sel, vals):
    start = css.index(block_sel)
    end = css.index("}", start)
    block = css[start:end]
    for k, v in vals.items():
        block = re.sub(rf"{re.escape(k)}:\s*[^;]+;", f"{k}: {v};", block, count=1)
    return css[:start] + block + css[end:]


def build(ver=""):
    """ver="" → slides.src.html → index.html …, ver="_v2" → slides_v2.src.html → index_v2.html …"""
    tpl = TPL.read_text(encoding="utf-8")
    tpl = tokens(tpl, ':root, html[data-theme="light"]', TOKENS_LIGHT)
    tpl = tokens(tpl, 'html[data-theme="dark"]', TOKENS_DARK)
    tpl = tpl.replace("</style>", EXTRA_CSS + "</style>", 1)
    tpl = re.sub(r"<template id=\"opt-[^\"]+\">.*?</template>\s*", "", tpl, flags=re.S)  # 쓰지 않는 선택 조각 제거
    # 내용 장 자리 표시 1장을 지운다 (목차 장 다음 ~ </main>)
    toc_end = tpl.index("</section>", tpl.index('data-title="목차"')) + len("</section>")
    main_end = tpl.index("</main>")
    head, tail = tpl[:toc_end], tpl[main_end:]
    src = (HERE / f"slides{ver}.src.html").read_text(encoding="utf-8")
    slides = re.findall(r"<section class=\"slide\" data-part=\"(\w+)\".*?</section>", src, flags=re.S)
    blocks = re.findall(r"(<section class=\"slide\" data-part=\"\w+\".*?</section>)", src, flags=re.S)
    for name, v in VARIANTS.items():
        v = dict(v)
        if ver == "_v2" and name == "run.html":
            v["sub"] = "스킬 zip 하나로 3단계 · Mac·Windows"
        chosen = [b for p, b in zip(slides, blocks) if v["parts"] is None or p in v["parts"]]
        html = head + "\n\n" + "\n\n".join(chosen) + "\n\n" + tail
        html = re.sub(r'(<div class="kicker r">\{\{행사·과목 이름\}\}</div>.*?<div class="who r">.*?</div>)',
                      r'<div class="ctext">\1</div>', html, count=1, flags=re.S)
        html = html.replace('<h1 class="r">{{발표 제목}}</h1>', f'<h1 class="r">{v.get("h1", v["title"])}</h1>', 1)
        html = (html.replace("{{발표 제목}}", v["title"]).replace("{{행사·과목 이름}}", v["kicker"])
                    .replace("{{한 줄 설명 — 명사형}}", v["sub"]).replace("{{발표자}} · {{YYYY.MM.DD}}", WHO))
        # 목차: 섹션을 순서대로 왼쪽 열부터 채운다 (원래 템플릿은 가장 가벼운 열에 넣어 순서가 섞였음)
        html = html.replace("const k = load.indexOf(Math.min(...load));  // 가장 가벼운 열에\n        cols[k].appendChild(g); load[k] += items.length + 1;",
                            "const size = items.length + 1; if (c < 3 && load[c] > 0 && load[c] + size / 2 > per) c += 1;\n        cols[c].appendChild(g); load[c] += size;")
        html = html.replace("const cols = [0, 1, 2].map(", "const cols = [0, 1, 2, 3].map(")
        html = html.replace("const load = [0, 0, 0];", "const load = [0, 0, 0, 0]; let c = 0; const per = [...groups].reduce((a, [, it]) => a + it.length + 1, 0) / 4;")
        if v["parts"] is not None:  # 부분판은 목차 번호가 달라지므로 kicker의 섹션 번호를 뺀다
            html = re.sub(r'<div class="kicker">\d\d · ', '<div class="kicker">', html)
        html = html.replace("</body>", "<script>if(navigator.webdriver)document.querySelectorAll('.theme-pick,.keyhint').forEach(e=>e.style.display='none')</script>\n</body>", 1)
        left = re.findall(r"\{\{[^}]+\}\}", html)
        if left:
            raise SystemExit(f"{name}: 남은 자리 표시 {left[:5]}")
        out = name.replace(".html", f"{ver}.html")
        (HERE / out).write_text(html, encoding="utf-8")
        print(out, len(chosen) + 2, "장")


if __name__ == "__main__":
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else "")
