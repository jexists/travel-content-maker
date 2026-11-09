# 여행 콘텐츠 3채널 제작 자동화

AX Campus 4회차 개인 과제 · 제출 2026-11-10 23:59 · 발표 2026-11-11

사진과 메모를 넣으면 **인스타그램 → 유튜브 숏폼 → 티스토리** 순서로 콘텐츠를 만들고, 채널마다 매니저가 컨펌하고 대표가 최종 승인하며, 모든 버전과 승인 기록을 콘텐츠대장에 남긴다. (1안 · Claude 스킬 + 로컬 파일)

> 이어서 작업한다면 먼저 [HANDOFF.md](HANDOFF.md)를 읽는다 (결정 사항·진행 상황·남은 일).

**저장소 이름**: `travel-content-maker` · **서비스 이름(안)**: **tripfolio** — 여행 한 번의 사진 묶음을 카드뉴스·숏폼·블로그 한 세트(폴리오)로 만든다는 뜻. 나중에 서비스로 만들 때 이 이름을 쓴다.

## 스킬 위치와 실행

- 스킬: [`.claude/skills/travel-content/`](.claude/skills/travel-content/SKILL.md) — Claude Code가 자동 인식
  - `references/settings.json` 기본 설정 · `references/rules.json` 게시 규칙 · `references/prompts/` 채널별 작성 규칙
  - `scripts/tc.py` 명령 모음 (`init scan catalog select plan build confirm reject publish status review`)
- 준비: `python3.12 -m venv .venv && .venv/bin/pip install -r .claude/skills/travel-content/scripts/requirements.txt`, `ffmpeg`, macOS `say`(한국어 Yuna)
- 작업 결과(`work/`)는 저장소에 올리지 않는다 (사진 복사본·영상 용량, `.gitignore`).
- 폰트: Pretendard(OFL), 나눔손글씨 중학생·티몬 몬소리(instpic 저장소에서 복사 — 티몬 몬소리 라이선스 원문 확인 필요).

## 최종 제출 문서 구성

**업무명 → 1. 현재 업무 분석 → 2. 개선 설계 → 3. 시스템 → 4. 실행 방법** 순서로 정리해야 한다. 항목별 내용과 진행 상태는 [00 제출 문서 구성](docs/00_제출문서_구성.md) 참고.

## 작업 문서

| 문서 | 내용 | 제출물 |
| --- | --- | --- |
| [00 제출 문서 구성](docs/00_제출문서_구성.md) | 최종 문서 5개 항목, 항목별 체크리스트, 상태 | — |
| [01 과제 기준 — 노션 정리](docs/01_과제기준_노션정리.md) | 과제 안내, 제출물·완료 기준, 수업 작성 기준 | — |
| [02 요구사항](docs/02_요구사항.md) | 내가 말한 요구, 결정 기록, 역할, 기능·비기능 요구, 게시 규칙, 수용 기준 | ② |
| [03 업무 흐름도](docs/03_업무흐름도.md) | As-Is·To-Be 프로세스맵, 시스템 구성도 (Draw.io) | ①② |
| [04 분석·설계 상세](docs/04_분석설계.md) | 캔버스, 자료 목록, 문제 카드, 기준선, 안 선택, RACI·CRUD, 대장 구조, 설계 10항목 | ①② |
| ③ 자동화 구현물 | 구현 후 작성 | ③ |

## 그림

`docs/diagrams/` — `asis` · `tobe` · `architecture` 각각 `.drawio`(편집 원본) · `.png` · `.svg`
다시 만들기: `python3.12 docs/diagrams/build_diagrams.py`
