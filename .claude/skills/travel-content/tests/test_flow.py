"""travel-content 스크립트 테스트 (표준 unittest, 새 패키지 없음).

실행: .venv/bin/python -m unittest discover -s .claude/skills/travel-content/tests -v
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from PIL import Image, ImageChops, ImageStat  # noqa: E402

import build_blog  # noqa: E402
import check_rules  # noqa: E402
import insta  # noqa: E402
import render_cards  # noqa: E402
import state  # noqa: E402
from common import font_file, settings  # noqa: E402
from make_shorts import split_sentences, tts_text, wrap_pages  # noqa: E402


def make_photos(d, n, size=(600, 800)):
    d.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        Image.new("RGB", size, ((i * 37) % 255, (i * 91) % 255, 120)).save(d / f"IMG_{i:03d}.jpg", quality=90)
    return d


def tc(*args):
    r = subprocess.run([sys.executable, str(SCRIPTS / "tc.py"), *map(str, args)], capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.work = self.tmp / "work" / "C-999_테스트"
        state.init(self.work, "C-999", "테스트")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class InstaFlow(Base):
    def test_pick_all_when_20_or_less(self):
        src = make_photos(self.tmp / "src", 7)
        res = insta.pick(self.work, src)
        self.assertTrue(res["auto"])
        self.assertEqual(res["count"], 7)
        self.assertEqual(len(list((self.work / "insta_pick").glob("*.jpg"))), 7)

    def test_pick_over_20_needs_ids(self):
        src = make_photos(self.tmp / "src", 22, size=(300, 400))
        with self.assertRaises(SystemExit):
            insta.pick(self.work, src)
        ids = [r["id"] for r in json.loads((self.work / "photos.json").read_text())["photos"]][:20]
        self.assertEqual(insta.pick(self.work, src, ids)["count"], 20)

    def test_mine_empty_is_refused(self):
        insta.mine(self.work)
        with self.assertRaises(SystemExit):
            insta.use(self.work, "insta_mine")

    def test_order_puts_cover_first_and_drops(self):
        src = make_photos(self.tmp / "src", 5)
        insta.pick(self.work, src)
        insta.use(self.work, "insta_pick")
        insta.cover(self.work, 3, ["전남", "강진"], "가우도")
        res = insta.order(self.work, [1, 2, 3, 5])  # 4번 빼기, 표지(3번)는 맨 앞으로
        self.assertTrue(res["order"][0].startswith("01_cover_"))
        self.assertEqual(len(res["order"]), 4)
        self.assertEqual(res["dropped"], [4])
        c = json.loads((self.work / "content.json").read_text())
        self.assertEqual([x["photo"] for x in c["instagram"]["cards"]], res["order"])

    def test_cover_only_text(self):
        src = make_photos(self.tmp / "src", 3)
        insta.pick(self.work, src)
        insta.use(self.work, "insta_pick")
        insta.cover(self.work, 1, ["전남", "강진"], "가우도")
        insta.order(self.work, [1, 2, 3])
        c = json.loads((self.work / "content.json").read_text())
        c["instagram"]["cards"][1]["text"] = "이 문구는 기본 설정에서 그리지 않아야 함"
        out = self.tmp / "cards"
        render_cards.render(c, self.work / "best_insta", out, settings(), insta.widths(self.work))
        plain = render_cards._fit_width(Image.open(self.work / "best_insta" / c["instagram"]["cards"][1]["photo"]).convert("RGB"), 1080)
        card2 = Image.open(out / "card_02.jpg").convert("RGB")
        diff = ImageStat.Stat(ImageChops.difference(plain, card2).convert("L")).mean[0]
        self.assertLess(diff, 2.0)  # 2번 카드 = 원본 사진 (JPEG 오차만)
        cover = Image.open(out / "card_01.jpg").convert("RGB")
        first = render_cards._fit_width(Image.open(self.work / "best_insta" / c["instagram"]["cards"][0]["photo"]).convert("RGB"), 1080)
        self.assertGreater(ImageStat.Stat(ImageChops.difference(first, cover).convert("L")).mean[0], 0.5)  # 표지엔 글자

    def test_publish_needs_ceo_approval(self):
        st = state.get(self.work)
        st["insta_photos"] = "fixed"
        state.put(self.work, st)
        state.start_build(self.work, "instagram")
        state.built(self.work, "instagram", 1, True, "x")
        state.confirm(self.work, "instagram", True)
        with self.assertRaises(state.Refused):
            state.published(self.work, "instagram", "https://example.com")
        state.ceo(self.work, "instagram", True)
        state.published(self.work, "instagram", "https://example.com")
        self.assertEqual(state.get(self.work)["channels"]["instagram"]["status"], "published")

    def test_build_refused_before_photos_fixed(self):
        with self.assertRaises(state.Refused):
            state.start_build(self.work, "instagram")


class Points(Base):
    """확인 지점 흐름: ceo 여러 채널, publish-all 링크 검사."""

    def ready(self, chs, status="confirmed"):
        st = state.get(self.work)
        for c in chs:
            st["channels"][c].update(version=1, status=status)
        st["insta_photos"] = "fixed"
        state.put(self.work, st)
        (self.work / "content.json").write_text(json.dumps({"youtube": {}}, ensure_ascii=False))

    def test_ceo_all_needs_every_channel_confirmed(self):
        self.ready(["instagram", "youtube"])  # 티스토리는 아직
        code, _, err = tc("ceo", "--work", self.work, "--ch", "all", "--approve")
        self.assertEqual(code, 2)
        self.assertIn("티스토리", err)
        self.assertEqual(state.get(self.work)["channels"]["instagram"]["status"], "confirmed")  # 아무것도 안 바뀜
        code, out, _ = tc("ceo", "--work", self.work, "--ch", "instagram,youtube", "--approve")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {"instagram": "approved", "youtube": "approved"})

    def test_publish_all_checks_links(self):
        self.ready(["instagram", "youtube", "tistory"], "approved")
        code, _, err = tc("publish-all", "--work", self.work, "--instagram", "https://www.instagram.com/")
        self.assertEqual(code, 2)
        self.assertIn("게시물 링크가 아닙니다", err)
        code, out, _ = tc("publish-all", "--work", self.work, "--instagram", "https://www.instagram.com/p/ABC123/",
                          "--youtube", "https://youtube.com/shorts/abcdefghijk")
        self.assertEqual(code, 0)
        st = state.get(self.work)["channels"]
        self.assertEqual((st["instagram"]["status"], st["youtube"]["status"], st["tistory"]["status"]),
                         ("published", "published", "approved"))
        c = json.loads((self.work / "content.json").read_text())
        self.assertEqual(c["youtube"]["url"], "https://youtube.com/shorts/abcdefghijk")

    def test_publish_all_refuses_before_ceo(self):
        self.ready(["tistory"], "confirmed")
        code, _, err = tc("publish-all", "--work", self.work, "--tistory", "https://jexists.tistory.com/123")
        self.assertEqual(code, 2)
        self.assertIn("대표 승인 전", err)


class Blog(unittest.TestCase):
    def content(self, blocks):
        return {"place": "가우도", "sponsored": False, "seo": {"main": "강진 가우도"}, "info": {},
                "tistory": {"title": "강진 가우도 여행", "intro": "강진 가우도는 작은 섬이에요.", "outro": "끝",
                            "tags": ["a", "b", "c", "d", "e"], "sections": [{"h2": "하나", "blocks": blocks},
                                                                          {"h2": "둘", "blocks": [{"text": "x"}]},
                                                                          {"h2": "셋", "blocks": [{"text": "y"}]}]}}

    def run_build(self, blocks, n=5):
        tmp = Path(tempfile.mkdtemp())
        best = make_photos(tmp / "best", 0)
        for i in range(1, n + 1):
            Image.new("RGB", (60, 80), (i * 40, 0, 0)).save(best / f"{i:02d}_P{i:03d}.jpg")
        c = self.content(blocks)
        build_blog.build(c, best, tmp / "out", None, settings())
        ok, rows = check_rules.check("tistory", c, tmp / "out", best, settings())
        return {i: (o, d) for i, o, d in rows}, (tmp / "out" / "post.html").read_text()

    def test_interleaved_passes(self):
        b = [{"text": "a"}, {"photo": "01_P001.jpg"}, {"text": "b"}, {"photo": "02_P002.jpg"}, {"photo": "03_P003.jpg"},
             {"text": "c"}, {"photo": "04_P004.jpg"}, {"text": "d"}, {"photo": "05_P005.jpg"}]
        r, html = self.run_build(b)
        self.assertTrue(r["글·사진 교차 배치"][0])
        self.assertTrue(r["사진 순서 유지"][0])
        self.assertTrue(r["선택 사진 모두 사용"][0])
        self.assertLess(html.index("<p>a</p>"), html.index("images/01.jpg"))
        self.assertFalse(r["본문 분량"][0])  # plog 기준 1500자 미만
        self.assertFalse(r["메인 키워드 횟수 (본문)"][0])

    def test_order_and_runs_fail(self):
        b = [{"text": "a"}, {"photo": "02_P002.jpg"}, {"photo": "01_P001.jpg"}, {"photo": "03_P003.jpg"}]
        r, _ = self.run_build(b)
        self.assertFalse(r["사진 순서 유지"][0])
        self.assertFalse(r["글·사진 교차 배치"][0])
        self.assertFalse(r["선택 사진 모두 사용"][0])

    def test_legacy_format_interleaves(self):
        c = {"photos": ["01.jpg", "02.jpg"], "text": ["가", "나"]}
        self.assertEqual([b[0] for b in build_blog.blocks_of(c)], ["photo", "text", "photo", "text"])


class Shorts(unittest.TestCase):
    def test_tts_normalize(self):
        t = tts_text("둘레길은 2.5km, 1시간쯤. 1~2월 GAUDO 함께해(海)길", {"GAUDO": "가우도"})
        self.assertIn("2점오 킬로미터", t)
        self.assertIn("한 시간", t)
        self.assertIn("1에서 2월", t)
        self.assertIn("가우도", t)
        self.assertNotIn("海", t)

    def test_split_keeps_decimal(self):
        self.assertEqual(split_sentences("길이는 2.5km예요. 좋아요!"), ["길이는 2.5km예요.", "좋아요!"])

    def test_wrap_pages(self):
        f = font_file("Pretendard-Bold.ttf", 64)
        text = "섬 둘레를 도는 함께해길은 약 2.5km로 천천히 걸으면 한 시간에서 한 시간 반 정도 걸린다고 안내판에 적혀 있어요."
        pages = wrap_pages(text, f, 860)
        self.assertTrue(all(len(p) <= 2 for p in pages))
        self.assertEqual(" ".join(" ".join(p) for p in pages).replace(" ", ""), text.replace(" ", ""))
        self.assertEqual(wrap_pages("걸어서만 들어가는 섬, 강진 가우도예요.", f, 860)[0][0], "걸어서만 들어가는 섬,")


class Rules(unittest.TestCase):
    def test_instagram_cards_limit_20(self):
        r = json.loads((SCRIPTS.parent / "references/rules.json").read_text())["instagram"]
        self.assertEqual((r["cards_min"], r["cards_max"]), (1, 20))


if __name__ == "__main__":
    unittest.main()
