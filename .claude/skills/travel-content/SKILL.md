---
name: travel-content
description: 여행 사진 폴더와 여행지 이름을 받아, 100장 넘는 사진을 정리·선별해 best_insta·best_tistory에 복사하고, 여행지 정보·SEO 키워드를 정리한 뒤 대표 기획안 승인 → 인스타 카드뉴스 → 유튜브 숏폼 → 티스토리 글 순서로 만든다. 채널마다 게시 규칙을 자동 점검하고 매니저 컨펌·반려를 받아 버전(v1·v2)을 남기며, 모든 사건을 콘텐츠대장(ledger.xlsx)에 기록한다. "여행 콘텐츠", "사진 정리", "베스트 컷", "카드뉴스", "숏폼", "티스토리 글", "매니저 컨펌", "대표 승인", "반려", "콘텐츠대장"에 사용한다.
---
# 여행 콘텐츠 3채널 제작 (travel-content)

## 목표
사진 폴더 하나로 인스타 → 유튜브 → 티스토리 콘텐츠를 만든다. 사람(에디터·매니저·대표)이 승인한 것만 다음 단계로 간다. 모든 버전과 승인·반려 사유를 콘텐츠대장에 남긴다.

## 역할 나눔
- **AI(이 지침)**: 썸네일을 보고 사진 분류·선택, 여행지 정보 조사(출처 포함), SEO 키워드, 채널별 문구 작성, 반려 사유 반영.
- **스크립트** (`scripts/tc.py` 하위 명령): 사진 필터·썸네일, 복사(EXIF·GPS 제거), 카드 PNG, 숏폼 MP4, 블로그 HTML, 게시 규칙 점검, 순서 강제, 대장 기록.
- **사람**: 에디터(본인) — 사진·여행지 입력, 사진·사실 확인, 업로드. 매니저 — 채널별 컨펌·반려. 대표 — 기획안 승인·반려.
- 매니저·대표는 과제용 **가상 역할**이다. 사용자가 "매니저 컨펌", "매니저 반려: 사유", "대표 승인", "대표 반려: 사유"처럼 말하면 그 역할의 결정으로 기록한다.
- **하지 않는 것**: 승인·컨펌을 대신 결정하기, 사용자가 말하지 않은 사실(영업시간·가격 등)을 확정하기, 사용자 확인 없이 외부에 게시하기, 원본 사진 폴더를 수정하기.

## 실행 환경
- 명령: `"$PROJECT/.venv/bin/python" "$SKILL_DIR/scripts/tc.py" <명령> --work <작업폴더> …`
  - `SKILL_DIR` = 이 SKILL.md가 있는 폴더, `PROJECT` = 프로젝트 루트(`.venv`가 있는 곳). 패키지: `scripts/requirements.txt`(Pillow, openpyxl). 외부 도구: `sips`(macOS, HEIC 변환), `ffmpeg`·`ffprobe`.
- 작업폴더: `work/<콘텐츠ID>_<장소>/` (예: `work/C-001_동막해변/`). 콘텐츠ID는 `work/ledger.xlsx`의 마지막 번호 + 1. 대장은 `work/ledger.xlsx` 하나에 계속 쌓는다.
- 스크립트가 `거절:`로 끝나면 순서·조건 위반이다. 이유를 사용자에게 그대로 전하고 우회하지 않는다.
- **기본 설정** `references/settings.json` (블로그 배치, 인스타 표지 디자인, 숏폼 목소리·속도·자막, 컨펌 방식). 콘텐츠별로 바꿀 값만 작업폴더 `settings.json`에 적는다. 같은 것을 매번 묻지 않는다.
- **채널별 작성 규칙** `references/prompts/`: `common.md`(공통) → `blog.md`·`instagram.md`·`shorts.md`. 해당 채널 문구를 쓰기 직전에 읽는다.
- **승인은 항상 컨펌 카드로**: `tc.py review --work W --stage photos|plan|instagram|youtube|tistory` 출력을 보여 주고 카드의 선택지로 답을 받는다. 규칙은 `references/prompts/confirm.md`.

## 단계

### 1. 시작
사용자에게 **사진 폴더 경로**와 **여행지 이름**을 받는다. 지역 태그 2개(예: `인천`, `강화도`)와 협찬 여부를 묻는다(모르면 협찬 아님). 그다음:
```
tc.py init --work W --id C-001 --place 동막해변
```

### 2. 사진 정리 (먼저 어떤 사진이 있는지 본다)
```
tc.py scan --work W --src <사진폴더> [--keep 40]
```
- 시스템이 흔들림·너무 어두움/밝음·스크린샷·연속 중복을 거르고 후보 최대 40장을 남긴다. 결과: `photos.json`, `contact/candidates_*.jpg`.
- **폴더에 사진이 20장 이하면** 에디터가 이미 고른 사진으로 보고 시스템 필터를 건너뛴다(`photos.json`의 `curated: true`). 이때 선택 단계의 최소 장수도 있는 만큼으로 낮춘다(인스타 최대 6장, 티스토리 최대 5장까지만 요구).
- **썸네일 시트를 Read로 모두 본다.** 사진마다 분류와 제외 여부를 정해 `catalog.json`을 쓴다.
  ```json
  {"P003": {"cat": "풍경", "exclude": false, "reason": "", "note": "얼음 갯벌 전경"},
   "P007": {"cat": "기타", "exclude": true, "reason": "손가락이 렌즈를 가림", "note": ""}}
  ```
  - 분류: `풍경`, `음식`, `메뉴판`, `간판/입구`, `실내`, `인물`, `길/주차`, `기타`.
  - 제외 기준: 손가락·렌즈 가림, 기울어짐이 심함, 모르는 사람 얼굴이 크게 나옴, 차량 번호판·개인정보, 같은 장면 반복.
- `tc.py catalog --work W` → `catalog.md`(분류별 장수, 뺀 사진과 사유, 정보 사진 부족 경고)와 분류별 시트.
- **에디터 확인**: `catalog.md` 요약과 시트를 보여 주고 "뺄 사진·되살릴 사진 번호"만 묻는다. 정보 사진이 없는 분류가 있으면 알려 준다.

### 3. 사진 선택
`selection.json`을 쓴다.
```json
{"insta": {"cover": "P012", "body": ["P003", "P020", "P021", "P025", "P030", "P033"]},
 "tistory": ["P012", "P014", "P015", "P016", "P020", "P026", "P027", "P031", "P035", "P036"],
 "shorts": ["P012", "P003", "P020", "P025", "P031"],
 "origin": {"P012": "editor", "P003": "ai"},
 "reasons": {"P012": "표지: 얼음 갯벌이 화면을 채우고 하늘이 맑음"}}
```
- **인스타(`best_insta`)**: 예뻐 보이는 사진만. 표지 1장 + 본문 5~9장(합계 6~10). 표지는 세로로 잘라도 주제가 살아 있고 아래쪽에 제목을 얹을 여백이 있는 사진.
- **티스토리(`best_tistory`)**: 예쁜 사진 + 정보 사진(간판·입구, 메뉴판·가격표, 길·주차, 실내, 전경) 8~20장. 인스타와 겹쳐도 된다. 첫 사진이 블로그 대표 이미지.
- **영상(`shorts`)**: 인스타·티스토리 선택 안에서 4~7장, 장면 순서대로. 복사하지 않고 best_* 파일을 참조한다. 없으면 인스타 순서.
- **`origin`**: 사용자가 번호로 지정한 사진은 `editor`, AI가 고른 사진은 `ai`. 목록 순서가 곧 사용자의 의도이므로 이후 채널에서 순서를 바꾸지 않는다.
- `tc.py select --work W` → 복사(긴 변 2048px, EXIF·GPS 제거), `contact/selected_insta_*.jpg`, `selected_tistory_*.jpg`.
- `select`는 `usage.md`(사진 사용표: 사진별 블로그·인스타·영상 순서, 고른 쪽, 이유)도 만든다.
- **에디터 확인**: `tc.py review --stage photos` 카드를 보여 준다. 바꾸면 `selection.json`을 고치고 다시 `select`.

### 4. 여행지 정보·SEO → `content.json`
- 정보: 사용자 메모를 먼저 쓰고, 부족하면 웹 검색한다. 출처 URL을 `info.sources`에 넣는다. 영업시간·요금·주차처럼 바뀌기 쉬운 값은 `info.unverified`에 넣는다(블로그에 "방문 전 확인 필요" 표시).
- SEO: `seo.main` = 지역 + 장소(예: `강화도 동막해변`). `seo.sub` = 가볼만한곳·계절·카테고리 조합 3~5개. `seo.longtail` 1~3개. 메인 키워드는 인스타 캡션 또는 해시태그, 유튜브 제목, 티스토리 제목과 첫 문단에 반드시 넣는다. 검색량 데이터는 없으므로 "AI 추천 키워드"라고 말한다.
- 형식은 `references/content_schema.md`. 채널 문구도 이때 초안을 함께 쓴다.

### 5. 대표 기획안 승인
`tc.py review --stage plan` 카드(표지, SEO, 채널 제목 초안, 확인 필요 정보)를 보여 주고 대표 결정을 받는다.
```
tc.py plan --work W --approve
tc.py plan --work W --reject --reason "표지를 바꿔 주세요"
```
반려되면 사유대로 2~4단계를 고친 뒤 다시 승인을 받는다. 승인 뒤에는 사진을 다시 고를 수 없다.

### 6. 채널별 제작 → 점검 → 매니저 컨펌 (인스타 → 유튜브 → 티스토리)
```
tc.py build   --work W --ch instagram        # 카드 JPG + caption.txt + check.md
tc.py confirm --work W --ch instagram        # 매니저 컨펌
tc.py reject  --work W --ch instagram --reason "…"   # 매니저 반려 → 다음 build는 v2
```
- `build` 결과가 `passed: false`면 `check.md`의 ❌ 항목을 고쳐 `content.json`을 수정하고 다시 `build`(같은 버전). 통과 전에는 컨펌을 요청하지 않는다.
- 통과하면 `tc.py review --stage <채널>` 카드와 결과물(이미지·영상·미리보기)을 보여 주고 매니저 결정을 받는다.
- 반려 사유는 `content.json`의 해당 채널 부분에만 반영한다. 이전 버전 폴더는 지우지 않는다.
- 인스타(`prompts/instagram.md`): **첫 장만** instpic 디자인(`#지역 #동네` + 장소명), 2장부터 원본 사진만. 사진 비율 유지.
- 유튜브(`prompts/shorts.md`): `content.youtube.script.scenes`로 대본을 쓴다. 첫 장면은 컨펌된 표지 카드(`"photo": "cover"`). 문장 단위 TTS(macOS say) 길이로 장면 길이가 정해지고, 자막 PNG·줌/팬·장면 전환이 들어간 1080×1920 MP4 + `voice.m4a`·`subtitles.srt`·`script.txt`. 점검이 음성·자막·길이·안전 영역을 확인하고, 발음·전환은 "수동 확인 필요"로 남긴다. (script가 없으면 옛 방식 슬라이드쇼)
- 티스토리(`prompts/blog.md`): `sections[].blocks`로 글→사진→글 순서를 정한다. best_tistory 사진을 순서대로 한 번씩, 연속 2장 이하. 유튜브 링크가 있으면 숏폼을 넣고 없으면 뺀다. 결과 `post.html`(붙여넣기용)·`article.md`·`preview.html`.

### 7. 업로드와 기록
- 컨펌된 채널은 바로 업로드한다. **실제 게시 직전에는 반드시 사용자에게 무엇을 어디에 올리는지 확인받는다.**
- 업로드 방법은 `references/upload.md`. 자동 업로드가 안 되는 채널은 결과 폴더를 그대로 "업로드 패키지"로 안내한다.
- 게시 후 링크를 받아 기록한다: `tc.py publish --work W --ch youtube --url https://…` (유튜브 링크는 `content.youtube.url`에도 저장되어 티스토리 글에 쓰인다).
- 언제든 `tc.py status --work W`로 진행 상황과 **결과물 위치**를 보여 준다. 파일을 실제로 확인해 ✅/❌로 표시하고 `OUTPUTS.md`(클릭 가능한 링크)를 쓴다. ❌인 파일을 완료라고 말하지 않는다.

## 파일
| 파일 | 만드는 쪽 |
| --- | --- |
| `photos.json`, `contact/*.jpg`(확인용 시트), `catalog.md`, `usage.json`·`usage.md`(사진 사용표), `OUTPUTS.md`(결과물 위치) | 스크립트 |
| `catalog.json`, `selection.json`, `content.json` | AI (사용자 확인) |
| `best_insta/`, `best_tistory/` | 스크립트 |
| `<채널>/vN/` 결과물 + `check.md` + `content_snapshot.json` — 인스타 `card_*.jpg`·`caption.txt` / 유튜브 `shorts.mp4`·`voice.m4a`·`subtitles.srt`·`script.txt`·`meta.txt` / 티스토리 `post.html`·`article.md`·`preview.html`·`images/` | 스크립트 |
| `_cache/`(HEIC 변환), `contact/` | 임시·확인용 (게시하지 않음) |
| `state.json`, `../ledger.xlsx` | 스크립트 |
