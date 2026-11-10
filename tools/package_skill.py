"""스킬 배포 zip 만들기 — 받는 사람은 풀어서 ~/.claude/skills/ (Windows: %USERPROFILE%\\.claude\\skills\\)에 넣으면 된다.

python3 tools/package_skill.py   →  dist/travel-content-skill.zip
"""
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / ".claude/skills/travel-content"
OUT = ROOT / "dist/travel-content-skill.zip"
SKIP_DIRS = {"__pycache__", ".venv", ".pytest_cache"}
SKIP_FILES = {".env", ".DS_Store"}
SECRET = re.compile(rb"sk-[A-Za-z0-9_-]{16,}")


def main():
    files = [p for p in sorted(SKILL.rglob("*")) if p.is_file()
             and not (set(p.relative_to(SKILL).parts) & SKIP_DIRS) and p.name not in SKIP_FILES]
    leaks = [str(p.relative_to(SKILL)) for p in files if (p.suffix in {".py", ".md", ".json", ".txt"} or p.name == ".env.example") and SECRET.search(p.read_bytes())]
    if leaks:
        sys.exit(f"키처럼 보이는 문자열이 있어 중단: {leaks}")
    OUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, Path("travel-content") / p.relative_to(SKILL))
    print(f"{OUT} · 파일 {len(files)}개 · {OUT.stat().st_size / 1e6:.1f}MB")


if __name__ == "__main__":
    main()
