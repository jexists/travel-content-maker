"""처음 한 번 실행하는 준비 스크립트 (Mac·Windows 공통).

    python setup.py          # Windows: python 또는 py -3 / Mac: python3

1. 필요한 패키지 설치 (Pillow, openpyxl, pillow-heif, static-ffmpeg) — 이미 있으면 건너뜀
2. ffmpeg·ffprobe 준비 (없으면 static-ffmpeg가 자동으로 받음)
3. 폰트·음성(OpenAI 키 / Mac say / Windows 한국어 음성) 확인
실패한 항목은 "원인 · 해결" 한 줄을 출력한다. Claude는 그 줄을 보고 이어서 처리한다.
"""
import importlib
import importlib.util
import platform
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKGS = {"PIL": "Pillow>=10", "openpyxl": "openpyxl>=3.1", "pillow_heif": "pillow-heif>=0.16", "static_ffmpeg": "static-ffmpeg>=2.5"}
rows = []


def row(ok, item, detail, fix=""):
    rows.append((ok, item, detail, fix))


def pip_install(specs):
    base = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-q"]
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    r = subprocess.run(base + ([] if in_venv else ["--user"]) + specs, capture_output=True, text=True)
    if r.returncode and "externally-managed" in (r.stderr + r.stdout):
        r = subprocess.run(base + ["--user", "--break-system-packages"] + specs, capture_output=True, text=True)
    return r


def main():
    if sys.version_info < (3, 10):
        row(False, "Python", platform.python_version(), "Python 3.10 이상 설치 (python.org)")
    else:
        row(True, "Python", f"{platform.python_version()} · {platform.system()}")

    missing = [spec for mod, spec in PKGS.items() if importlib.util.find_spec(mod) is None]
    if missing:
        r = pip_install(missing)
        importlib.invalidate_caches()
        still = [spec for mod, spec in PKGS.items() if importlib.util.find_spec(mod) is None]
        if still:
            err = (r.stderr or r.stdout).strip().splitlines()[-1:] or [""]
            row(False, "패키지", ", ".join(still) + f" 설치 실패 — {err[0][:120]}",
                f'"{sys.executable}" -m venv "{HERE.parent / ".venv"}" 로 가상환경을 만들고 그 python으로 다시 실행')
        else:
            row(True, "패키지", "설치함: " + ", ".join(missing))
    else:
        row(True, "패키지", "이미 있음")

    sys.path.insert(0, str(HERE))
    try:
        from common import FONT_DIR, ensure_tools
        ok = ensure_tools()
        ff = shutil.which("ffmpeg")
        row(ok, "ffmpeg·ffprobe", ff or "없음",
            "" if ok else ("brew install ffmpeg" if platform.system() == "Darwin" else "winget install Gyan.FFmpeg") + " (자동 다운로드가 막힌 경우)")
        fonts = sorted(p.name for p in FONT_DIR.glob("*.ttf"))
        row(len(fonts) >= 4, "폰트", f"{len(fonts)}개", "" if len(fonts) >= 4 else "스킬 zip을 다시 풀기 (assets/fonts 누락)")
        from make_shorts import local_engine, openai_key
        key, local = bool(openai_key()), local_engine()
        if key:
            row(True, "음성", "OpenAI TTS (키 있음)")
        elif local:
            row(True, "음성", {"say": "macOS 기본 음성 (OpenAI 키 없음)", "windows": "Windows 기본 음성 (한국어 음성 필요)"}[local],
                "괜찮은 목소리: 스킬 폴더의 .env.example을 .env로 복사하고 OPENAI_API_KEY=… 넣기")
        else:
            row(False, "음성", "사용할 음성 없음", "스킬 폴더의 .env.example을 .env로 복사하고 OPENAI_API_KEY=… 넣기")
    except Exception as e:  # 패키지 설치 실패 등
        row(False, "확인", f"{type(e).__name__}: {e}"[:160], "위 패키지 문제를 먼저 해결")

    print("travel-content 준비 확인")
    for ok, item, detail, fix in rows:
        print(f"{'✅' if ok else '❌'} {item}: {detail}" + (f"\n   → {fix}" if fix else ""))
    bad = [r for r in rows if not r[0]]
    print("\n준비 완료" if not bad else f"\n준비 안 됨 {len(bad)}건 — 위 → 줄을 따라 해결")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
