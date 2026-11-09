"""As-Is / To-Be / 시스템 구성도를 Draw.io(.drawio)와 SVG로 함께 만든다.

python3.12 docs/diagrams/build_diagrams.py
같은 좌표로 두 파일을 만들기 때문에 Draw.io에서 열어 고쳐도 배치가 그대로다.
"""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent

HEAD_W, LANE_H, COL_W, LEFT_PAD, TOP = 120, 140, 160, 24, 70
NODE_W, NODE_H, DIA_W, DIA_H, CIRC = 132, 62, 120, 84, 34

STYLES = {  # fill, stroke, dashed
    "normal": ("#F1EFE8", "#888780", False),
    "problem": ("#FAECE7", "#D85A30", False),
    "keep": ("#F1EFE8", "#888780", False),
    "change": ("#E6F1FB", "#378ADD", False),
    "add": ("#E1F5EE", "#1D9E75", False),
    "move": ("#EEEDFE", "#7F77DD", False),
    "option": ("#FFFFFF", "#1D9E75", True),
    "store": ("#FAEEDA", "#BA7517", False),
    "ext": ("#FFFFFF", "#888780", True),
}
FONT = "Apple SD Gothic Neo, Pretendard, sans-serif"


class Diagram:
    def __init__(self, name, title, lanes, ncols):
        self.name, self.title, self.lanes, self.ncols = name, title, lanes, ncols
        self.nodes, self.edges, self.badges, self.legend = {}, [], [], []
        self.width = HEAD_W + LEFT_PAD * 2 + ncols * COL_W
        self.height = TOP + len(lanes) * LANE_H

    def lane_top(self, lane):
        return TOP + self.lanes.index(lane) * LANE_H

    def node(self, nid, lane, col, label, kind="task", style="normal"):
        w, h = {"task": (NODE_W, NODE_H), "decision": (DIA_W, DIA_H),
                "start": (CIRC, CIRC), "end": (CIRC, CIRC)}[kind]
        cx = HEAD_W + LEFT_PAD + col * COL_W + COL_W / 2
        cy = self.lane_top(lane) + LANE_H / 2
        self.nodes[nid] = dict(x=cx - w / 2, y=cy - h / 2, w=w, h=h, cx=cx, cy=cy,
                               label=label, kind=kind, style=style)

    def edge(self, a, b, label="", exit="right", entry="left", kind="normal", via=None):
        self.edges.append(dict(a=a, b=b, label=label, exit=exit, entry=entry, kind=kind, via=via))

    def badge(self, nid, text):
        self.badges.append((nid, text))

    # ---------- geometry ----------
    def port(self, nid, spec):
        """spec = 'side' 또는 'side:offset' (top/bottom은 x 이동, left/right는 y 이동)."""
        side, _, off = spec.partition(":")
        off = float(off or 0)
        n = self.nodes[nid]
        if side in ("top", "bottom"):
            x = n["cx"] + off
            inset = abs(off) * n["h"] / n["w"] if n["kind"] == "decision" else 0
            y = n["y"] + inset if side == "top" else n["y"] + n["h"] - inset
        else:
            y = n["cy"] + off
            inset = abs(off) * n["w"] / n["h"] if n["kind"] == "decision" else 0
            x = n["x"] + inset if side == "left" else n["x"] + n["w"] - inset
        return x, y

    def rel(self, nid, spec):
        x, y = self.port(nid, spec)
        n = self.nodes[nid]
        return (x - n["x"]) / n["w"], (y - n["y"]) / n["h"]

    def route(self, e):
        (x1, y1), (x2, y2) = self.port(e["a"], e["exit"]), self.port(e["b"], e["entry"])
        hx = e["exit"].split(":")[0] in ("left", "right")
        hy = e["entry"].split(":")[0] in ("left", "right")
        if hx and hy:
            if abs(y1 - y2) < 1:
                pts = []
            else:
                xm = e["via"] if e["via"] is not None else (x1 + x2) / 2
                pts = [(xm, y1), (xm, y2)]
        elif not hx and not hy:
            if abs(x1 - x2) < 1:
                pts = []
            else:
                ym = e["via"] if e["via"] is not None else (y1 + y2) / 2
                pts = [(x1, ym), (x2, ym)]
        elif hx and not hy:
            pts = [(x2, y1)]
        else:
            pts = [(x1, y2)]
        return [(x1, y1)] + pts + [(x2, y2)]

    # ---------- drawio ----------
    def drawio(self):
        cells, i = [], 2

        def nid():
            nonlocal i
            i += 1
            return f"c{i}"

        ids = {}
        cells.append(f'<mxCell id="title" value="{escape(self.title)}" style="text;fontSize=18;fontStyle=1;align=left;fontFamily={FONT};" vertex="1" parent="1"><mxGeometry x="20" y="16" width="900" height="30" as="geometry"/></mxCell>')
        for lane in self.lanes:
            y = self.lane_top(lane)
            cells.append(f'<mxCell id="{nid()}" value="" style="rounded=0;fillColor=none;strokeColor=#B4B2A9;" vertex="1" parent="1"><mxGeometry x="0" y="{y}" width="{self.width}" height="{LANE_H}" as="geometry"/></mxCell>')
            cells.append(f'<mxCell id="{nid()}" value="{escape(lane)}" style="rounded=0;fillColor=#F1EFE8;strokeColor=#B4B2A9;fontStyle=1;fontSize=13;whiteSpace=wrap;fontFamily={FONT};" vertex="1" parent="1"><mxGeometry x="0" y="{y}" width="{HEAD_W}" height="{LANE_H}" as="geometry"/></mxCell>')
        for k, n in self.nodes.items():
            fill, stroke, dashed = STYLES[n["style"]]
            shape = {"task": "rounded=1;arcSize=12;", "decision": "rhombus;",
                     "start": "ellipse;", "end": "ellipse;strokeWidth=3;"}[n["kind"]]
            st = f'{shape}whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontSize=11;fontFamily={FONT};' + ("dashed=1;" if dashed else "")
            ids[k] = nid()
            val = escape(n["label"]).replace("\n", "&lt;br&gt;")
            cells.append(f'<mxCell id="{ids[k]}" value="{val}" style="{st}" vertex="1" parent="1"><mxGeometry x="{n["x"]:.0f}" y="{n["y"]:.0f}" width="{n["w"]}" height="{n["h"]}" as="geometry"/></mxCell>')
        for e in self.edges:
            pts = self.route(e)[1:-1]
            color = {"normal": "#0F6E56", "loop": "#D85A30", "data": "#888780", "option": "#1D9E75"}[e["kind"]]
            dash = "dashed=1;" if e["kind"] != "normal" else ""
            wp = "".join(f'<mxPoint x="{x:.0f}" y="{y:.0f}"/>' for x, y in pts)
            ex, ey = self.rel(e["a"], e["exit"])
            nx, ny = self.rel(e["b"], e["entry"])
            st = (f'edgeStyle=none;html=1;endArrow=block;endFill=1;strokeColor={color};fontSize=10;fontFamily={FONT};{dash}labelBackgroundColor=#FFFFFF;'
                  f'exitX={ex:.3f};exitY={ey:.3f};exitDx=0;exitDy=0;entryX={nx:.3f};entryY={ny:.3f};entryDx=0;entryDy=0;')
            cells.append(f'<mxCell id="{nid()}" value="{escape(e["label"])}" style="{st}" edge="1" parent="1" source="{ids[e["a"]]}" target="{ids[e["b"]]}"><mxGeometry relative="1" as="geometry">' + (f'<Array as="points">{wp}</Array>' if wp else "") + '</mxGeometry></mxCell>')
        for k, text in self.badges:
            n = self.nodes[k]
            cells.append(f'<mxCell id="{nid()}" value="{escape(text)}" style="rounded=1;arcSize=50;fillColor=#E24B4A;strokeColor=none;fontColor=#FFFFFF;fontSize=10;fontStyle=1;fontFamily={FONT};" vertex="1" parent="1"><mxGeometry x="{n["x"] + n["w"] - 18:.0f}" y="{n["y"] - 9:.0f}" width="26" height="18" as="geometry"/></mxCell>')
        ly = self.height + 16
        for j, (style, text) in enumerate(self.legend):
            fill, stroke, dashed = STYLES.get(style, ("#FFFFFF", style, False))
            x = 20 + j * 170
            cells.append(f'<mxCell id="{nid()}" value="" style="rounded=1;fillColor={fill};strokeColor={stroke};' + ("dashed=1;" if dashed else "") + f'" vertex="1" parent="1"><mxGeometry x="{x}" y="{ly}" width="22" height="14" as="geometry"/></mxCell>')
            cells.append(f'<mxCell id="{nid()}" value="{escape(text)}" style="text;fontSize=11;align=left;fontFamily={FONT};" vertex="1" parent="1"><mxGeometry x="{x + 28}" y="{ly - 4}" width="140" height="22" as="geometry"/></mxCell>')
        body = "".join(cells)
        xml = (f'<mxfile host="build_diagrams.py"><diagram name="{escape(self.name)}" id="{self.name}">'
               f'<mxGraphModel dx="1200" dy="800" grid="0" gridSize="10" guides="1" page="0" pageScale="1" math="0" shadow="0">'
               f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>{body}</root></mxGraphModel></diagram></mxfile>')
        (OUT / f"{self.name}.drawio").write_text(xml, encoding="utf-8")

    # ---------- svg ----------
    def svg(self):
        H = self.height + 50
        o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{H}" viewBox="0 0 {self.width} {H}" font-family="{FONT}">',
             '<defs>' + "".join(f'<marker id="m{c[1:]}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="{c}"/></marker>' for c in ("#0F6E56", "#D85A30", "#888780", "#1D9E75")) + '</defs>',
             f'<rect width="{self.width}" height="{H}" fill="#FFFFFF"/>',
             f'<text x="20" y="38" font-size="18" font-weight="700" fill="#2C2C2A">{escape(self.title)}</text>']
        for lane in self.lanes:
            y = self.lane_top(lane)
            o.append(f'<rect x="0.5" y="{y}" width="{self.width - 1}" height="{LANE_H}" fill="none" stroke="#B4B2A9"/>')
            o.append(f'<rect x="0.5" y="{y}" width="{HEAD_W}" height="{LANE_H}" fill="#F1EFE8" stroke="#B4B2A9"/>')
            o.append(self._text(HEAD_W / 2, y + LANE_H / 2, lane, 13, "#2C2C2A", bold=True))
        for e in self.edges:
            pts = self.route(e)
            color = {"normal": "#0F6E56", "loop": "#D85A30", "data": "#888780", "option": "#1D9E75"}[e["kind"]]
            dash = ' stroke-dasharray="6 4"' if e["kind"] != "normal" else ""
            d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
            o.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.6"{dash} marker-end="url(#m{color[1:]})"/>')
            if e["label"]:
                (ax, ay), (bx, by) = pts[0], pts[1]
                lx, ly = (ax + bx) / 2, (ay + by) / 2
                tw = len(e["label"]) * 11 + 8
                o.append(f'<rect x="{lx - tw / 2:.1f}" y="{ly - 9:.1f}" width="{tw}" height="18" rx="3" fill="#FFFFFF"/>')
                o.append(self._text(lx, ly, e["label"], 10.5, color, bold=True))
        for n in self.nodes.values():
            fill, stroke, dashed = STYLES[n["style"]]
            dash = ' stroke-dasharray="5 3"' if dashed else ""
            if n["kind"] == "task":
                o.append(f'<rect x="{n["x"]:.1f}" y="{n["y"]:.1f}" width="{n["w"]}" height="{n["h"]}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.3"{dash}/>')
            elif n["kind"] == "decision":
                cx, cy, w, h = n["cx"], n["cy"], n["w"], n["h"]
                o.append(f'<polygon points="{cx},{cy - h / 2} {cx + w / 2},{cy} {cx},{cy + h / 2} {cx - w / 2},{cy}" fill="{fill}" stroke="{stroke}" stroke-width="1.3"/>')
            else:
                sw = 3 if n["kind"] == "end" else 1.3
                o.append(f'<circle cx="{n["cx"]}" cy="{n["cy"]}" r="{CIRC / 2}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
            if n["kind"] in ("start", "end"):
                o.append(self._text(n["cx"], n["y"] + n["h"] + 12, n["label"], 10.5, "#444441"))
            else:
                o.append(self._text(n["cx"], n["cy"], n["label"], 11, "#2C2C2A"))
        for k, text in self.badges:
            n = self.nodes[k]
            x, y = n["x"] + n["w"] - 18, n["y"] - 9
            o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="26" height="18" rx="9" fill="#E24B4A"/>')
            o.append(self._text(x + 13, y + 9, text, 10, "#FFFFFF", bold=True))
        ly = self.height + 22
        for j, (style, text) in enumerate(self.legend):
            fill, stroke, dashed = STYLES.get(style, ("#FFFFFF", style, False))
            x = 20 + j * 170
            dash = ' stroke-dasharray="4 2"' if dashed else ""
            o.append(f'<rect x="{x}" y="{ly}" width="22" height="14" rx="3" fill="{fill}" stroke="{stroke}"{dash}/>')
            o.append(f'<text x="{x + 28}" y="{ly + 11}" font-size="11.5" fill="#444441">{escape(text)}</text>')
        o.append("</svg>")
        (OUT / f"{self.name}.svg").write_text("\n".join(o), encoding="utf-8")

    @staticmethod
    def _text(x, y, label, size, color, bold=False):
        lines = label.split("\n")
        lh = size * 1.3
        y0 = y - lh * (len(lines) - 1) / 2
        fw = ' font-weight="700"' if bold else ""
        spans = "".join(f'<tspan x="{x:.1f}" y="{y0 + i * lh:.1f}">{escape(t)}</tspan>' for i, t in enumerate(lines))
        return f'<text text-anchor="middle" dominant-baseline="central" font-size="{size}" fill="{color}"{fw}>{spans}</text>'

    def build(self):
        self.drawio()
        self.svg()


# =================== As-Is ===================
L_CEO, L_MGR, L_ED, L_CH = "대표\n(가상)", "매니저\n(가상)", "에디터\n(본인)", "외부 채널"
a = Diagram("asis", "As-Is · 여행 콘텐츠 제작 (F 실제 / V 가상 팀 설정 · 유튜브는 실제로 아직 못 하는 일)", [L_CEO, L_MGR, L_ED, L_CH], 13)
a.node("start", L_ED, 0, "시작", "start")
a.node("A01", L_ED, 0.75, "A01 사진 고르기\n사진첩 · F", style="problem")
a.node("A02", L_ED, 1.75, "A02 장소 정보 찾기\n지도·검색 · F", style="problem")
a.node("A03", L_ED, 2.75, "A03 인스타 카드\n수작업 + 캡션·태그\nF", style="problem")
a.node("A04", L_MGR, 3.75, "인스타\n검토\nA04 · V", "decision", style="problem")
a.node("A05", L_ED, 3.75, "A05 수정 후\n메신저로 재전송\nV", style="problem")
a.node("A06", L_ED, 4.95, "A06 숏폼 직접 편집\n+ 제목·설명 작성\nV · 실제 미실시", style="problem")
a.node("A07", L_MGR, 5.95, "유튜브\n검토\nA07 · V", "decision", style="problem")
a.node("A08", L_ED, 5.95, "A08 다시 편집 후\n재전송\nV", style="problem")
a.node("A09", L_ED, 7.15, "A09 티스토리 글\n처음부터 새로 작성\nF", style="problem")
a.node("A10", L_MGR, 8.15, "티스토리\n검토\nA10 · V", "decision", style="problem")
a.node("A11", L_ED, 8.15, "A11 수정 후\n재전송\nV", style="problem")
a.node("A12", L_CEO, 9.3, "최종\n승인?\nA12 · V", "decision")
a.node("A13", L_ED, 10.3, "A13 3채널 게시\n인스타·티스토리 F\n유튜브 V")
a.node("A13x", L_CH, 10.3, "인스타 · 유튜브\n· 티스토리 게시됨")
a.node("A14", L_ED, 11.3, "A14 기록 없음\n메신저·폴더에 흩어짐\nV", style="problem")
a.node("end", L_ED, 12.2, "종료", "end")
a.edge("start", "A01")
a.edge("A01", "A02")
a.edge("A02", "A03")
a.edge("A03", "A04", "검토 요청", exit="top", entry="left")
a.edge("A04", "A05", "수정", exit="bottom:-16", entry="top:-16", kind="loop")
a.edge("A05", "A04", "재검토", exit="top:16", entry="bottom:16", kind="loop")
a.edge("A04", "A06", "통과", exit="right", entry="top")
a.edge("A06", "A07", "", exit="right", entry="left", via=a.nodes["A06"]["x"] + NODE_W + 14)
a.edge("A07", "A08", "수정", exit="bottom:-16", entry="top:-16", kind="loop")
a.edge("A08", "A07", "재검토", exit="top:16", entry="bottom:16", kind="loop")
a.edge("A07", "A09", "통과", exit="right", entry="top")
a.edge("A09", "A10", "", exit="right", entry="left", via=a.nodes["A09"]["x"] + NODE_W + 14)
a.edge("A10", "A11", "수정", exit="bottom:-16", entry="top:-16", kind="loop")
a.edge("A11", "A10", "재검토", exit="top:16", entry="bottom:16", kind="loop")
a.edge("A10", "A12", "통과", exit="top", entry="left")
a.edge("A12", "A11", "반려", exit="bottom", entry="right", kind="loop")
a.edge("A12", "A13", "승인", exit="right", entry="top")
a.edge("A13", "A13x", exit="bottom", entry="top", kind="data")
a.edge("A13", "A14")
a.edge("A14", "end")
for k, b in [("A01", "P1"), ("A03", "P1"), ("A02", "P2"), ("A09", "P2"), ("A06", "P3"), ("A04", "P4"), ("A07", "P4"), ("A10", "P4"), ("A05", "P5"), ("A08", "P5"), ("A11", "P5"), ("A14", "P6")]:
    a.badge(k, b)
a.legend = [("normal", "현재 작업"), ("problem", "문제가 있는 단계"), ("#D85A30", "주황 점선: 되돌림"), ("#888780", "회색 점선: 게시")]
a.build()

# =================== To-Be ===================
T_CEO, T_MGR, T_ED, T_AI, T_SYS, T_CH = "대표\n(가상)", "매니저\n(가상)", "에디터\n(본인)", "AI\n(Claude 스킬)", "시스템\n(스크립트·파일)", "외부 채널"
t = Diagram("tobe", "To-Be · 인스타 → 유튜브 → 티스토리 순차 제작 + 채널별 컨펌 + 대표 최종 승인", [T_CEO, T_MGR, T_ED, T_AI, T_SYS, T_CH], 15)
t.node("start", T_ED, 0, "시작", "start")
t.node("T01", T_ED, 0.75, "T01 사진·메모\n입력 폴더에 저장\n변경", style="change")
t.node("T02", T_AI, 1.75, "T02 인스타 카드 구성\n캡션·해시태그 초안\n이동", style="move")
t.node("T03", T_SYS, 2.75, "T03 카드 PNG 렌더\n+ 규칙 점검\n추가", style="add")
t.node("T04", T_MGR, 3.75, "컨펌 ①\n인스타\nT04 변경", "decision", style="change")
t.node("T05", T_AI, 4.75, "T05 유튜브 제목·\n설명·태그 초안\n이동", style="move")
t.node("T06", T_SYS, 5.75, "T06 숏폼 MP4 자동 생성\n+ 규칙 점검\n변경", style="change")
t.node("T07", T_MGR, 6.75, "컨펌 ②\n유튜브\nT07 변경", "decision", style="change")
t.node("T08", T_AI, 7.75, "T08 티스토리 글\n(앞 두 채널 확장)\n이동", style="move")
t.node("T09", T_SYS, 8.75, "T09 블로그 HTML\n+ 규칙 점검\n추가", style="add")
t.node("T10", T_MGR, 9.75, "컨펌 ③\n티스토리\nT10 변경", "decision", style="change")
t.node("T11", T_CEO, 10.75, "최종 승인\n3채널 묶음\nT11 유지", "decision", style="keep")
t.node("T12", T_ED, 11.75, "T12 3채널 업로드\n+ 링크 입력\n변경", style="change")
t.node("T13", T_CH, 11.75, "인스타 · 유튜브\n· 티스토리", style="ext")
t.node("T14", T_SYS, 12.75, "T14 콘텐츠대장\n게시 완료 기록\n추가", style="add")
t.node("end", T_SYS, 13.9, "종료", "end")
t.edge("start", "T01")
t.edge("T01", "T02", exit="bottom", entry="left")
t.edge("T02", "T03", exit="bottom", entry="left")
t.edge("T03", "T04", "점검 통과", exit="top", entry="left")
t.edge("T04", "T02", "반려 · 사유 → v2", exit="bottom", entry="top", kind="loop")
t.edge("T04", "T05", "컨펌", exit="right", entry="top")
t.edge("T05", "T06", exit="bottom", entry="left")
t.edge("T06", "T07", "점검 통과", exit="top", entry="left")
t.edge("T07", "T05", "반려 → v2", exit="bottom", entry="top", kind="loop")
t.edge("T07", "T08", "컨펌", exit="right", entry="top")
t.edge("T08", "T09", exit="bottom", entry="left")
t.edge("T09", "T10", "점검 통과", exit="top", entry="left")
t.edge("T10", "T08", "반려 → v2", exit="bottom", entry="top", kind="loop")
t.edge("T10", "T11", "컨펌", exit="top", entry="left")
t.edge("T11", "T10", "반려 · 채널 지정", exit="bottom", entry="right", kind="loop")
t.edge("T11", "T12", "승인", exit="right", entry="top")
t.edge("T12", "T13", exit="bottom:-30", entry="top:-30", kind="data")
t.edge("T12", "T14", exit="bottom:20", entry="left")
t.edge("T14", "end")
t.legend = [("keep", "유지"), ("change", "변경"), ("move", "이동 (사람 → AI)"), ("add", "추가"), ("ext", "외부 (자동화 안 함)")]
t.build()

# =================== 시스템 구성도 ===================
A_HUM, A_AI, A_RULE, A_STORE, A_EXT = "사람\n(에디터·매니저·대표)", "AI 처리\n(Claude 스킬)", "규칙 처리\n(스크립트)", "저장소\n(로컬 PC)", "외부 채널\n(사람이 업로드)"
s = Diagram("architecture", "개략 시스템 구성 · Claude Code 스킬 + 로컬 파일", [A_HUM, A_AI, A_RULE, A_STORE, A_EXT], 8)
s.node("in1", A_HUM, 0.6, "에디터\ninput/C-001/\n사진 · memo.md", style="store")
s.node("in2", A_HUM, 4.6, "Claude Code 대화\n매니저 컨펌·반려\n대표 승인·반려", style="change")
s.node("ai1", A_AI, 1.6, "채널별 초안\ncontent.json\n인스타→유튜브→티스토리", style="move")
s.node("r1", A_RULE, 2.6, "카드 렌더러\nHTML → PNG", style="add")
s.node("r2", A_RULE, 3.6, "숏폼 생성\nffmpeg → MP4", style="add")
s.node("r3", A_RULE, 4.6, "블로그 생성\nHTML", style="add")
s.node("r4", A_RULE, 5.6, "규칙 점검기\nrules.json", style="add")
s.node("r5", A_RULE, 6.6, "대장 기록기\n상태·버전·중복 방지", style="add")
s.node("st0", A_STORE, 5.6, "rules.json\n게시 규칙", style="store")
s.node("st1", A_STORE, 3.6, "output/C-001/\n채널/vN/ 결과물", style="store")
s.node("st2", A_STORE, 6.6, "ledger.xlsx\n콘텐츠대장", style="store")
s.node("ex1", A_EXT, 3.6, "인스타 · 유튜브\n· 티스토리", style="ext")
s.edge("in1", "ai1", exit="bottom", entry="left")
s.edge("ai1", "r1", exit="bottom", entry="left")
s.edge("r1", "r2")
s.edge("r2", "r3")
s.edge("r3", "r4")
s.edge("r4", "r5")
s.edge("st0", "r4", exit="top", entry="bottom", kind="data")
s.edge("r2", "st1", exit="bottom", entry="top")
s.edge("r5", "st2", exit="bottom", entry="top")
s.edge("st1", "ex1", "에디터 업로드", exit="bottom", entry="top", kind="data")
s.edge("in2", "ai1", "반려 사유", exit="bottom", entry="right", kind="loop")
s.edge("in2", "r5", "컨펌 기록", exit="right", entry="top", kind="data")
s.legend = [("store", "파일·저장소"), ("move", "AI 처리"), ("add", "규칙 처리"), ("change", "사람 접점"), ("ext", "외부 (자동화 안 함)")]
s.build()
print("done:", sorted(p.name for p in OUT.iterdir() if p.suffix in (".drawio", ".svg")))
