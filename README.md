# travel-content-maker · 여행 콘텐츠 3채널 자동화

여행 사진 폴더와 장소 이름을 넣으면 **인스타그램 카드뉴스 → 유튜브 숏폼 → 티스토리 블로그**를 만들고, 승인·버전·게시 링크를 콘텐츠대장(`ledger.xlsx`)에 남기는 Claude Code 스킬이다.
AX Campus 1기 4회차 개인 과제(1안 · Claude 스킬 + 로컬 파일) · 제출 2026-11-10 · 발표 2026-11-11.

> 발표·제출 문서(최신 v2): [`전체_v2.pdf`](docs/자동화업무소개_전체_v2.pdf) · [`업무분석_개선설계_v2.pdf`](docs/자동화업무소개_업무분석_개선설계_v2.pdf) · [`실행방법_v2.pdf`](docs/자동화업무소개_실행방법_v2.pdf) · 발표 HTML [`docs/presentation/index_v2.html`](docs/presentation/index_v2.html) (이전 판은 `_v2` 없는 파일)

## 해결하려는 문제
| 문제 | 지금(As-Is) | 이 프로젝트 |
| --- | --- | --- |
| P1 카드 수작업 | 표지를 매번 손으로 | 표지 템플릿(instpic 디자인)으로 첫 장만 자동 생성 |
| P2 반복 작성 | 채널마다 정보를 다시 찾고 씀 | `content.json` 브리프 하나로 3채널 |
| P3 숏폼 못 함 | 편집 부담으로 유튜브 미시작 | 사진 + 대본 → TTS·자막·전환 들어간 MP4 |
| P4·P5 검토·규칙 | 메신저 검토, 눈으로 규칙 확인 | 확인 지점 A~E + `rules.json` 자동 점검 |
| P6 기록 없음 | 링크·이력이 흩어짐 | `ledger.xlsx` 콘텐츠대장 + `OUTPUTS.md` |

## 주요 기능
- **사진**: 20장 이하는 전부, 넘으면 AI가 20장 선택 · GPS·EXIF 제거 복사 · 번호 시트 · 사용자가 고른 폴더(`insta_mine/`)로 교체
- **인스타**: 첫 장만 `#지역 #동네` + 장소명 표지, 2장부터 원본 사진 · 캡션·해시태그 · 카드 1~20장
- **숏폼**: 장면별 대본 → OpenAI TTS(`gpt-4o-mini-tts`, 키 없으면 Mac `say` / Windows 기본 한국어 음성) → 자막 PNG·훅 문구·줌/팬·전환 → 1080×1920 MP4 + `voice.m4a`·`subtitles.srt`
- **블로그**: plog 여행 프롬프트 기준, 글→사진→글 배치, 제목 후보 5개 → `post.html`·`article.md`·`preview.html`
- **관리**: 순서 강제(`state.json`), 채널별 버전 v1·v2, 규칙 자동 점검(`check.md`), 대장 기록(추가만·중복 방지), 결과물 존재 확인(✅/❌)
- **질문은 5번만**: A 브리프+인스타 · B 영상 대본 · C 블로그 제목·내용 · D 대표 최종 승인 · E 게시 링크

## 기술 스택
| 구분 | 사용 | 역할 |
| --- | --- | --- |
| 실행 | Claude Code + 스킬(`.claude/skills/travel-content/SKILL.md`) | 흐름·질문·글쓰기 |
| 스크립트 | Python 3.10+ · Pillow · openpyxl · pillow-heif (`scripts/requirements.txt`) | 이미지·HEIC·카드·대장 |
| 영상 | ffmpeg·ffprobe (static-ffmpeg가 Mac·Windows용을 자동으로 받음) | 숏폼 합성·검사 |
| 음성 | OpenAI `/v1/audio/speech` (선택) · Mac `say` · Windows `System.Speech` | 내레이션 |
| 기타 | Chrome(선택, 업로드 입력) | — |

## 폴더 구조
```
.claude/skills/travel-content/
  SKILL.md                  흐름·확인 지점·멈춤 규칙
  references/               settings.json(기본값) · rules.json(게시 규칙) · upload.md
    prompts/                common · instagram · shorts · blog · blog_plog(원문) · confirm
  설치방법.md               받는 사람용 3단계 (Mac·Windows)
  scripts/setup.py          처음 한 번 준비 (패키지·ffmpeg·음성 확인)
  scripts/tc.py             명령 모음
  scripts/*.py              insta · render_cards · make_shorts · build_blog · check_rules · review · state · ledger · usage …
  assets/fonts/             Pretendard · 나눔손글씨 중학생 · 티몬 몬소리
  tests/test_flow.py        unittest 17개
examples/가우도/             예제 입력 사진 7장 (GPS·EXIF 제거본)
dist/travel-content-skill.zip  배포용 스킬 zip (tools/package_skill.py)
docs/                       분석·설계 문서(00~04) · diagrams/(drawio·svg·png) · presentation/(발표 HTML) · PDF 3개
work/                       실행 결과 (git 제외) — work/C-xxx_장소/, work/ledger.xlsx
.env.example                OPENAI_API_KEY (선택)
```

## 설치 (Mac · Windows, 3단계)
스킬 zip(`dist/travel-content-skill.zip`, `python3 tools/package_skill.py`로 생성) 하나만 주면 된다. zip 안 [`설치방법.md`](.claude/skills/travel-content/설치방법.md)와 같은 내용.

| 단계 | Mac | Windows |
| --- | --- | --- |
| ① 앱 설치 | [Claude 데스크톱 앱](https://claude.ai/download) 로그인(Code 탭) · [Python 3.10+](https://www.python.org/downloads/) | 같음 · Python 설치 시 **Add python.exe to PATH** 체크 |
| ② 스킬 넣기 | zip을 풀어 `~/.claude/skills/travel-content/` | zip을 풀어 `%USERPROFILE%\.claude\skills\travel-content\` |
| ③ 쓰기 | 사진 폴더를 Code 탭에서 열고 "이 사진으로 여행 콘텐츠 만들어줘. 장소는 ○○" | 같음 |

- 처음 실행 때 스킬이 `scripts/setup.py`로 패키지·ffmpeg를 준비한다. 오류가 나면 Claude가 원인을 보고 고친다(SKILL.md "준비 문제 해결"). 사람이 할 일은 Python·앱 설치, 로그인, 관리자 권한 승인뿐.
- 선택: 사진 폴더에 `.env` 파일 → `OPENAI_API_KEY=…` (OpenAI 목소리). 키는 `.env`에만 두고 채팅·zip에 넣지 않는다.
- Claude Code는 유료 계정(Pro·Max·Team·Console)이 필요하다.

## 쓰는 법
확인 지점은 다섯 번이고, 답은 한 메시지로 한다.

| 지점 | 보는 것 | 답 예시 |
| --- | --- | --- |
| A | 순서 시트(1번=표지) · 표지 문구 · 캡션 · 검색 정보 | `이대로` / 고칠 것 / `내가 고를게` |
| B | 영상 제목 · 장면별 대본 | `이대로` / 고칠 문장 |
| C | 블로그 제목 후보 5개 · 미리보기 | `2번 제목으로 이대로` |
| D | 세 채널 체크리스트 | `대표 승인 전부` / `유튜브 반려: 사유` |
| E | 올린 뒤 게시 링크 | 링크 3개 한 번에 |

<details><summary>개발자용 · 이 저장소에서 스크립트 직접 실행</summary>

```bash
python3 .claude/skills/travel-content/scripts/setup.py
tc(){ python3 .claude/skills/travel-content/scripts/tc.py "$@"; }
tc init --work work/C-003_가우도 --id C-003 --place 가우도
tc insta-pick --work work/C-003_가우도 --src examples/가우도
tc insta-use --work work/C-003_가우도 --dir insta_pick
tc insta-cover --work work/C-003_가우도 --photo 3 --region 전남,강진 --title 가우도
tc insta-order --work work/C-003_가우도 --order 3,1,2,4,6,5
# content.json에 캡션·대본·블로그 글 작성 (references/prompts/) 후
tc build --work work/C-003_가우도 --ch instagram --confirm      # youtube · tistory 같은 방식
tc tistory-photos --work work/C-003_가우도 --extra P007
tc ceo --work work/C-003_가우도 --ch all --approve
tc publish-all --work work/C-003_가우도 --instagram URL --youtube URL --tistory URL
tc status --work work/C-003_가우도
```
</details>

## 결과물 확인
- `work/C-xxx_장소/instagram/vN/` card_*.jpg · caption.txt
- `work/C-xxx_장소/youtube/vN/` shorts.mp4 · voice.m4a · subtitles.srt · script.txt · meta.txt
- `work/C-xxx_장소/tistory/vN/` post.html · article.md · preview.html · images/
- 채널 폴더마다 `check.md`(자동 점검) · 작업폴더에 `usage.md`(사진 사용표) · `OUTPUTS.md`(결과물 링크 ✅/❌) · `work/ledger.xlsx`(콘텐츠대장)

## 테스트
```bash
.venv/bin/python -m unittest discover -s .claude/skills/travel-content/tests
```

## 주의사항·문제 해결
| 상황 | 메시지·증상 | 해결 |
| --- | --- | --- |
| 캡션 전에 build | `거절: content.json이 없습니다` | 확인 지점 A부터 |
| 빈 `insta_mine/` | `… 에 사진이 없습니다` | 사진을 넣고 다시 |
| 메인 주소를 링크로 | `거절: 게시물 링크가 아닙니다` | 게시물 주소(`/p/…`, `/shorts/…`) |
| 대표 승인 전 게시 기록 | `거절: 대표 승인 전 채널이 있어…` | D 먼저 |
| OpenAI 키 없음 | check.md에 "예비 엔진" 경고 (Mac·Windows 기본 음성) | 사진 폴더 `.env`에 키 저장 후 다시 build |
| 준비 안 됨 | setup.py ❌ 줄 | → 줄의 해결 방법 (Claude가 먼저 시도) |
| Chrome 확장 미연결 | 업로드 자동 입력 불가 | 업로드 묶음으로 직접 올리기 (공유·발행은 항상 사람) |

- Mac·Windows 공통으로 만들었지만 **Windows 실제 실행은 아직 검증하지 못함**(Mac에서 분기만 테스트). 인스타·유튜브 자동 업로드 API는 설정하지 않았다.
- `gpt-4o-mini-tts`는 OpenAI 문서 기준 2027-01-06 종료 예정.
- 폰트: Pretendard(OFL), 나눔손글씨 중학생·티몬 몬소리는 jexists/instpic에서 복사 — 티몬 몬소리 라이선스 원문 확인 필요.
- 확장 계획(구현 안 됨): 1단계 **tripfolio**(AI 코딩 기반 시스템으로 확장할 때의 서비스 이름) → 2단계 식당·물건 리뷰 등 다른 주제 → 3단계 생성형 이미지로 컨셉까지 만드는 자동 인플루언서 (2·3단계 서비스 이름은 새로 정함).

## 문서
| 문서 | 내용 |
| --- | --- |
| [docs/00_제출문서_구성.md](docs/00_제출문서_구성.md) | 제출물 체크리스트 |
| [docs/01_과제기준_노션정리.md](docs/01_과제기준_노션정리.md) | 과제 기준 |
| [docs/02_요구사항.md](docs/02_요구사항.md) | 요구사항·결정 기록 |
| [docs/03_업무흐름도.md](docs/03_업무흐름도.md) | As-Is·To-Be 프로세스맵 (Draw.io 원본 `docs/diagrams/`) |
| [docs/04_분석설계.md](docs/04_분석설계.md) | 캔버스·자료 목록·문제 카드·RACI |
| [HANDOFF.md](HANDOFF.md) | 다음 작업자용 현재 상태 |

그림 다시 만들기: `python3.12 docs/diagrams/build_diagrams.py && bash docs/diagrams/render_png.sh` · 발표 HTML·PDF: `python3 docs/presentation/build.py && bash docs/presentation/export_pdfs.sh` · 스킬 zip: `python3 tools/package_skill.py`
