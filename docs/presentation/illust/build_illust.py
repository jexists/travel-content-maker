"""실행 방법 장의 설명 그림 — SVG로 그리고 render.sh로 PNG.

python3 docs/presentation/illust/build_illust.py   (실제 캡처 표시는 mark_captures.py)

사용자 PC 화면(Finder·탐색기·설치 창·Claude 앱)은 캡처할 수 없어 단순한 '예시 그림'으로 그린다.
실제 화면처럼 꾸미지 않고 상자·선·번호 동그라미만 쓴다. 색·글꼴은 흐름도(docs/diagrams)와 같다.
"""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent
FONT = "Pretendard, Apple SD Gothic Neo, sans-serif"
MONO = "JetBrains Mono, Menlo, monospace"
INK, MUTED, LINE, SOFT = "#1F2421", "#5C625E", "#C9CDC9", "#F4F6F5"
TEAL, TEAL_C, ORANGE, ORANGE_C = "#0F6E56", "#E3F2EC", "#D85A30", "#FCEEE8"


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.p = w, h, []

    def rect(self, x, y, w, h, fill="#fff", stroke=LINE, sw=2, r=12, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size=22, fill=INK, weight=500, anchor="start", mono=False):
        f = MONO if mono else FONT
        self.p.append(f'<text x="{x}" y="{y}" font-family="{f}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" dominant-baseline="middle">{escape(s)}</text>')

    def line(self, x1, y1, x2, y2, stroke=LINE, sw=2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.p.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def arrow(self, x1, y1, x2, y2, color=TEAL, sw=4, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.p.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}" marker-end="url(#ah)"{d}/>')

    def curve(self, d, color=ORANGE, sw=4, dash="10 8"):
        self.p.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-dasharray="{dash}" marker-end="url(#aho)"/>')

    def num(self, cx, cy, n, r=22, color=ORANGE):
        self.p.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>')
        self.text(cx, cy + 1, str(n), size=int(r * 1.15), fill="#fff", weight=800, anchor="middle")

    def ring(self, x, y, w, h, color=ORANGE):
        self.p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" fill="none" stroke="{color}" stroke-width="4.5"/>')

    def window(self, x, y, w, h, title="", tint=SOFT):
        self.rect(x, y, w, h, fill="#fff", stroke="#9AA09C", sw=2, r=14)
        self.p.append(f'<path d="M{x} {y + 14} a14 14 0 0 1 14 -14 h{w - 28} a14 14 0 0 1 14 14 v30 h{-w} z" fill="{tint}"/>')
        self.line(x, y + 44, x + w, y + 44, stroke="#D5D9D6")
        for i, c in enumerate(("#E6E8E7", "#E6E8E7", "#E6E8E7")):
            self.p.append(f'<circle cx="{x + 24 + i * 22}" cy="{y + 22}" r="7" fill="{c}" stroke="#C3C8C5"/>')
        if title:
            self.text(x + w / 2, y + 23, title, size=18, fill=MUTED, weight=600, anchor="middle")

    def folder(self, x, y, label, w=96, color="#7FB7A4", sub=None):
        h = w * 0.72
        self.p.append(f'<path d="M{x} {y + 10} q0 -10 10 -10 h{w * .3} l10 10 h{w * .7 - 20} q10 0 10 10 v{h - 10} q0 10 -10 10 h{-w + 10} q-10 0 -10 -10 z" fill="{color}"/>')
        self.text(x + w / 2, y + h + 26, label, size=19, weight=700, anchor="middle")
        if sub:
            self.text(x + w / 2, y + h + 50, sub, size=16, fill=MUTED, anchor="middle")

    def zipf(self, x, y, label, w=74):
        h = w * 1.25
        self.p.append(f'<path d="M{x} {y} h{w * .7} l{w * .3} {w * .3} v{h - w * .3} h{-w} z" fill="#fff" stroke="#9AA09C" stroke-width="2"/>')
        for i in range(5):
            self.rect(x + w * .42, y + 8 + i * 12, w * .16, 7, fill="#9AA09C", stroke="none", r=1)
        self.rect(x + w * .14, y + h - 30, w * .72, 20, fill=TEAL, stroke="none", r=4)
        self.text(x + w / 2, y + h - 19, "ZIP", size=13, fill="#fff", weight=800, anchor="middle")
        self.text(x + w / 2, y + h + 24, label, size=17, weight=600, anchor="middle")

    def label(self, x, y, s):  # 예시 그림 표시
        self.text(x, y, s, size=16, fill="#8A8F8B", weight=500, anchor="end")

    def save(self, name):
        defs = (f'<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{TEAL}"/></marker>'
                f'<marker id="aho" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{ORANGE}"/></marker></defs>')
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
               f'<rect width="100%" height="100%" fill="#fff"/>{defs}' + "".join(self.p) + "</svg>")
        (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")
        print(f"{name}.svg {self.w}x{self.h}")


def win_python():
    """Windows Python 설치 첫 화면 — Add python.exe to PATH 체크."""
    s = Svg(760, 520)
    s.window(20, 20, 720, 470, "Python 설치 프로그램 (Windows)")
    s.text(60, 110, "Install Python 3.x", size=30, weight=800)
    s.text(60, 150, "설치 방법을 고르세요", size=19, fill=MUTED)
    s.rect(60, 180, 520, 70, fill=TEAL_C, stroke=TEAL, r=10)
    s.text(84, 215, "→  Install Now", size=24, weight=700, fill=TEAL)
    s.rect(60, 266, 520, 54, fill="#fff", stroke=LINE, r=10)
    s.text(84, 293, "→  Customize installation", size=20, fill=MUTED)
    s.rect(60, 360, 24, 24, fill="#fff", stroke="#9AA09C", r=4)
    s.text(98, 372, "Use admin privileges when installing py.exe", size=18, fill=MUTED)
    s.rect(60, 410, 24, 24, fill=TEAL, stroke=TEAL, r=4)
    s.p.append('<path d="M65 422 l6 6 l11 -12" fill="none" stroke="#fff" stroke-width="3.5"/>')
    s.text(98, 422, "Add python.exe to PATH", size=22, weight=800)
    s.ring(46, 398, 360, 48)
    s.num(440, 422, 3)
    s.text(474, 422, "먼저 체크", size=22, weight=800, fill=ORANGE)
    s.num(620, 215, 4)
    s.text(650, 215, "설치", size=22, weight=800, fill=ORANGE)
    s.label(740, 508, "예시 그림 · 실제 설치 창 문구 기준, 모양은 단순화")
    s.save("win_python_path")


def put_skill():
    """zip 풀기 → skills 폴더 열기 → travel-content 넣기 (Mac / Windows 두 줄)."""
    s = Svg(1760, 780)
    cols = [(150, 470), (660, 560), (1260, 480)]  # 칸 x, 너비
    heads = ["zip 풀기", "skills 폴더 열기", "travel-content 넣기"]
    for i, (x, w) in enumerate(cols):
        s.num(x + 22, 34, i + 1, r=22)
        s.text(x + 56, 35, heads[i], size=26, weight=800)
    for row, (os_name, y) in enumerate((("Mac", 80), ("Windows", 430))):
        s.rect(10, y, 120, 320, fill=SOFT, stroke="none", r=12)
        s.text(70, y + 160, os_name, size=26, weight=800, anchor="middle")
        # ① zip
        x, w = cols[0]
        s.rect(x, y, w, 320, fill="#fff", stroke=LINE)
        s.zipf(x + 50, y + 70, "travel-content-skill.zip")
        s.arrow(x + 200, y + 120, x + 290, y + 120)
        s.folder(x + 320, y + 80, "travel-content")
        if row == 0:
            s.text(x + 245, y + 255, "zip 더블클릭 → 폴더가 생김", size=20, weight=600, anchor="middle")
        else:
            s.rect(x + 40, y + 225, 210, 40, fill="#fff", stroke="#9AA09C", r=6)
            s.text(x + 56, y + 245, "모두 압축 풀기…", size=18, weight=700)
            s.ring(x + 34, y + 221, 222, 48)
            s.text(x + 245, y + 292, "zip 오른쪽 클릭 → 모두 압축 풀기", size=19, weight=600, anchor="middle")
        s.arrow(x + w + 6, y + 160, cols[1][0] - 8, y + 160)
        # ② skills 폴더 열기
        x, w = cols[1]
        s.rect(x, y, w, 320, fill="#fff", stroke=LINE)
        if row == 0:
            s.rect(x + 24, y + 24, w - 48, 40, fill=SOFT, stroke="none", r=6)
            for k, m in enumerate(["Finder", "파일", "편집", "보기", "이동", "윈도우"]):
                s.text(x + 44 + k * 78, y + 44, m, size=18, weight=800 if m in ("Finder", "이동") else 500)
            s.ring(x + 340, y + 26, 64, 36)
            s.rect(x + 330, y + 66, 200, 44, fill="#fff", stroke="#9AA09C", r=6)
            s.text(x + 344, y + 88, "폴더로 이동…  ⇧⌘G", size=17, weight=700)
            s.rect(x + 40, y + 140, w - 80, 120, fill="#fff", stroke="#9AA09C", r=10)
            s.text(x + 60, y + 166, "폴더로 이동", size=17, fill=MUTED, weight=600)
            s.rect(x + 60, y + 186, w - 120, 50, fill="#fff", stroke=TEAL, sw=2.5, r=8)
            s.text(x + 78, y + 211, "~/.claude/skills", size=24, weight=700, mono=True, fill=TEAL)
            s.text(x + w / 2, y + 292, "Finder 이동 메뉴 → 폴더로 이동 → 경로 입력 → Enter", size=18, weight=600, anchor="middle")
        else:
            s.window(x + 24, y + 22, w - 48, 200, "파일 탐색기")
            s.rect(x + 44, y + 80, w - 88, 50, fill="#fff", stroke=TEAL, sw=2.5, r=8)
            s.text(x + 60, y + 105, "%USERPROFILE%\\.claude\\skills", size=22, weight=700, mono=True, fill=TEAL)
            s.text(x + 60, y + 165, "주소창을 클릭하고 경로 입력 → Enter", size=19, weight=600)
            s.text(x + w / 2, y + 268, "= C:\\Users\\내 이름\\.claude\\skills", size=19, fill=MUTED, anchor="middle", mono=True)
        s.arrow(x + w + 6, y + 160, cols[2][0] - 8, y + 160)
        # ③ 넣기
        x, w = cols[2]
        s.rect(x, y, w, 320, fill="#fff", stroke=LINE)
        s.window(x + 220, y + 24, 236, 220, "skills", tint=TEAL_C)
        s.folder(x + 290, y + 90, "travel-content", w=96)
        s.folder(x + 40, y + 90, "travel-content", w=96, color="#B9D8CC")
        s.curve(f"M{x + 140} {y + 120} C {x + 190} {y + 60}, {x + 250} {y + 70}, {x + 284} {y + 112}")
        s.text(x + 88, y + 220, "끌어다 놓기", size=18, fill=ORANGE, weight=800, anchor="middle")
        s.text(x + w / 2, y + 290, "skills 폴더가 없으면 새 폴더로 만들기", size=18, fill=MUTED, anchor="middle")
    s.label(1750, 770, "예시 그림 · 메뉴 이름과 경로는 실제와 같고 창 모양은 단순화")
    s.save("put_skill")


def use_claude():
    """Claude 앱 Code 탭 → 사진 폴더 선택 → 한 문장 요청."""
    s = Svg(1760, 640)
    s.window(20, 20, 1720, 580, "Claude 데스크톱 앱")
    s.rect(22, 66, 240, 532, fill=SOFT, stroke="none", r=0)
    for k, t in enumerate(["Chat", "Code"]):
        y = 110 + k * 64
        if t == "Code":
            s.rect(40, y - 26, 200, 52, fill=TEAL_C, stroke=TEAL, r=10)
        s.text(70, y, t, size=24, weight=800 if t == "Code" else 500, fill=TEAL if t == "Code" else MUTED)
    s.ring(32, 148, 216, 60)
    s.num(286, 174, 1)
    s.text(316, 174, "Code 탭", size=24, weight=800, fill=ORANGE)
    # 폴더 선택
    s.rect(490, 150, 520, 60, fill="#fff", stroke="#9AA09C", r=10)
    s.folder(510, 162, "", w=46)
    s.text(574, 180, "가우도 사진 (사진이 있는 폴더)", size=22, weight=700)
    s.ring(480, 142, 540, 76)
    s.num(1056, 180, 2)
    s.text(1086, 180, "작업 폴더 = 사진 폴더 선택", size=24, weight=800, fill=ORANGE)
    # 대화 미리보기
    s.rect(420, 260, 1260, 150, fill=SOFT, stroke="none", r=12)
    s.text(450, 300, "Claude", size=19, weight=800, fill=TEAL)
    s.text(450, 340, "사진 7장 확인 · 찾은 정보 정리 → A 확인: 사진 순서 · 표지 문구 · 캡션", size=21, fill=MUTED)
    s.text(450, 378, "(이후 B 대본 · C 블로그 · D 대표 승인 · E 링크 순서로 물어봄)", size=19, fill="#8A8F8B")
    # 입력창
    s.rect(420, 450, 1260, 100, fill="#fff", stroke=TEAL, sw=3, r=16)
    s.text(450, 500, "이 사진으로 여행 콘텐츠 만들어줘. 장소는 가우도", size=28, weight=800)
    s.p.append(f'<circle cx="1630" cy="500" r="26" fill="{TEAL}"/>')
    s.p.append('<path d="M1630 512 v-22 M1620 499 l10 -10 l10 10" fill="none" stroke="#fff" stroke-width="4"/>')
    s.num(1100, 450, 3)
    s.text(1130, 432, "한 문장 입력 → 보내기", size=24, weight=800, fill=ORANGE)
    s.label(1730, 625, "예시 그림 · 앱 화면을 단순화한 그림 (실제 배치와 다를 수 있음)")
    s.save("use_claude")


if __name__ == "__main__":
    win_python()
    put_skill()
    use_claude()
