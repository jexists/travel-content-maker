"""As-Is / To-Be / 시스템 구성도를 Draw.io(.drawio)와 SVG로 함께 만든다.

python3.12 docs/diagrams/build_diagrams.py   (PNG는 render_png.sh 로 헤드리스 Chrome 캡처)

표기 규칙 (AX Campus 2회차 5-3 · 4회차 2-4):
  스윔레인 = 담당 · 동그라미 = 시작·종료 · 사각형 = 작업 · 마름모 = 판단
  문서 모양 = 자료 · 원통 = 보관
  청록 실선 = 정상 진행 · 주황 점선 = 재확인·되돌림 · 회색 점선 = 자료 연결
같은 좌표로 두 파일을 만들기 때문에 Draw.io에서 열어 고쳐도 배치가 그대로다.
"""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent
FONT = "Pretendard, Apple SD Gothic Neo, sans-serif"
INK, MUTED, LINE, HEAD = "#1F2421", "#5C625E", "#C9CDC9", "#EEF3F0"
TEAL, ORANGE, GRAY = "#0F6E56", "#D85A30", "#8A8F8B"
EDGE = {"normal": (TEAL, False), "loop": (ORANGE, True), "data": (GRAY, True)}
FILL = {  # fill, stroke
    "task": ("#FFFFFF", INK), "problem": ("#FCEEE8", ORANGE), "ai": ("#E3F2EC", TEAL),
    "sys": ("#FFFFFF", TEAL), "human": ("#FFFFFF", INK), "decision": ("#FFFFFF", TEAL),
    "data": ("#F6F7F6", GRAY), "ext": ("#FFFFFF", GRAY),
}
HEAD_W, LANE_H, COL_W, PAD = 112, 150, 118, 18
SIZE = {"task": (104, 74), "decision": (108, 92), "start": (34, 34), "end": (34, 34), "doc": (104, 62), "db": (104, 70)}
FS = 13.5


class Diagram:
    def __init__(self, name, lanes, ncols):
        self.name, self.lanes = name, lanes
        self.nodes, self.edges, self.badges = {}, [], []
        self.width = HEAD_W + PAD * 2 + ncols * COL_W
        self.height = len(lanes) * LANE_H

    def node(self, nid, lane, col, label, kind="task", style=None):
        w, h = SIZE[kind]
        cx = HEAD_W + PAD + col * COL_W + COL_W / 2
        cy = self.lanes.index(lane) * LANE_H + LANE_H / 2
        style = style or {"decision": "decision", "doc": "data", "db": "data"}.get(kind, "task")
        self.nodes[nid] = dict(x=cx - w / 2, y=cy - h / 2, w=w, h=h, cx=cx, cy=cy, label=label, kind=kind, style=style)

    def edge(self, a, b, label="", exit="right", entry="left", kind="normal", via=None):
        self.edges.append(dict(a=a, b=b, label=label, exit=exit, entry=entry, kind=kind, via=via))

    def badge(self, nid, text):
        self.badges.append((nid, text))

    def port(self, nid, spec):
        side, _, off = spec.partition(":")
        off = float(off or 0)
        n = self.nodes[nid]
        dia = n["kind"] == "decision"
        if side in ("top", "bottom"):
            x = n["cx"] + off
            inset = abs(off) * n["h"] / n["w"] if dia else 0
            return x, (n["y"] + inset if side == "top" else n["y"] + n["h"] - inset)
        y = n["cy"] + off
        inset = abs(off) * n["w"] / n["h"] if dia else 0
        return (n["x"] + inset if side == "left" else n["x"] + n["w"] - inset), y

    def rel(self, nid, spec):
        x, y = self.port(nid, spec)
        n = self.nodes[nid]
        return (x - n["x"]) / n["w"], (y - n["y"]) / n["h"]

    def route(self, e):
        (x1, y1), (x2, y2) = self.port(e["a"], e["exit"]), self.port(e["b"], e["entry"])
        hx = e["exit"].split(":")[0] in ("left", "right")
        hy = e["entry"].split(":")[0] in ("left", "right")
        if hx and hy:
            pts = [] if abs(y1 - y2) < 1 else [((e["via"] if e["via"] is not None else (x1 + x2) / 2), y1),
                                                ((e["via"] if e["via"] is not None else (x1 + x2) / 2), y2)]
        elif not hx and not hy:
            pts = [] if abs(x1 - x2) < 1 else [(x1, e["via"] if e["via"] is not None else (y1 + y2) / 2),
                                                (x2, e["via"] if e["via"] is not None else (y1 + y2) / 2)]
        elif hx:
            pts = [(x2, y1)]
        else:
            pts = [(x1, y2)]
        return [(x1, y1)] + pts + [(x2, y2)]

    # ---------------- drawio ----------------
    def drawio(self):
        cells, ids, c = [], {}, [2]

        def nid():
            c[0] += 1
            return f"c{c[0]}"
        for i, lane in enumerate(self.lanes):
            y = i * LANE_H
            cells.append(f'<mxCell id="{nid()}" value="" style="rounded=0;fillColor=none;strokeColor={LINE};" vertex="1" parent="1"><mxGeometry x="0" y="{y}" width="{self.width}" height="{LANE_H}" as="geometry"/></mxCell>')
            cells.append(f'<mxCell id="{nid()}" value="{escape(lane).replace(chr(10), "&lt;br&gt;")}" style="rounded=0;html=1;fillColor={HEAD};strokeColor={LINE};fontStyle=1;fontSize=14;whiteSpace=wrap;fontFamily={FONT};" vertex="1" parent="1"><mxGeometry x="0" y="{y}" width="{HEAD_W}" height="{LANE_H}" as="geometry"/></mxCell>')
        for k, n in self.nodes.items():
            fill, stroke = FILL[n["style"]]
            shape = {"task": "rounded=1;arcSize=10;", "decision": "rhombus;", "start": "ellipse;", "end": "ellipse;strokeWidth=3;",
                     "doc": "shape=document;boundedLbl=1;", "db": "shape=cylinder3;boundedLbl=1;size=10;"}[n["kind"]]
            ids[k] = nid()
            val = escape(n["label"]).replace("\n", "&lt;br&gt;") if n["kind"] not in ("start", "end") else ""
            cells.append(f'<mxCell id="{ids[k]}" value="{val}" style="{shape}whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontSize={FS};fontFamily={FONT};" vertex="1" parent="1"><mxGeometry x="{n["x"]:.0f}" y="{n["y"]:.0f}" width="{n["w"]}" height="{n["h"]}" as="geometry"/></mxCell>')
        for e in self.edges:
            color, dashed = EDGE[e["kind"]]
            wp = "".join(f'<mxPoint x="{x:.0f}" y="{y:.0f}"/>' for x, y in self.route(e)[1:-1])
            ex, ey = self.rel(e["a"], e["exit"])
            nx, ny = self.rel(e["b"], e["entry"])
            st = (f'edgeStyle=none;html=1;endArrow=block;endFill=1;endSize=5;strokeWidth=2;strokeColor={color};fontSize=12;fontStyle=1;fontColor={color};fontFamily={FONT};'
                  f'{"dashed=1;" if dashed else ""}labelBackgroundColor=#FFFFFF;exitX={ex:.3f};exitY={ey:.3f};exitDx=0;exitDy=0;entryX={nx:.3f};entryY={ny:.3f};entryDx=0;entryDy=0;')
            cells.append(f'<mxCell id="{nid()}" value="{escape(e["label"])}" style="{st}" edge="1" parent="1" source="{ids[e["a"]]}" target="{ids[e["b"]]}"><mxGeometry relative="1" as="geometry">' + (f'<Array as="points">{wp}</Array>' if wp else "") + '</mxGeometry></mxCell>')
        for k, text in self.badges:
            n = self.nodes[k]
            cells.append(f'<mxCell id="{nid()}" value="{text}" style="rounded=1;arcSize=50;fillColor={ORANGE};strokeColor=none;fontColor=#FFFFFF;fontSize=11;fontStyle=1;fontFamily={FONT};" vertex="1" parent="1"><mxGeometry x="{n["x"] + n["w"] - 20:.0f}" y="{n["y"] - 10:.0f}" width="28" height="19" as="geometry"/></mxCell>')
        body = "".join(cells)
        (OUT / f"{self.name}.drawio").write_text(
            f'<mxfile host="build_diagrams.py"><diagram name="{self.name}" id="{self.name}"><mxGraphModel dx="1200" dy="800" grid="0" gridSize="10" guides="1" page="0" math="0" shadow="0">'
            f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>{body}</root></mxGraphModel></diagram></mxfile>', encoding="utf-8")

    # ---------------- svg ----------------
    def svg(self):
        W, H = self.width, self.height + 56
        o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
             "<defs>" + "".join(f'<marker id="m{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto"><path d="M0 0L10 5L0 10z" fill="{c}"/></marker>' for k, (c, _) in EDGE.items()) + "</defs>",
             f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
        for i, lane in enumerate(self.lanes):
            y = i * LANE_H
            o.append(f'<rect x="0.5" y="{y + 0.5}" width="{W - 1}" height="{LANE_H}" fill="none" stroke="{LINE}"/>')
            o.append(f'<rect x="0.5" y="{y + 0.5}" width="{HEAD_W}" height="{LANE_H}" fill="{HEAD}" stroke="{LINE}"/>')
            o.append(_text(HEAD_W / 2, y + LANE_H / 2, lane, 14.5, INK, True))
        for e in self.edges:
            color, dashed = EDGE[e["kind"]]
            pts = self.route(e)
            d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
            o.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.2"{" stroke-dasharray=\"7 5\"" if dashed else ""} marker-end="url(#m{e["kind"]})"/>')
        labels = []
        for e in self.edges:  # 라벨은 선을 다 그린 뒤 가장 긴 구간 가운데에 알약으로
            if not e["label"]:
                continue
            pts = self.route(e)
            segs = list(zip(pts, pts[1:]))
            (ax, ay), (bx, by) = max(segs, key=lambda s: abs(s[0][0] - s[1][0]) + abs(s[0][1] - s[1][1]))
            lx, ly = (ax + bx) / 2, (ay + by) / 2
            tw = len(e["label"]) * 12.5 + 14
            color = EDGE[e["kind"]][0]
            labels.append(f'<rect x="{lx - tw / 2:.1f}" y="{ly - 11:.1f}" width="{tw:.1f}" height="22" rx="11" fill="#FFFFFF" stroke="{color}" stroke-width="1"/>')
            labels.append(_text(lx, ly, e["label"], 12, color, True))
        for n in self.nodes.values():
            fill, stroke = FILL[n["style"]]
            x, y, w, h, cx, cy = n["x"], n["y"], n["w"], n["h"], n["cx"], n["cy"]
            k = n["kind"]
            if k == "task":
                o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="9" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
            elif k == "decision":
                o.append(f'<polygon points="{cx},{y} {x + w},{cy} {cx},{y + h} {x},{cy}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
            elif k == "doc":
                o.append(f'<path d="M{x} {y} H{x + w} V{y + h - 9} Q{x + w * .75} {y + h - 18} {x + w / 2} {y + h - 9} T{x} {y + h - 9} Z" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
            elif k == "db":
                ry = 9
                o.append(f'<path d="M{x} {y + ry} V{y + h - ry} A{w / 2} {ry} 0 0 0 {x + w} {y + h - ry} V{y + ry}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
                o.append(f'<ellipse cx="{cx}" cy="{y + ry}" rx="{w / 2}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
            else:
                o.append(f'<circle cx="{cx}" cy="{cy}" r="{w / 2}" fill="#FFFFFF" stroke="{INK}" stroke-width="{3 if k == "end" else 1.6}"/>')
            if k in ("start", "end"):
                o.append(_text(cx, y + h + 14, n["label"], 12.5, MUTED))
            else:
                ty = cy + (7 if k == "db" else -4 if k == "doc" else 0)
                o.append(_text(cx, ty, n["label"], FS if k != "decision" else 13, INK, k == "decision"))
        for k, text in self.badges:
            n = self.nodes[k]
            bx, by = n["x"] + n["w"] - 20, n["y"] - 10
            o.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="28" height="19" rx="9.5" fill="{ORANGE}"/>')
            o.append(_text(bx + 14, by + 9.5, text, 11, "#FFFFFF", True))
        o += labels
        # 범례: 표기 규칙
        ly, x = self.height + 30, 16
        items = [("circle", "시작·종료"), ("rect", "작업"), ("dia", "판단"), ("doc", "자료"), ("db", "보관"),
                 ("normal", "정상 진행"), ("loop", "재확인·되돌림"), ("data", "자료 연결")]
        for kind, text in items:
            if kind == "circle":
                o.append(f'<circle cx="{x + 9}" cy="{ly}" r="8" fill="#fff" stroke="{INK}" stroke-width="1.5"/>')
            elif kind == "rect":
                o.append(f'<rect x="{x}" y="{ly - 8}" width="22" height="16" rx="3" fill="#fff" stroke="{INK}" stroke-width="1.5"/>')
            elif kind == "dia":
                o.append(f'<polygon points="{x + 11},{ly - 10} {x + 22},{ly} {x + 11},{ly + 10} {x},{ly}" fill="#fff" stroke="{TEAL}" stroke-width="1.5"/>')
            elif kind == "doc":
                o.append(f'<path d="M{x} {ly - 8} H{x + 22} V{ly + 5} Q{x + 16} {ly + 1} {x + 11} {ly + 5} T{x} {ly + 5} Z" fill="#F6F7F6" stroke="{GRAY}" stroke-width="1.4"/>')
            elif kind == "db":
                o.append(f'<path d="M{x} {ly - 6} V{ly + 6} A11 4 0 0 0 {x + 22} {ly + 6} V{ly - 6}" fill="#F6F7F6" stroke="{GRAY}" stroke-width="1.4"/><ellipse cx="{x + 11}" cy="{ly - 6}" rx="11" ry="4" fill="#F6F7F6" stroke="{GRAY}" stroke-width="1.4"/>')
            else:
                color, dashed = EDGE[kind]
                o.append(f'<path d="M{x} {ly} H{x + 30}" stroke="{color}" stroke-width="2.2"{" stroke-dasharray=\"7 5\"" if dashed else ""} marker-end="url(#m{kind})"/>')
            off = 38 if kind in EDGE else 30
            o.append(f'<text x="{x + off}" y="{ly + 5}" font-size="13" fill="{MUTED}">{escape(text)}</text>')
            x += off + len(text) * 13 + 26
        o.append("</svg>")
        (OUT / f"{self.name}.svg").write_text("\n".join(o), encoding="utf-8")

    def build(self):
        self.drawio()
        self.svg()


def _text(x, y, label, size, color, bold=False):
    lines = label.split("\n")
    lh = size * 1.3
    y0 = y - lh * (len(lines) - 1) / 2
    spans = "".join(f'<tspan x="{x:.1f}" y="{y0 + i * lh:.1f}">{escape(t)}</tspan>' for i, t in enumerate(lines))
    return f'<text text-anchor="middle" dominant-baseline="central" font-size="{size}" fill="{color}"{" font-weight=\"700\"" if bold else ""}>{spans}</text>'


# ================= As-Is (F 실제 · V 가상 팀) =================
CEO, MGR, ED, DAT = "대표\n(V 가상)", "매니저\n(V 가상)", "에디터\n(본인)", "자료·보관"
a = Diagram("asis", [CEO, MGR, ED, DAT], 12)
a.node("start", ED, 0, "여행 다녀옴", "start")
a.node("A01", ED, 1, "A01\n사진 고르기\nF", style="problem")
a.node("A02", ED, 2, "A02\n장소 정보 찾기\nF", style="problem")
a.node("A03", ED, 3, "A03 인스타\n카드·캡션\n수작업 F", style="problem")
a.node("A04", MGR, 4, "A04\n인스타 검토\nV", "decision")
a.node("A06", ED, 5, "A06 숏폼\n직접 편집\nV · 아직 못 함", style="problem")
a.node("A07", MGR, 6, "A07\n유튜브 검토\nV", "decision")
a.node("A09", ED, 7, "A09 티스토리\n글 새로 쓰기\nF", style="problem")
a.node("A10", MGR, 8, "A10\n티스토리 검토\nV", "decision")
a.node("A12", CEO, 9, "A12\n최종 승인\nV", "decision")
a.node("A13", ED, 10, "A13\n3채널 게시\nF / V")
a.node("end", ED, 11, "게시 끝", "end")
a.node("D1", DAT, 1.5, "사진첩 ·\n지도·검색 메모", "doc")
a.node("D2", DAT, 4 + 30 / COL_W, "메신저 피드백\n(수정 요청)", "doc")
a.node("D3", DAT, 10, "A14 기록 없음\n메신저·폴더", "db", style="problem")
a.edge("start", "A01")
a.edge("A01", "A02")
a.edge("A02", "A03")
a.edge("A03", "A04", "검토 요청", exit="top", entry="left")
a.edge("A04", "A03", "A05 수정 · P5", exit="bottom", entry="right:-18", kind="loop")
a.edge("A04", "A06", "통과", exit="right", entry="top")
a.edge("A06", "A07", exit="top", entry="left")
a.edge("A07", "A06", "A08 수정 · P5", exit="bottom", entry="right:-18", kind="loop")
a.edge("A07", "A09", "통과", exit="right", entry="top")
a.edge("A09", "A10", exit="top", entry="left")
a.edge("A10", "A09", "A11 수정 · P5", exit="bottom", entry="right:-18", kind="loop")
a.edge("A10", "A12", "통과", exit="top", entry="left")
a.edge("A12", "A09", "반려", exit="left", entry="top:-30", kind="loop")
a.edge("A12", "A13", "승인", exit="right", entry="top")
a.edge("A13", "end")
a.edge("A01", "D1", exit="bottom", entry="top:-30", kind="data")
a.edge("A02", "D1", exit="bottom", entry="top:30", kind="data")
a.edge("A04", "D2", exit="bottom:30", entry="top", kind="data")
a.edge("A13", "D3", exit="bottom", entry="top", kind="data")
for k, b in [("A01", "P1"), ("A03", "P1"), ("A02", "P2"), ("A09", "P2"), ("A06", "P3"), ("A04", "P4"), ("A07", "P4"), ("A10", "P4"), ("D3", "P6")]:
    a.badge(k, b)
a.build()

# ================= To-Be (현재 코드 기준 · 확인 지점 A~E) =================
CEO2, ED2, AI2, SYS2, DAT2 = "대표\n(V 가상)", "에디터\n(본인)", "AI\nClaude 스킬", "시스템\ntc.py", "자료·보관"
t = Diagram("tobe", [CEO2, ED2, AI2, SYS2, DAT2], 14)
t.node("start", ED2, 0, "사진 폴더\n+ 장소", "start")
t.node("T01", SYS2, 1, "T01 사진 추리기\n20장 이하 전부\n번호 시트", style="sys")
t.node("T02", AI2, 2, "T02 정보 검색\n브리프·표지·\n순서·캡션 제안", style="ai")
t.node("A", ED2, 3, "A 확인\n브리프+인스타", "decision")
t.node("T03", SYS2, 4, "T03 카드 제작\n+ 규칙 점검", style="sys")
t.node("T04", AI2, 5, "T04 영상\n제목·대본", style="ai")
t.node("B", ED2, 6, "B 확인\n대본", "decision")
t.node("T05", SYS2, 7, "T05 숏폼 제작\nTTS·자막\n+ 점검", style="sys")
t.node("T06", AI2, 8, "T06 블로그\n제목 5개·글", style="ai")
t.node("T07", SYS2, 9, "T07 블로그\nHTML + 점검", style="sys")
t.node("C", ED2, 10, "C 확인\n블로그", "decision")
t.node("D", CEO2, 11, "D 최종 승인\n3채널 한 번에", "decision")
t.node("T08", ED2, 12, "T08 업로드\n공유·발행\nE 링크 입력", style="human")
t.node("T09", SYS2, 13, "T09 대장\n게시 완료", style="sys")
t.node("D1", DAT2, 2, "content.json\n브리프·문구", "doc")
t.node("D2", DAT2, 7, "best_*·채널/vN\n결과물", "db")
t.node("D3", DAT2, 13, "ledger.xlsx\n콘텐츠대장", "db")
t.edge("start", "T01", exit="right", entry="left")
t.edge("T01", "T02", exit="top", entry="left")
t.edge("T02", "A", exit="top", entry="left")
t.edge("A", "T02", "수정", exit="bottom", entry="right", kind="loop")
t.edge("A", "T03", "승인", exit="right", entry="top")
t.edge("T03", "T04", exit="right", entry="bottom")
t.edge("T04", "B", exit="top", entry="left")
t.edge("B", "T04", "수정", exit="bottom", entry="right", kind="loop")
t.edge("B", "T05", "승인", exit="right", entry="top")
t.edge("T05", "T06", exit="right", entry="bottom")
t.edge("T06", "T07", exit="right", entry="top")
t.edge("T07", "C", exit="top", entry="bottom")
t.edge("C", "T06", "수정", exit="left", entry="top", kind="loop")
t.edge("C", "D", "컨펌", exit="top", entry="left")
t.edge("D", "T06", "반려 → v2", exit="left", entry="top:-30", kind="loop", via=None)
t.edge("D", "T08", "승인", exit="right", entry="top")
t.edge("T08", "T09", exit="right", entry="top")
t.edge("T02", "D1", exit="bottom", entry="top", kind="data")
t.edge("T05", "D2", exit="bottom", entry="top", kind="data")
t.edge("T09", "D3", exit="bottom", entry="top", kind="data")
t.build()

# ================= 시스템 구성도 =================
H, AIL, SC, TOOL, ST = "사람", "Claude Code\n스킬", "스크립트\ntc.py", "외부 도구·API", "저장\n(로컬 PC)"
s = Diagram("architecture", [H, AIL, SC, TOOL, ST], 9)
s.node("u1", H, 0, "사진 폴더\n+ 장소", "doc")
s.node("u2", H, 4, "확인 지점\nA·B·C 답", "decision")
s.node("u3", H, 7.5, "D 대표 승인\nE 링크", "decision")
s.node("k1", AIL, 1, "SKILL.md\n흐름·멈춤 규칙", style="ai")
s.node("k2", AIL, 3, "prompts/\n채널별 작성 규칙", style="ai")
s.node("c1", SC, 1, "insta-pick·use\n사진·시트", style="sys")
s.node("c2", SC, 3, "render_cards\n인스타 카드", style="sys")
s.node("c3", SC, 4.5, "make_shorts\n숏폼", style="sys")
s.node("c4", SC, 6, "build_blog\n블로그", style="sys")
s.node("c5", SC, 7.5, "check_rules\nstate·ledger", style="sys")
s.node("x1", TOOL, 2, "Pillow\n이미지", style="ext")
s.node("x2", TOOL, 4.5, "ffmpeg ·\nOpenAI TTS", style="ext")
s.node("x3", TOOL, 6.6, "sips · Chrome\n(선택: 업로드)", style="ext")
s.node("s1", ST, 3, "settings·rules\n.json", "doc")
s.node("s2", ST, 6, "work/C-xxx/\n채널/vN", "db")
s.node("s3", ST, 7.5, "ledger.xlsx", "db")
s.edge("u1", "k1", exit="bottom", entry="top")
s.edge("k1", "c1", exit="bottom", entry="top")
s.edge("c1", "c2")
s.edge("c2", "c3")
s.edge("c3", "c4")
s.edge("c4", "c5")
s.edge("k2", "u2", exit="top", entry="left")
s.edge("u2", "c3", "승인", exit="bottom:30", entry="top:-29")
s.edge("u3", "c5", exit="bottom", entry="top")
s.edge("c2", "x1", exit="bottom:-30", entry="top", kind="data")
s.edge("c3", "x2", exit="bottom", entry="top", kind="data")
s.edge("c4", "x3", exit="bottom:40", entry="top:-30.8", kind="data")
s.edge("s1", "c2", exit="top", entry="bottom", kind="data")
s.edge("c4", "s2", exit="bottom", entry="top", kind="data")
s.edge("c5", "s3", exit="bottom", entry="top", kind="data")
s.build()
# ================= 시스템 구성도 v2 (Mac·Windows, 스킬 zip) =================
v = Diagram("architecture_v2", [H, AIL, SC, TOOL, ST], 9)
for k, n in s.nodes.items():
    v.nodes[k] = dict(n)
v.edges, v.badges = list(s.edges), list(s.badges)
v.nodes["u1"]["label"] = "스킬 zip 넣기\n+ 사진 폴더"
v.nodes["x1"]["label"] = "Pillow ·\npillow-heif(HEIC)"
v.nodes["x2"]["label"] = "ffmpeg 자동 준비 ·\nOpenAI TTS"
v.nodes["x3"]["label"] = "Mac say / Win 음성\n(선택: Chrome)"
v.nodes["k1"]["label"] = "SKILL.md ·\nsetup.py 첫 준비"
v.build()
print("done:", sorted(p.name for p in OUT.iterdir() if p.suffix in (".drawio", ".svg")))
