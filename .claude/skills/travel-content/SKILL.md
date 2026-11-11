---
name: travel-content
description: 여행 사진 폴더와 여행지 이름을 받아 인스타 카드뉴스 → 유튜브 숏폼 → 티스토리 글을 만든다. 처음에 사진·검색 정보·사용자 메모로 브리프 하나를 정리하고, 사용자에게는 확인 지점 다섯 번(A 브리프+인스타, B 영상 대본, C 블로그 제목·내용, D 대표 최종 승인, E 링크)만 묻는다. 채널마다 게시 규칙을 자동 점검하고, 버전(v1·v2)과 모든 사건을 콘텐츠대장(ledger.xlsx)에 기록한다. "여행 콘텐츠", "인스타 사진", "표지", "카드뉴스", "숏폼", "티스토리 글", "컨펌", "대표 승인", "반려", "콘텐츠대장"에 사용한다.
---
# 여행 콘텐츠 3채널 제작 (travel-content)

## 목표
사진 폴더 하나로 인스타 → 유튜브 → 티스토리 콘텐츠를 만든다. 사용자에게 묻는 것은 **확인 지점 A~E 다섯 번뿐**이다. 그 사이의 결정은 기본값(`settings.json`)과 브리프로 처리하고, 점검 실패는 묻지 않고 고친다. 모든 버전과 승인·반려 사유를 콘텐츠대장에 남긴다.

## 역할 나눔
- **AI(이 지침)**: 사진 추리기(20장 초과일 때), 표지·순서 제안, 여행지 정보 검색(출처 포함), 브리프 정리, SEO 키워드, 채널별 문구, 반려 사유 반영.
- **스크립트** (`scripts/tc.py`): 사진 필터·번호 시트, 복사(EXIF·GPS 제거), 표지·카드, 숏폼 MP4(TTS·자막), 블로그 HTML, 게시 규칙 점검, 순서 강제, 대장 기록, 확인 지점 카드.
- **사람**: 에디터(사용자 본인) — A·B·C 확인(= 에디터 컨펌), 인스타 공유·티스토리 발행·유튜브 업로드 버튼, E 링크. 대표(과제용 가상 역할) — D에서 세 채널을 한 번에 승인·반려.
- 사용자가 "대표 승인 …", "대표 반려: …"라고 말한 것만 대표 결정이다. 나머지 승인 말은 에디터 결정이다.
- **하지 않는 것**: 확인 지점 밖에서 묻기, 승인을 대신 결정하기, 브리프에 없는 사실·경험 쓰기, 공유·발행 버튼 누르기, 원본 사진 폴더 수정.

## 실행 환경
- Mac·Windows 공통. `SKILL_DIR` = 이 파일이 있는 폴더(보통 `~/.claude/skills/travel-content`, Windows `%USERPROFILE%\.claude\skills\travel-content`).
- **파이썬**: Mac `python3`, Windows `python`(없으면 `py -3`). 스킬 폴더에 `.venv`가 있으면 그 안의 python(Mac `.venv/bin/python`, Windows `.venv\Scripts\python.exe`)을 쓴다. 아래 `tc.py`는 `<python> "<SKILL_DIR>/scripts/tc.py"`의 줄임.
- **처음 한 번 준비**: `<python> "<SKILL_DIR>/scripts/setup.py"` — 패키지(Pillow·openpyxl·pillow-heif·static-ffmpeg) 설치, ffmpeg·ffprobe 자동 준비, 폰트·음성 확인. ❌ 줄이 나오면 아래 "준비 문제 해결"대로 Claude가 먼저 고친다. 사용자에게 묻지 않는다(사람이 해야 하는 것만 부탁).
- 작업폴더: **Claude Code를 연 폴더**의 `work/<콘텐츠ID>_<장소>/`. 콘텐츠ID = `work/ledger.xlsx` 마지막 번호 + 1.
- 목소리: `.env`의 `OPENAI_API_KEY`(작업 폴더 → 상위 폴더 → 스킬 폴더 순으로 찾음)가 있으면 OpenAI TTS, 없으면 Mac `say` / Windows 기본 한국어 음성. 키가 없으면 B(영상 대본) 전에 한 줄로 알린다: "스킬 폴더의 `.env.example`을 `.env`로 복사해 키를 넣으면 OpenAI 목소리" — 키를 채팅으로 받지 않는다.

### 준비 문제 해결 (setup.py ❌ 줄)
| 증상 | Claude가 먼저 할 일 | 사용자에게 부탁 |
| --- | --- | --- |
| `python`을 못 찾음 · 3.10 미만 | `python3`·`py -3`로 다시 → 없으면 **Claude가 설치**: Windows `winget install -e --id Python.Python.3.12 --scope user` · Mac `brew install python@3.12`(brew 있을 때) · 둘 다 안 되면 uv(Mac `curl -LsSf https://astral.sh/uv/install.sh \| sh`, Windows `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"`) → `uv venv --seed -p 3.12 "<SKILL_DIR>/.venv"` 만들고 그 python으로 setup.py | 명령 실행 승인 (원하면 python.org에서 직접 설치, Windows는 "Add python.exe to PATH" 체크) |
| 패키지 설치 실패(권한·externally-managed) | 스킬 폴더에 `.venv` 만들고 그 python으로 setup.py 다시 | — |
| ffmpeg 없음(자동 다운로드 막힘) | Mac `brew install ffmpeg` / Windows `winget install Gyan.FFmpeg` 실행 제안 | 관리자 권한 승인 |
| 음성 없음 | Windows 설정 > 시간 및 언어 > 음성에서 한국어 음성 추가 안내, 또는 OpenAI 키 | `.env`에 키 넣기 |
| 그 밖 | 오류 원문을 보여 주고 원인·해결 한 줄 | — |
- 스크립트가 `거절:`로 끝나면 순서·조건 위반이다. 이유를 그대로 전하고 우회하지 않는다.
- 기본값 `references/settings.json`(표지 디자인, 블로그 배치, 목소리·자막, 숏폼 화면 배치 `shorts.layout`) — 묻지 않는다. 채널 문구 규칙 `references/prompts/`(`common.md` → `instagram.md`·`shorts.md`·`blog.md`·`blog_plog.md`), 확인 지점 규칙 `references/prompts/confirm.md`.
- **토큰·시간 절약**: 확인 지점마다 카드 1개(`tc.py review --stage …` 출력) + 이미지 1장만 보낸다. 중간 진행은 한 줄로만 알리고, 같은 내용을 다시 설명하지 않는다.

## 흐름

### 준비 (묻지 않음)
1. `tc.py init --work W --id C-003 --place <장소>`
2. 사진: 20장 이하 → `tc.py insta-pick --work W --src <폴더>`. 20장 초과 → `tc.py scan …` 후보 시트를 Read로 보고 20장을 골라 `tc.py insta-pick … --ids P003,…`.
3. `tc.py insta-use --work W --dir insta_pick` → 확정 시트(`contact/insta_fixed_01.jpg`)를 보고 표지 1장·올라가는 순서를 정한다(정보 사진은 뒤로, 글씨 많은 안내판은 인스타에서 빼고 티스토리 정보 사진으로).
4. 여행지 정보를 웹 검색(출처 URL), 사진 속 안내판·촬영 시각을 읽어 `content.json`의 `brief`·`info`·`seo`·`region`을 채운다. 사진·검색으로 알 수 없는데 글에 필요한 것(예: 누구와 갔는지, 꼭 넣고 싶은 경험)은 `brief.questions`에 1~3개만.
5. `tc.py insta-cover --photo N --region 전남,강진 --title <장소명>` → `tc.py insta-order --order …` (A 시트 `contact/A_insta_01.jpg` 생성). `instagram.md`대로 캡션·해시태그를 쓴다.

### A. 브리프 + 인스타 ⏸
- `tc.py review --stage brief` 카드 + `contact/A_insta_01.jpg` 1장을 보낸다.
- 답 처리 (한 메시지 안의 요청을 모두 반영):
  - `이대로` → `tc.py build --ch instagram --confirm`
  - 수정(표지 번호·순서·문구·캡션·메모) → 해당 명령·문구만 고친 뒤 build --confirm. 메모는 `brief.memo`에 넣고 모든 채널 문구에 반영. **다시 묻지 않는다**(바뀐 것이 크면 B 카드 앞에 한 줄로 알린다).
  - `내가 고를게` → `tc.py insta-mine` 경로만 알려 주고 ⏸. "넣었어"면 `insta-use --dir insta_mine` 후 준비 3·5를 다시 해서 A 카드를 한 번 더(그 밖의 항목은 유지).

### B. 영상 제목·대본 ⏸ (제작 전)
- `shorts.md`대로 `content.youtube`(제목·설명·태그·`script.hook_text`·`scenes`)를 쓴다. 사진·순서 = 확정된 인스타 순서, 첫 장면 `"cover"`. 훅 문구는 두 줄 명사형(20자 이내), 첫 문장은 구체적인 약속, 보여 주기 전에 `shorts.md` 자체 점검 6가지.
- `tc.py review --stage script` 카드만 보낸다(이미지 없음).
- `이대로`/수정 반영 → `tc.py build --ch youtube --confirm`. 대본 글 규칙(해요체·문장 35자·훅 길이 등)은 영상 만들기 전에 검사해 TTS 없이 멈추고, 영상 점검 실패(길이 초과 등)와 함께 대본을 고쳐 다시 build.

### C. 블로그 제목 5개 + 내용 ⏸
- `tc.py tistory-photos --extra <정보 사진 ID>` → `blog.md`·`blog_plog.md`대로 `content.tistory`(제목 후보 5개, `blocks`) → `tc.py build --ch tistory`(컨펌 없이) → 점검 통과까지 고친다.
- `tc.py review --stage blog` 카드 + `preview.html` 캡처 1장(헤드리스 Chrome, 3단으로 나눠 1장).
- `N번 제목으로 이대로` → 제목이 바뀌면 `title` 수정 후 다시 build, 그다음 `tc.py confirm --ch tistory`. 문단 수정도 같은 방식.

### D. 대표 최종 승인 ⏸ (세 채널 한 번에)
- `tc.py review --stage final` 체크리스트(채널·버전·점검·에디터 컨펌·대표 승인·링크·결과물)를 보낸다.
- `대표 승인 전부` → `tc.py ceo --ch all --approve`. 일부 반려 → 승인 채널은 `ceo --ch instagram,tistory --approve`, 반려 채널은 `ceo --ch youtube --reject --reason "…"` → 해당 부분만 고쳐 다시 build --confirm → 다음 D 카드에서 그 채널만 다시 묻는다.
- 승인한 채널의 업로드 묶음을 한 메시지로 안내(`references/upload.md`). Chrome이 연결돼 있으면 입력까지만, 공유·발행은 사용자.

### E. 링크 한 번에 ⏸
- 사용자가 올린 뒤 링크를 한 메시지로 준다 → `tc.py publish-all --instagram … --youtube … --tistory …`(준 것만, 메인 주소는 거절). 마지막에 `review --stage final`로 체크리스트를 한 번 보여 주고 끝.
- 유튜브 링크를 블로그에 넣고 싶다고 하면 티스토리 v2(build --confirm) → 그 채널만 D·E.

### 공통
- 바뀌는 정보(영업시간·요금·주차)는 출처와 함께 `info`, 확인 안 된 값은 `info.unverified`("방문 전 확인").
- `tc.py status --work W`로 결과물 위치(✅/❌, `OUTPUTS.md`). ❌인 파일을 완료라고 말하지 않는다.
- 옛 흐름(scan → catalog → select → plan, 매니저 컨펌, 단계별 질문)으로 만든 작업폴더도 열리지만 새 콘텐츠는 위 흐름을 쓴다.

## 파일
| 파일 | 만드는 쪽 |
| --- | --- |
| `insta_pick/`(AI 후보), `insta_mine/`(사용자가 넣는 폴더) | 스크립트 / 사용자 |
| `best_insta/`(확정 사진, 올라가는 순서), `best_tistory/`(인스타 + 정보 사진), `insta.json` | 스크립트 |
| `contact/A_insta_01.jpg`(확인 지점 A 시트), `contact/*.jpg`, `usage.md`, `OUTPUTS.md` | 스크립트 |
| `content.json`(`brief`·캡션·대본·글) | AI (사용자 확인) |
| `<채널>/vN/` 결과물 + `check.md` + `content_snapshot.json` | 스크립트 |
| `instagram/cover_preview.jpg`, `_cache/`(HEIC·TTS) | 미리보기·임시 |
| `state.json`, `../ledger.xlsx` | 스크립트 |
