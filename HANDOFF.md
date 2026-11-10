# HANDOFF — 여행 콘텐츠 3채널 자동화 (AX Campus 4회차 개인 과제)

> 갱신 2026-11-10 · **마감 2026-11-10(화) 23:59 제출 · 2026-11-11(수) 발표·시연**
> 저장소: github.com/jexists/travel-content-maker (비공개, main)

## 1. 사용자와 정한 것
- 답변은 한국어. 사용자는 질문을 줄이길 원함 → 스킬도 **확인 지점 A~E 다섯 번**만 묻는다.
- 과제 기준: Notion「4회차 · 업무 자동화」(jexists 복사본 `41399edccd2e803ca92ff438f97a5608`, 원본 uglysmith1 링크는 접근 불가). 흐름도 표기는「2회차 · AX FDE」5-3·「4회차 · To-be 설계」2-4.
- 역할: 에디터(본인, 실제) · 대표(가상 V, 세 채널 배포 직전 1회). 매니저 역할은 없앴다.
- 흐름: 준비(사진 추리기·검색·브리프) → **A** 브리프+인스타(사진·순서·표지·캡션 한 번에) → **B** 영상 제목·대본(제작 전) → **C** 블로그 제목 5개+내용 → **D** 대표 최종 승인(세 채널 한 번에) → **E** 게시 링크 한 번에.
- 인스타: 20장 이하 전부 / 초과 시 AI 20장, 싫으면 `insta_mine/`에 사용자가 직접. 첫 장만 instpic 표지(왼쪽 여백 0.055, 높이 0.151·0.037), 2장부터 원본.
- 숏폼: OpenAI TTS(`gpt-4o-mini-tts`/marin, 키는 `.env`), 없으면 say. 릴스 트렌드 대본(훅 문구 고정, 한 장면 한 문장, 저장 유도).
- 블로그: plog 프롬프트 원문(`references/prompts/blog_plog.md`), 1500자·키워드 5~7회·제목 25~35자 점검.
- 업로드: Claude in Chrome으로 입력까지, 공유·발행은 사용자. 이번 세션에서는 Chrome 확장이 연결되지 않아 사용자가 직접 올리기로 함.
- 확장 계획(발표 마지막 장): 1단계 tripfolio(AI 코딩 기반 시스템) → 2단계 식당·물건 리뷰 등 다른 주제 → 3단계 생성형 이미지로 컨셉까지 자동 인플루언서(2·3단계 이름 새로). 한계: 사진 선택·대본·블로그 아직 어색, 토큰·시간 절약, 잘 쓴 내용 검증 기준.

- 배포(2026-11-10 추가): 스킬 zip(`dist/travel-content-skill.zip`)을 받아 skills 폴더에 넣는 3단계, Mac·Windows 공통. 첫 실행 때 `scripts/setup.py`가 패키지·ffmpeg(static-ffmpeg)·음성을 준비하고, 오류는 Claude가 SKILL.md "준비 문제 해결" 표대로 처리. Windows 실제 실행은 미검증.
- v5(2026-11-10): 실행 방법 4단계(① 앱 ② 스킬 ③ 목소리 키 `.env` ④ 쓰기), 스킬 zip에 `.env.example` 포함(스킬 폴더 `.env`로 OpenAI TTS 확인), 효과·한계는 사용자 문장대로, 마지막 장은 확장 3단계만.
- v4(2026-11-10): 흐름도 그림만(테두리·빈칸 없음), 표 초록 강조 줄 제거, 구성도 가로판(`architecture_v3`), Python은 첫 실행 때 Claude가 설치(winget·brew·uv, SKILL.md 준비 문제 해결), 첫 실행 장 터미널 모양, 효과·한계 카드.
- 문서·발표는 `_v2`로 새로 만듦(이전 PDF·HTML 보존). 최신은 `_v3`: 목차 3열, 업무 소개 카드, 근거 열 삭제, 개선 설계 비교 행·5칸 흐름, 구성도 크게, "과제 완료" 카드, 실행 방법은 실제 캡처(claude.ai/download·python.org) + 예시 그림(`docs/presentation/illust/`).

## 2. 파일
- 스킬 `.claude/skills/travel-content/` (SKILL.md · references · scripts/tc.py · tests 21개)
- 예제 입력 `examples/가우도/` (GPS 제거 7장) · 배포 zip `dist/` (`tools/package_skill.py`)
- 문서 `docs/00~04`, 흐름도 `docs/diagrams/` (`build_diagrams.py` → drawio·svg, `render_png.sh` → png)
- 발표 `docs/presentation/` (`slides.src.html` → `build.py` → index·analysis·run.html → `export_pdfs.sh` → `docs/자동화업무소개_*.pdf` 3개, 최신은 `slides_v5.src.html` → `build.py _v5` → `*_v5.pdf`, 목차 3열은 v3부터)
- 실행 결과 `work/` (git 제외): C-001(옛 흐름, 3채널 컨펌), C-002(새 흐름, 3채널 대표 승인까지)

## 3. 남은 일
1. C-002 게시 링크 받기(E) → `tc.py publish-all --work work/C-002_가우도 --instagram … --youtube … --tistory …`
2. 제출 폼에 3장 제출(사용자). 구현물 링크(비공개 저장소) 처리는 사용자가 직접.
3. 발표 시연 준비: 발표 HTML `docs/presentation/index.html`(로컬 서버 `python3 -m http.server 8765 --directory docs/presentation`), 시연은 `examples/가우도`로 새 콘텐츠 C-003.

## 4. 주의
- 원본 사진 폴더 수정 금지. 외부 게시 버튼은 사용자가 누름.
- 키(`OPENAI_API_KEY`)는 `.env`에만. 한 번 `.env.example`에 잘못 저장된 적 있음 → 커밋 전 `.env.example` 값이 비었는지 확인.
- 사실(요금·운영 시간)은 출처 + "방문 전 확인".
