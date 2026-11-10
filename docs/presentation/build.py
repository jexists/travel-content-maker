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
V4_CSS = """
/* v4: 흐름도 그림만 · Python 안내 · 터미널 · 효과/한계 카드 */
img.map { display: block; max-width: 100%; max-height: 800px; width: auto; height: auto; margin: 0 auto; }
.pyq { background: var(--card); border: 1.5px solid var(--line); border-top: 6px solid var(--accent); border-radius: 16px; padding: 34px 36px; gap: 14px; }
.pyq .q { font: 700 22px var(--font-mono); color: var(--accent); }
.pyq .a { font-size: 38px; font-weight: 800; line-height: 1.25; }
.pyq .s { font-size: 24px; color: var(--muted); }
.pyq .ways { display: flex; flex-wrap: wrap; gap: 10px; margin: 8px 0; }
.pyq .ways .chip b { background: var(--accent); color: var(--on-accent); }
.pyq .me { font-size: 25px; }
.pyq .opt { font-size: 19px; color: var(--subtle); border-top: 1px solid var(--line); padding-top: 14px; margin-top: 6px; line-height: 1.5; }
.term { background: #111418; border-radius: 16px; overflow: hidden; box-shadow: 0 18px 40px rgba(0,0,0,.18); }
.term .bar { display: flex; align-items: center; gap: 9px; padding: 14px 18px; background: #1d2228; }
.term .bar i { width: 14px; height: 14px; border-radius: 50%; background: #ff5f57; display: block; }
.term .bar i:nth-child(2) { background: #febc2e; } .term .bar i:nth-child(3) { background: #28c840; }
.term .bar span { margin-left: 14px; font: 600 17px var(--font-mono); color: #8b949e; }
.term pre { margin: 0; padding: 26px 30px 30px; font: 500 22px/1.6 var(--font-mono); color: #e6edf3; white-space: pre; }
.term .pr { color: #3cc39a; font-weight: 700; } .term .cm { color: #fff; font-weight: 700; }
.term .hd { color: #79c0ff; font-weight: 700; } .term .dim { color: #8b949e; }
.term .tip { color: #e3b341; } .term .done { color: #3cc39a; font-weight: 800; }
.fixes { gap: 12px; }
.fixes .fh { font-size: 28px; font-weight: 800; margin-bottom: 6px; }
.fixes .fx { display: grid; grid-template-columns: 250px 52px 1fr; align-items: center; background: var(--card); border: 1.5px solid var(--line); border-radius: 12px; padding: 16px 20px; }
.fixes .fx .p { font-size: 22px; font-weight: 700; color: var(--warn); }
.fixes .fx .ar svg { width: 34px; height: 20px; } .fixes .fx .ar path { fill: var(--subtle); }
.fixes .fx .s { font-size: 22px; }
.fixes .fx.me { border-style: dashed; } .fixes .fx.me .p { color: var(--ink); }
.eff { display: grid; grid-template-columns: 1fr 1fr; gap: 44px; }
.eff .colh { font-size: 30px; font-weight: 800; display: flex; align-items: center; gap: 14px; margin-bottom: 18px; }
.eff .it { display: flex; align-items: center; gap: 20px; background: var(--card); border: 1.5px solid var(--line); border-radius: 14px; padding: 18px 24px; margin-bottom: 12px; }
.eff .ic { width: 46px; height: 46px; flex: none; border-radius: 50%; display: grid; place-items: center; color: #fff; font-size: 24px; font-weight: 900; }
.eff .ic.ok { background: var(--ok); } .eff .ic.wn { background: var(--warn); }
.eff .it .w { font-size: 26px; font-weight: 800; }
.eff .it .h { font-size: 20px; color: var(--muted); margin-top: 3px; }
.eff .it .tag { margin-left: auto; font: 700 19px var(--font-mono); color: var(--accent); }
"""
V5_CSS = """
/* v5: 목소리 키 안내 · 한계 메모 · 확장 3단계 */
.keynote { display: flex; align-items: center; gap: 16px; font-size: 23px; color: var(--muted); }
.later { font-size: 22px; color: var(--muted); border: 2px dashed var(--line); border-radius: 12px; padding: 14px 22px; text-align: center; }
.flow.grow .st { padding: 40px 36px; min-height: 380px; }
.flow.grow .st .nm { font-size: 24px; }
.flow.grow .st .big { font-size: 46px; margin-top: 18px; }
.flow.grow .st .ex { font-size: 25px; margin-top: 22px; line-height: 1.55; }
"""
VARIANTS = {
    "index.html": dict(parts=None, kicker="AX Campus 1기 · 4회차 개인 과제",
                       title="여행 콘텐츠 3채널 자동화", h1="여행 콘텐츠<br>3채널 자동화", sub="사진 폴더 하나로 인스타 카드뉴스 · 유튜브 숏폼 · 티스토리 블로그"),
    "analysis.html": dict(parts={"intro", "asis", "tobe", "impl", "end", "thanks"}, kicker="제출물 ①·② · 현재 업무 분석과 개선 설계",
                          title="여행 콘텐츠 3채널 자동화", h1="여행 콘텐츠<br>3채널 자동화", sub="As-Is 분석 · To-Be 설계 · 구현 결과"),
    "run.html": dict(parts={"run", "thanks"}, kicker="제출물 ③ · 실행 방법",
                     title="travel-content 실행 방법", h1="travel-content<br>실행 방법", sub="설치부터 결과 확인까지 8단계"),
}
WHO = "정주애 · 2026.11.11"
V3_CSS = """
/* v3: 카드 · 비교 행 · 5칸 흐름 · 완료 카드 */
.toc-grid { grid-template-columns: repeat(3, 1fr); gap: 0 64px; }
.cards3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.card { background: var(--card); border: 1.5px solid var(--line); border-radius: 16px; padding: 28px 32px; border-top: 6px solid var(--accent); }
.card .lb { font: 700 19px var(--font-mono); color: var(--accent); }
.card .v { font-size: 30px; font-weight: 800; margin-top: 10px; line-height: 1.3; }
.card .s { font-size: 21px; color: var(--muted); margin-top: 10px; line-height: 1.5; }
.pick { display: flex; align-items: center; gap: 24px; background: var(--accent-c); border: 2px solid var(--accent); border-radius: 16px; padding: 22px 30px; }
.pick .t1 { font-size: 30px; font-weight: 800; white-space: nowrap; }
.pick .why { display: flex; gap: 12px; flex-wrap: wrap; margin-left: auto; }
.pick .chip b { background: var(--accent); color: var(--on-accent); }
.cmp { gap: 14px; }
.cmp .hd, .cmp .rw { display: grid; grid-template-columns: 130px 1fr 72px 1.2fr; align-items: stretch; }
.cmp .hd { font-size: 26px; font-weight: 800; padding: 0 0 4px; }
.cmp .hd > div { display: flex; align-items: center; gap: 12px; padding-left: 26px; }
.cmp .rw { border: 1.5px solid var(--line); border-radius: 14px; background: var(--card); overflow: hidden; min-height: 104px; }
.cmp .p { font: 800 24px var(--font-mono); color: var(--warn); display: grid; place-items: center; background: var(--card2); border-right: 1.5px solid var(--line); }
.cmp .a { padding: 0 26px; font-size: 25px; color: var(--muted); display: flex; align-items: center; }
.cmp .ar { display: grid; place-items: center; }
.cmp .ar svg { width: 40px; height: 22px; } .cmp .ar path { fill: var(--accent); }
.cmp .b { padding: 14px 26px; background: var(--accent-c); display: flex; flex-direction: column; justify-content: center; }
.cmp .b .w { font-size: 27px; font-weight: 800; color: var(--accent-ink); }
.cmp .b .f { font: 600 18px var(--font-mono); color: var(--muted); margin-top: 6px; }
.pipe .st { display: flex; flex-direction: column; gap: 12px; padding: 26px 22px; }
.pipe .no { width: 48px; height: 48px; border-radius: 50%; background: var(--ink); color: var(--bg); font: 800 24px var(--font-mono); display: grid; place-items: center; }
.pipe .st.hot .no { background: var(--accent); color: var(--on-accent); }
.pipe .nm2 { font-size: 34px; font-weight: 800; }
.pipe .d { font-size: 22px; line-height: 1.45; flex: 1; }
.pipe .eg { font: 600 17px/1.5 var(--font-mono); color: var(--muted); background: var(--card2); border-radius: 8px; padding: 10px 12px; }
.pipe .who { font-size: 19px; font-weight: 700; color: var(--accent); }
.pipe .ar { width: 48px; }
.loopnote { display: flex; align-items: center; gap: 16px; font-size: 23px; color: var(--muted); border: 2px dashed var(--warn); border-radius: 12px; padding: 14px 22px; }
.done { display: grid; grid-template-columns: 1fr 1fr; gap: 28px; }
.done .dn { display: flex; gap: 22px; background: var(--card); border: 1.5px solid var(--line); border-radius: 16px; padding: 40px 38px; min-height: 250px; }
.done .ck { width: 60px; height: 60px; flex: none; border-radius: 50%; background: var(--ok); color: #fff; font-size: 30px; font-weight: 900; display: grid; place-items: center; }
.done .w { font-size: 34px; font-weight: 800; margin-bottom: 16px; }
.done .h { font-size: 24px; color: var(--muted); line-height: 1.6; }
.done .h code { font: 700 21px var(--font-mono); color: var(--accent-ink); }
"""


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
    tpl = tpl.replace("</style>", EXTRA_CSS + (V3_CSS if ver >= "_v3" else "") + (V4_CSS if ver >= "_v4" else "") + (V5_CSS if ver >= "_v5" else "") + "</style>", 1)
    ncol = 3 if ver >= "_v3" else 4  # v1·v2는 4열 그대로
    tpl = re.sub(r"<template id=\"opt-[^\"]+\">.*?</template>\s*", "", tpl, flags=re.S)  # 쓰지 않는 선택 조각 제거
    # 내용 장 자리 표시 1장을 지운다 (목차 장 다음 ~ </main>)
    toc_end = tpl.index("</section>", tpl.index('data-title="목차"')) + len("</section>")
    main_end = tpl.index("</main>")
    head, tail = tpl[:toc_end], tpl[main_end:]
    src = (HERE / f"slides{ver}.src.html").read_text(encoding="utf-8")
    slides = re.findall(r"<section class=\"slide[^\"]*\" data-part=\"(\w+)\".*?</section>", src, flags=re.S)
    blocks = re.findall(r"(<section class=\"slide[^\"]*\" data-part=\"\w+\".*?</section>)", src, flags=re.S)
    for name, v in VARIANTS.items():
        v = dict(v)
        if ver >= "_v2" and name == "run.html":
            v["sub"] = "스킬 zip 하나로 4단계 · Mac·Windows" if ver >= "_v5" else "스킬 zip 하나로 3단계 · Mac·Windows"
        chosen = [b for p, b in zip(slides, blocks) if v["parts"] is None or p in v["parts"]]
        html = head + "\n\n" + "\n\n".join(chosen) + "\n\n" + tail
        html = re.sub(r'(<div class="kicker r">\{\{행사·과목 이름\}\}</div>.*?<div class="who r">.*?</div>)',
                      r'<div class="ctext">\1</div>', html, count=1, flags=re.S)
        html = html.replace('<h1 class="r">{{발표 제목}}</h1>', f'<h1 class="r">{v.get("h1", v["title"])}</h1>', 1)
        html = (html.replace("{{발표 제목}}", v["title"]).replace("{{행사·과목 이름}}", v["kicker"])
                    .replace("{{한 줄 설명 — 명사형}}", v["sub"]).replace("{{발표자}} · {{YYYY.MM.DD}}", WHO))
        # 목차: 섹션을 순서대로 왼쪽 열부터 채운다 (원래 템플릿은 가장 가벼운 열에 넣어 순서가 섞였음)
        html = html.replace("const k = load.indexOf(Math.min(...load));  // 가장 가벼운 열에\n        cols[k].appendChild(g); load[k] += items.length + 1;",
                            "const size = items.length + 1; if (c < NCOL - 1 && load[c] > 0 && load[c] + size / 2 > per) c += 1;\n        cols[c].appendChild(g); load[c] += size;")
        html = html.replace("const cols = [0, 1, 2].map(", f"const cols = {list(range(ncol))}.map(")
        html = html.replace("const load = [0, 0, 0];", f"const load = {[0] * ncol}; let c = 0; const per = [...groups].reduce((a, [, it]) => a + it.length + 1, 0) / {ncol};")
        html = html.replace("NCOL - 1", str(ncol - 1))
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
