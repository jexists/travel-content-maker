"""유튜브 숏폼 1080×1920 MP4.

새 방식 (content.youtube.script 가 있을 때):
  대본 장면마다 사진 1장 + 내레이션. 문장 단위 TTS(macOS say) → 실제 길이로 장면 길이를 정하고,
  자막은 Pillow로 PNG를 그려 overlay 한다 (이 ffmpeg에는 drawtext/subtitles 필터가 없음).
  장면 움직임은 1.2초 동안만 부드럽게 줌·팬하고 멈춘다 (blog2shorts 방식), 장면 사이 xfade.
  결과: shorts.mp4, voice.m4a, subtitles.srt, script.txt, meta.txt, timeline.json

옛 방식 (script 가 없을 때): 컨펌된 인스타 카드를 장당 2.5초씩 이어 붙인다 (make_slideshow).
"""
import json
import re
import subprocess
import tempfile
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from common import font_file, open_rgb

W, H, FPS = 1080, 1920, 30
RATE = 24000  # TTS 샘플레이트 (16bit mono)


# ---------------------------------------------------------------- 텍스트

NATIVE = {1: "한", 2: "두", 3: "세", 4: "네", 5: "다섯", 6: "여섯", 7: "일곱", 8: "여덟", 9: "아홉", 10: "열",
          11: "열한", 12: "열두", 20: "스무"}
NATIVE_COUNTERS = "시간|개|명|곳|번|장|살|군데|가지"
UNITS = [("km", "킬로미터"), ("cm", "센티미터"), ("kg", "킬로그램"), ("m", "미터"), ("%", "퍼센트")]
DIGITS = "영일이삼사오육칠팔구"


def split_sentences(text):
    """문장 끝(. ? ! …)에서 나눈다. 숫자 안의 점(2.5)은 나누지 않는다."""
    parts = re.split(r"(?<=[.?!…])(?!\d)\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def tts_text(text, pronounce=None):
    """발음용 텍스트. 자막에는 쓰지 않는다 (자막은 원문)."""
    t = text
    for k, v in (pronounce or {}).items():
        t = t.replace(k, v)
    t = re.sub(r"\(([一-鿿]+)\)", "", t)            # 함께해(海)길 → 함께해길
    t = re.sub(r"(\d)\s*~\s*(\d)", r"\1에서 \2", t)          # 1~2 → 1에서 2
    for u, ko in UNITS:  # 단위를 먼저 (2.5km → 2.5 킬로미터)
        t = re.sub(rf"(\d)\s*{re.escape(u)}(?![A-Za-z])", rf"\1 {ko}", t)
    t = re.sub(r"(\d+)\.(\d+)", lambda m: f"{m.group(1)}점{''.join(DIGITS[int(c)] for c in m.group(2))}", t)  # 2.5 → 2점오
    t = re.sub(rf"\b(\d{{1,2}})\s*({NATIVE_COUNTERS})",
               lambda m: f"{NATIVE.get(int(m.group(1)), m.group(1))} {m.group(2)}" if int(m.group(1)) in NATIVE else m.group(0), t)
    t = t.replace("·", ", ").replace("/", ", ")
    return re.sub(r"\s+", " ", t).strip()


def _balanced_two(text, fnt, max_w, d):
    """두 줄에 들어가면 줄 길이가 비슷하고 쉼표 뒤에서 끊기는 지점을 고른다 ('강진 / 가우도예요' 같은 끊김 방지)."""
    words = text.split()
    best = None
    for k in range(1, len(words)):
        l1, l2 = " ".join(words[:k]), " ".join(words[k:])
        w1, w2 = d.textlength(l1, font=fnt), d.textlength(l2, font=fnt)
        if w1 > max_w or w2 > max_w:
            continue
        cost = abs(w1 - w2) - (max_w * 0.5 if l1.endswith(",") else 0) + (max_w if len(l2.replace(" ", "")) <= 3 else 0)
        if best is None or cost < best[0]:
            best = (cost, [l1, l2])
    return best[1] if best else None


def wrap_pages(text, fnt, max_w, max_lines=2):
    """자막 페이지: 띄어쓰기 단위로 max_w 픽셀 안에 줄을 채우고, max_lines 줄씩 한 페이지."""
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    if d.textlength(text, font=fnt) <= max_w:
        return [[text]]
    if max_lines >= 2:
        two = _balanced_two(text, fnt, max_w, d)
        if two:
            return [two]
    lines, cur = [], ""
    for word in text.split():
        cand = f"{cur} {word}".strip()
        if d.textlength(cand, font=fnt) <= max_w:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = word
            while d.textlength(cur, font=fnt) > max_w:  # 띄어쓰기 없는 긴 단어
                cut = len(cur) - 1
                while cut > 1 and d.textlength(cur[:cut], font=fnt) > max_w:
                    cut -= 1
                lines.append(cur[:cut])
                cur = cur[cut:]
    if cur:
        lines.append(cur)
    # 마지막 줄이 너무 짧으면(2글자 이하) 앞 줄과 균형을 맞춘다
    pages = [lines[i:i + max_lines] for i in range(0, len(lines), max_lines)]
    if len(pages) > 1 and len(pages[-1]) == 1 and len(pages[-1][0]) <= 3 and len(pages[-2]) == max_lines:
        pages[-1].insert(0, pages[-2].pop())
    return pages


def subtitle_png(lines, path, cfg, center_y):
    S = cfg["subtitle"]
    fnt = font_file(S["font"], S["size"])
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lh = round(S["size"] * 1.32)
    top = round(center_y - lh * len(lines) / 2)
    boxes = []
    for i, line in enumerate(lines):
        tw = d.textlength(line, font=fnt)
        x, y = round((W - tw) / 2), top + i * lh
        d.text((x, y), line, font=fnt, fill="white", stroke_width=S["stroke"], stroke_fill=(0, 0, 0, 235))
        boxes.append(d.textbbox((x, y), line, font=fnt, stroke_width=S["stroke"]))
    im.save(path)
    return [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]


# ---------------------------------------------------------------- 오디오

def say(text, out, cfg):
    """macOS say (예비 엔진, OpenAI 키가 없을 때)."""
    subprocess.run(["say", "-v", cfg["voice"], "-r", str(cfg["rate"]), "-o", str(out),
                    "--data-format=LEI16@24000", text], check=True)
    with wave.open(str(out)) as w:
        return w.getnframes() / w.getframerate(), w.readframes(w.getnframes())


WIN_PS = r"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$v = $s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -eq 'ko-KR' } | Select-Object -First 1
if (-not $v) { exit 3 }
$s.SelectVoice($v.VoiceInfo.Name)
$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(24000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
$s.SetOutputToWaveFile($env:TC_OUT, $fmt)
$s.Rate = 1
$s.Speak((Get-Content -Raw -Encoding UTF8 $env:TC_TXT))
$s.Dispose()
"""


def win_speech(text, out, cfg):
    """Windows 기본 음성 (System.Speech, 한국어 음성이 설치돼 있을 때)."""
    import os
    txt = Path(str(out) + ".txt")
    txt.write_text(text, encoding="utf-8")
    env = {**os.environ, "TC_OUT": str(out), "TC_TXT": str(txt)}
    r = subprocess.run(["powershell", "-NoProfile", "-Command", WIN_PS], env=env, capture_output=True, text=True)
    if r.returncode == 3:
        raise SystemExit("Windows에 한국어 음성이 없습니다. OpenAI 키를 작업 폴더 .env에 넣거나 설정 > 시간 및 언어 > 음성에서 한국어 음성을 추가하세요.")
    if r.returncode:
        raise SystemExit(f"Windows 음성 생성 실패: {r.stderr.strip()[:300]}")
    with wave.open(str(out)) as w:
        return w.getnframes() / w.getframerate(), w.readframes(w.getnframes())


def local_engine():
    """OpenAI 키가 없을 때 쓸 기본 음성: macOS say / Windows System.Speech / 없음."""
    import platform
    import shutil
    if shutil.which("say"):
        return "say"
    if platform.system() == "Windows" and shutil.which("powershell"):
        return "windows"
    return None


def openai_key():
    """환경변수 OPENAI_API_KEY, 없으면 프로젝트 루트 .env (git에 안 올라감). 키 값은 출력하지 않는다."""
    import os
    k = os.environ.get("OPENAI_API_KEY")
    if k:
        return k.strip()
    for d in [Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents]:  # 작업 폴더 .env 우선
        env = d / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("OPENAI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def openai_tts(text, cfg, cache_dir):
    """OpenAI /v1/audio/speech → PCM 24kHz 16bit mono. 같은 문장·설정은 캐시해서 다시 과금하지 않는다."""
    import hashlib
    import urllib.error
    import urllib.request
    O = cfg["openai"]
    body = {"model": O["model"], "voice": O["voice"], "input": text, "response_format": "pcm"}
    if O.get("instructions"):
        body["instructions"] = O["instructions"]
    key = hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:24]
    cache = Path(cache_dir) / f"{key}.pcm"
    if cache.exists() and cache.stat().st_size:
        data = cache.read_bytes()
    else:
        req = urllib.request.Request("https://api.openai.com/v1/audio/speech", data=json.dumps(body).encode(),
                                     headers={"Authorization": f"Bearer {openai_key()}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
        except urllib.error.HTTPError as e:
            raise SystemExit(f"OpenAI TTS 실패 ({e.code}): {e.read().decode(errors='ignore')[:300]}")
        if len(data) < RATE // 10:
            raise SystemExit("OpenAI TTS 응답이 비어 있습니다.")
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(data)
    data = data[: len(data) // 2 * 2]
    return len(data) / 2 / RATE, data


def trim_silence(data, keep=0.06, thr=500):
    """문장 앞뒤 무음을 잘라 장면이 늘어지지 않게 한다 (OpenAI 음성은 끝에 0.2~0.8초 무음이 붙음)."""
    import array
    a = array.array("h")
    a.frombytes(data)
    if not a:
        return data
    first = next((i for i, v in enumerate(a) if abs(v) > thr), 0)
    last = len(a) - next((i for i, v in enumerate(reversed(a)) if abs(v) > thr), 0)
    pad = int(RATE * keep)
    a = a[max(0, first - pad):min(len(a), last + pad)]
    return a.tobytes()


def tts(text, out, cfg, cache_dir):
    """설정 engine=openai 이고 키가 있으면 OpenAI, 아니면 say. (사용한 엔진, 길이, PCM)"""
    if cfg.get("engine", "openai") == "openai" and openai_key():
        _, data = openai_tts(text, cfg, cache_dir)
        eng = "openai"
    else:
        eng = local_engine()
        if eng == "say":
            _, data = say(text, out, cfg)
        elif eng == "windows":
            _, data = win_speech(text, out, cfg)
        else:
            raise SystemExit("사용할 음성이 없습니다. 작업 폴더 .env에 OPENAI_API_KEY를 넣어 주세요.")
    data = trim_silence(data)
    return eng, len(data) / 2 / RATE, data


def write_wav(path, pcm):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm)


# ---------------------------------------------------------------- 화면

def frame_image(src, out, contain=False):
    """2배 해상도(2160×3840) 바탕 이미지. 사진은 비율 유지로 꽉 채우고(늘이지 않음),
    contain=True(표지 카드)면 글자가 잘리지 않게 전부 보이게 놓고 뒤를 흐린 사진으로 채운다."""
    im = open_rgb(src)
    big = (W * 2, H * 2)
    bg = ImageOps.fit(im, big, method=Image.LANCZOS)
    if contain:
        bg = bg.filter(ImageFilter.GaussianBlur(40)).point(lambda v: int(v * 0.6))
        fg = im.copy()
        fg.thumbnail(big, Image.LANCZOS)
        if fg.width < big[0]:
            fg = fg.resize((big[0], round(fg.height * big[0] / fg.width)), Image.LANCZOS)
        bg.paste(fg, ((big[0] - fg.width) // 2, (big[1] - fg.height) // 2))
    bg.save(out, quality=92)
    return out


MOTIONS = ["zoom_in", "pan_right", "zoom_out", "pan_left"]


def zoompan(motion, frames, cfg):
    k = max(1, round(cfg["motion_seconds"] * FPS))
    z = cfg["zoom"]
    p = f"min(on/{k},1)"
    s = f"({p}*{p}*(3-2*{p}))"  # smoothstep: 처음 1.2초만 움직이고 멈춤
    if motion == "zoom_in":
        zz, xx = f"1+{z}*{s}", "iw/2-(iw/zoom/2)"
    elif motion == "zoom_out":
        zz, xx = f"{1 + z}-{z}*{s}", "iw/2-(iw/zoom/2)"
    elif motion == "pan_right":
        zz, xx = f"{1 + z}", f"(iw-iw/zoom)*(0.35+0.3*{s})"
    else:
        zz, xx = f"{1 + z}", f"(iw-iw/zoom)*(0.65-0.3*{s})"
    return f"zoompan=z='{zz}':x='{xx}':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}"


def ffmpeg(*args):
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *map(str, args)], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"ffmpeg 실패: {r.stderr.strip()[:600]}")


# ---------------------------------------------------------------- 메인

def hook_png(text, path, cfg):
    """화면 위쪽 훅 문구 (영상 내내 고정, 1~2줄). 반환: bbox"""
    Hk = cfg["hook"]
    size = Hk["size"]
    while size > 48:
        fnt = font_file(Hk["font"], size)
        pages = wrap_pages(text, fnt, Hk["max_width"], 2)
        if len(pages) == 1:
            break
        size -= 4
    lines = pages[0]
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lh = round(size * 1.25)
    top = Hk["top"]
    boxes = []
    for i, line in enumerate(lines):
        tw = d.textlength(line, font=fnt)
        x, y = round((W - tw) / 2), top + i * lh
        d.text((x, y), line, font=fnt, fill="white", stroke_width=Hk["stroke"], stroke_fill=(0, 0, 0, 240))
        boxes.append(d.textbbox((x, y), line, font=fnt, stroke_width=Hk["stroke"]))
    im.save(path)
    return [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]


def make(scenes, out_dir, meta, cfg, hook_text=None, cache_dir=None):
    """scenes: [{"src": 사진 경로, "id": "P003"|"cover", "role", "narration", "subtitle"?, "contain"?}]
    hook_text: 화면 위쪽에 영상 내내 고정되는 훅 문구 (선택)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    S = cfg
    cache_dir = Path(cache_dir or out_dir.parent.parent / "_cache" / "tts")
    engines = set()
    T, lead, tail = S["transition"], 0.15, S["transition"] + S["scene_pad"]
    sub_font = font_file(S["subtitle"]["font"], S["subtitle"]["size"])
    pause = bytes(int(RATE * S["sentence_pause"]) * 2)
    timeline, pcm_all, srt, script = [], bytearray(), [], []
    t0 = 0.0  # 이 장면이 영상에서 시작하는 시각
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        segs = []
        for i, sc in enumerate(scenes):
            last = i == len(scenes) - 1
            sents = split_sentences(sc["narration"])
            subs = split_sentences(sc.get("subtitle") or sc["narration"])
            if len(subs) != len(sents):  # 자막 문장을 따로 쓴 경우 문장 수가 같아야 타이밍을 맞출 수 있다
                raise SystemExit(f"장면 {i + 1}: narration과 subtitle의 문장 수가 다릅니다 ({len(sents)} ≠ {len(subs)})")
            cur, pcm, pages = lead, bytearray(), []
            for j, (sent, sub) in enumerate(zip(sents, subs)):
                spoken = tts_text(sent, S.get("pronounce"))
                eng, dur, data = tts(spoken, tmp / f"s{i}_{j}.wav", S, cache_dir)
                engines.add(eng)
                pcm += data
                ps = wrap_pages(sub, sub_font, S["subtitle"]["max_width"], S["subtitle"]["max_lines"])
                chars = [max(1, sum(len(l.replace(" ", "")) for l in pg)) for pg in ps]
                a = cur
                for pg, c in zip(ps, chars):
                    b = a + dur * c / sum(chars)
                    pages.append({"lines": pg, "start": round(a, 3), "end": round(b, 3)})
                    a = b
                script.append({"scene": i + 1, "id": sc["id"], "role": sc.get("role", "body"), "text": sent,
                               "subtitle": sub, "tts": spoken, "sec": round(dur, 2)})
                cur += dur
                if j < len(sents) - 1:
                    pcm += pause
                    cur += S["sentence_pause"]
            speech_end = cur
            dur_scene = speech_end + (S["end_hold"] + 0.4 if last else tail)
            frames = round(dur_scene * FPS)
            dur_scene = frames / FPS
            # 장면 소리를 전체 트랙의 시작 시각(t0 + lead)에 놓는다
            start_sample = round((t0 + lead) * RATE) * 2
            if len(pcm_all) < start_sample:
                pcm_all += bytes(start_sample - len(pcm_all))
            pcm_all[start_sample:start_sample + len(pcm)] = pcm
            # 자막 PNG: 표지(contain) 장면은 카드 글씨를 가리지 않게 위쪽에
            cy = 330 if sc.get("contain") else S["subtitle"]["center_y"]
            inputs, chain = ["-i", frame_image(sc["src"], tmp / f"bg{i}.jpg", sc.get("contain"))], ""
            label = "[v0]"
            chain = f"[0]{zoompan(MOTIONS[i % len(MOTIONS)], frames, S)},format=yuv420p{label}"
            for k, pg in enumerate(pages):
                png = tmp / f"sub{i}_{k}.png"
                pg["box"] = subtitle_png(pg["lines"], png, S, cy)
                inputs += ["-i", png]
                nxt = f"[v{k + 1}]"
                chain += f";{label}[{k + 1}]overlay=0:0:enable='between(t,{pg['start']},{pg['end']})'{nxt}"
                label = nxt
                srt.append((t0 + pg["start"], t0 + pg["end"], "\n".join(pg["lines"])))
            seg = tmp / f"seg{i}.mp4"
            ffmpeg(*inputs, "-filter_complex", chain, "-map", label, "-frames:v", frames, "-r", FPS,
                   "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", seg)
            segs.append((seg, dur_scene))
            timeline.append({"scene": i + 1, "id": sc["id"], "role": sc.get("role", "body"), "start": round(t0, 3),
                             "duration": round(dur_scene, 3), "speech_end": round(t0 + speech_end, 3),
                             "motion": MOTIONS[i % len(MOTIONS)], "contain": bool(sc.get("contain")), "pages": pages})
            t0 += dur_scene - (0 if last else T)
        total = t0
        # 영상: xfade로 이어 붙이고 끝을 페이드아웃
        args, fc, prev, off = [], "", "[0:v]", 0.0
        for k, (seg, d) in enumerate(segs):
            args += ["-i", seg]
        for k in range(1, len(segs)):
            off += segs[k - 1][1] - T
            nxt = f"[x{k}]"
            fc += f"{prev}[{k}:v]xfade=transition=fade:duration={T}:offset={off:.3f}{nxt};"
            prev = nxt
        hook_box = None
        if hook_text:  # 훅 문구는 영상 내내 위쪽에 고정
            hp = tmp / "hook.png"
            hook_box = hook_png(hook_text, hp, S)
            args += ["-loop", "1", "-i", hp]
            fc += f"{prev}[{len(segs)}:v]overlay=0:0:shortest=1[hk];"
            prev = "[hk]"
        fc += f"{prev}fade=t=out:st={total - 0.5:.3f}:d=0.5,format=yuv420p[vout]"
        voice_wav = tmp / "voice.wav"
        pcm_all += bytes(max(0, round(total * RATE) * 2 - len(pcm_all)))
        write_wav(voice_wav, bytes(pcm_all[:round(total * RATE) * 2]))
        ffmpeg("-i", voice_wav, "-af", "afade=t=out:st=%.3f:d=0.4" % (total - 0.4), "-c:a", "aac", "-b:a", "160k",
               out_dir / "voice.m4a")
        out = out_dir / "shorts.mp4"
        a_idx = len(segs) + (1 if hook_text else 0)
        ffmpeg(*args, "-i", out_dir / "voice.m4a", "-filter_complex", fc, "-map", "[vout]", "-map", f"{a_idx}:a",
               "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-r", FPS, "-c:a", "copy",
               "-t", f"{total:.3f}", "-movflags", "+faststart", out)

    def ts(x):
        ms = round(x * 1000)
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    (out_dir / "subtitles.srt").write_text(
        "\n".join(f"{n}\n{ts(a)} --> {ts(b)}\n{t}\n" for n, (a, b, t) in enumerate(srt, 1)), encoding="utf-8")
    lines = [f"# 숏폼 대본 — 총 {total:.1f}초", ""]
    for sc_t in timeline:
        lines.append(f"## 장면 {sc_t['scene']} · {sc_t['role']} · 사진 {sc_t['id']} · {sc_t['start']:.1f}~{sc_t['start'] + sc_t['duration']:.1f}초 · {sc_t['motion']}")
        for s in [x for x in script if x["scene"] == sc_t["scene"]]:
            lines.append(f"- 내레이션: {s['text']}")
            if s["subtitle"] != s["text"]:
                lines.append(f"  - 자막: {s['subtitle']}")
            if s["tts"] != s["text"]:
                lines.append(f"  - TTS 발음: {s['tts']}")
        lines.append("")
    engine = next(iter(engines)) if len(engines) == 1 else "mixed"
    voice = {"openai": f"OpenAI {cfg['openai']['model']} / {cfg['openai']['voice']}",
             "say": f"macOS say / {cfg['voice']} (속도 {cfg['rate']})",
             "windows": "Windows 기본 한국어 음성"}.get(engine, "여러 엔진")
    if hook_text:
        lines.insert(1, f"훅 문구(화면 위 고정): {hook_text}")
    lines.insert(1, f"목소리: {voice}")
    (out_dir / "script.txt").write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "timeline.json").write_text(json.dumps({"total": round(total, 3), "engine": engine, "voice": voice,
                                                       "rate": cfg["rate"], "hook": hook_text, "hook_box": hook_box,
                                                       "scenes": timeline}, ensure_ascii=False, indent=2), encoding="utf-8")
    write_meta(out_dir, meta)
    return out


def write_meta(out_dir, meta):
    (Path(out_dir) / "meta.txt").write_text(
        f"제목: {meta['title']}\n\n설명:\n{meta['description']}\n\n태그: {', '.join(meta['tags'])}\n", encoding="utf-8")


def make_slideshow(card_files, out_dir, meta, sec=2.5, fade=0.3):
    """옛 방식: 인스타 카드를 장당 2.5초씩 (대본이 없을 때만)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        segs = []
        for i, card in enumerate(card_files):
            seg = tmp / f"seg_{i:02d}.mp4"
            vf = (f"[0]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
                  f"boxblur=30:5,eq=brightness=-0.1[bg];"
                  f"[0]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,"
                  f"fade=t=in:st=0:d={fade},fade=t=out:st={sec - fade}:d={fade},format=yuv420p")
            ffmpeg("-loop", "1", "-t", sec, "-i", card, "-filter_complex", vf, "-r", "30", "-c:v", "libx264",
                   "-preset", "veryfast", "-crf", "20", seg)
            segs.append(seg)
        lst = tmp / "list.txt"
        lst.write_text("".join(f"file '{s}'\n" for s in segs))
        out = out_dir / "shorts.mp4"
        ffmpeg("-f", "concat", "-safe", "0", "-i", lst, "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
               "-c:v", "copy", "-c:a", "aac", "-movflags", "+faststart", out)
    write_meta(out_dir, meta)
    return out
