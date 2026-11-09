"""티스토리 글 — HTML 모드에 붙여 넣을 post.html + 로컬 미리보기 preview.html + images/."""
import html
import re
import shutil
from pathlib import Path

from common import RULES, load

PREVIEW_CSS = """body{max-width:760px;margin:40px auto;padding:0 16px;font-family:'Apple SD Gothic Neo',sans-serif;line-height:1.8;color:#222}
img{width:100%;border-radius:8px;margin:8px 0}figure{margin:16px 0}figcaption{color:#888;font-size:14px;text-align:center}h1{font-size:28px}h2{font-size:22px;margin-top:40px;border-left:4px solid #1D9E75;padding-left:10px}
table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:8px;text-align:left}th{background:#f4f4f0;width:28%}
.notice{background:#FAECE7;padding:10px 14px;border-radius:6px}.tags{color:#1D9E75}.check{color:#BA7517;font-size:14px}"""


def _yt_id(url):
    m = re.search(r"(?:youtu\.be/|v=|shorts/|embed/)([\w-]{11})", url or "")
    return m.group(1) if m else None


def blocks_of(sec):
    """섹션을 [("text", 문단) | ("photo", 파일명, 설명)] 순서로 펼친다.

    새 형식: sec["blocks"] = [{"text": "…"}, {"photo": "01_P001.jpg", "caption": "…"}, …] — 적힌 순서 그대로 (글→사진→글).
    옛 형식: sec["photos"] + sec["text"] — 사진을 문단 사이에 번갈아 끼운다 (사진을 한꺼번에 몰지 않음).
    """
    if "blocks" in sec:
        out = []
        for b in sec["blocks"]:
            if "photo" in b:
                out.append(("photo", b["photo"], b.get("caption", ""), b.get("alt", "")))
            elif b.get("text"):
                out.append(("text", b["text"]))
        return out
    photos, texts = list(sec.get("photos", [])), list(sec.get("text", []))
    out = []
    while photos or texts:
        if photos:
            out.append(("photo", photos.pop(0), "", ""))
        if texts:
            out.append(("text", texts.pop(0)))
    return out


def layout(content):
    """글 전체를 펼친 순서. 점검(check_rules)과 미리보기에 같이 쓴다."""
    ts = content["tistory"]
    seq = [("text", ts["intro"])]
    for sec in ts["sections"]:
        seq.append(("h2", sec["h2"]))
        for b in blocks_of(sec):
            seq.append(b + (sec,) if b[0] == "photo" else b)
    return seq


def build(content, best_dir, out_dir, youtube_url=None, cfg=None):
    ts, info, main = content["tistory"], content.get("info", {}), content["seo"]["main"]
    R = load(RULES)["common"]
    out_dir = Path(out_dir)
    img_dir = out_dir / "images"
    if img_dir.exists():
        shutil.rmtree(img_dir)
    img_dir.mkdir(parents=True)
    e = html.escape
    parts, md = [], [f"# {ts['title']}", ""]
    if content.get("sponsored"):
        parts.append(f'<p class="notice">{e(R["sponsor_notice"])}</p>')
        md += [f"> {R['sponsor_notice']}", ""]
    n, used = 0, []
    for item in layout(content):
        kind = item[0]
        if kind == "h2":
            parts.append(f"<h2>{e(item[1])}</h2>")
            md += [f"## {item[1]}", ""]
        elif kind == "text":
            parts.append(f"<p>{e(item[1])}</p>")
            md += [item[1], ""]
        else:
            _, ph, caption, alt_one, sec = item
            src = Path(best_dir) / ph
            if not src.exists():
                raise SystemExit(f"티스토리 사진이 best_tistory에 없습니다: {ph}")
            n += 1
            name = f"{n:02d}.jpg"
            shutil.copy2(src, img_dir / name)
            if not (img_dir / name).stat().st_size:
                raise SystemExit(f"사진 복사 실패: {name}")
            used.append({"n": n, "file": f"images/{name}", "source": ph})
            alt = alt_one or caption or sec.get("alt") or f"{main} {sec['h2']}"
            alt = alt if alt_one or caption else f"{alt} {n}"
            fig = f'<img src="images/{name}" alt="{e(alt)}">'
            parts.append(f"<figure>{fig}<figcaption>{e(caption)}</figcaption></figure>" if caption else f"<p>{fig}</p>")
            md += [f"![{alt}](images/{name})", ""] + ([f"*{caption}*", ""] if caption else [])
    if info:
        parts.append(f"<h2>{e(content['place'])} 기본 정보</h2>")
        md += [f"## {content['place']} 기본 정보", "", "| 항목 | 내용 |", "| --- | --- |"]
        unver = set(info.get("unverified", []))
        rows = [(k, v) for k, v in info.items() if k not in ("sources", "unverified", "tips") and v]
        labels = {"address": "위치", "hours": "운영 시간", "fee": "요금", "parking": "주차", "best_time": "추천 시기", "contact": "문의"}
        parts.append("<table>" + "".join(
            f"<tr><th>{e(labels.get(k, k))}</th><td>{e(str(v))}{' <span class=\"check\">(방문 전 확인 필요)</span>' if k in unver else ''}</td></tr>"
            for k, v in rows) + "</table>")
        md += [f"| {labels.get(k, k)} | {v}{' (방문 전 확인 필요)' if k in unver else ''} |" for k, v in rows] + [""]
        if info.get("tips"):
            parts.append("<ul>" + "".join(f"<li>{e(t)}</li>" for t in info["tips"]) + "</ul>")
            md += [f"- {t}" for t in info["tips"]] + [""]
        if info.get("sources"):
            parts.append("<p>참고: " + " · ".join(f'<a href="{e(u)}">{e(re.sub(r"^https?://(www\\.)?", "", u).split("/")[0])}</a>' for u in info["sources"]) + "</p>")
            md += ["참고: " + " · ".join(info["sources"]), ""]
    vid = _yt_id(youtube_url)
    if vid:
        parts.append("<h2>숏폼으로 보기</h2>")
        parts.append(f'<p><iframe width="360" height="640" src="https://www.youtube.com/embed/{vid}" '
                     f'title="{e(main)} 숏폼" frameborder="0" allowfullscreen></iframe></p>')
        md += ["## 숏폼으로 보기", "", youtube_url, ""]
    if ts.get("outro"):
        parts.append(f"<p>{e(ts['outro'])}</p>")
        md += [ts["outro"], ""]
    cover_i = (cfg or {}).get("blog", {}).get("cover_photo_index", 0)
    cover = used[cover_i]["file"] if used else None
    md += [" ".join("#" + t for t in ts["tags"]), ""]
    md.insert(1, f"\n> 대표 이미지: {cover}" if cover else "")
    body = "\n".join(parts)
    (out_dir / "post.html").write_text(body + "\n", encoding="utf-8")
    (out_dir / "article.md").write_text("\n".join(md), encoding="utf-8")
    (out_dir / "tags.txt").write_text(", ".join(ts["tags"]) + "\n", encoding="utf-8")
    (out_dir / "title.txt").write_text(ts["title"] + "\n", encoding="utf-8")
    (out_dir / "cover.txt").write_text((cover or "") + "\n", encoding="utf-8")
    (out_dir / "preview.html").write_text(
        f"<!doctype html><html lang='ko'><meta charset='utf-8'><title>{e(ts['title'])}</title><style>{PREVIEW_CSS}</style>"
        f"<p class='check'>미리보기 · 대표 이미지 {e(cover or '없음')}</p>"
        f"<h1>{e(ts['title'])}</h1>{body}<p class='tags'>{' '.join('#' + t for t in ts['tags'])}</p></html>",
        encoding="utf-8")
    return used
