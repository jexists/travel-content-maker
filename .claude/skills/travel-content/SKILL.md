---
name: travel-content
description: 여행 사진 폴더와 여행지 이름을 받아 인스타 카드뉴스 → 유튜브 숏폼 → 티스토리 글 순서로 만든다. 인스타 사진은 AI가 20장 이하로 추려 주되 사용자가 원하면 직접 고른 폴더를 쓰고, 표지 추천 → 표지 문구 → 순서 → 캡션을 한 단계씩 사용자에게 확인받는다. 채널마다 게시 규칙을 자동 점검하고, 에디터 컨펌 뒤 배포 직전 대표 승인을 받아 업로드하며, 버전(v1·v2)과 모든 사건을 콘텐츠대장(ledger.xlsx)에 기록한다. "여행 콘텐츠", "인스타 사진", "표지", "카드뉴스", "숏폼", "티스토리 글", "컨펌", "대표 승인", "반려", "콘텐츠대장"에 사용한다.
---
# 여행 콘텐츠 3채널 제작 (travel-content)

## 목표
사진 폴더 하나로 인스타 → 유튜브 → 티스토리 콘텐츠를 만든다. 사용자가 승인한 것만 다음 단계로 가고, 각 채널은 배포 직전에 대표 승인을 받는다. 모든 버전과 승인·반려 사유를 콘텐츠대장에 남긴다.

## 역할 나눔
- **AI(이 지침)**: 사진 추리기(20장 초과일 때), 표지 추천, 여행지 정보 조사(출처 포함), SEO 키워드, 채널별 문구, 반려 사유 반영.
- **스크립트** (`scripts/tc.py` 하위 명령): 사진 필터·번호 시트, 복사(EXIF·GPS 제거), 표지·카드, 숏폼 MP4(TTS·자막), 블로그 HTML, 게시 규칙 점검, 순서 강제, 대장 기록.
- **사람**: 에디터(사용자 본인) — 사진 고르기, 표지·순서·문구 결정, **모든 중간 단계 승인**, 인스타 공유·티스토리 발행 버튼. 대표 — **채널마다 배포 직전** 승인·반려.
- 대표는 과제용 **가상 역할**이다. 사용자가 "대표 승인", "대표 반려: 사유"라고 말하면 대표의 결정으로 기록한다. 그 밖의 "컨펌", "좋아요", "반려: …"는 에디터 결정이다.
- **하지 않는 것**: 승인·컨펌을 대신 결정하기, 사용자가 말하지 않은 사실(영업시간·가격 등)을 확정하기, 공유·발행 버튼 누르기, 원본 사진 폴더를 수정하기.

## 실행 환경
- 명령: `"$PROJECT/.venv/bin/python" "$SKILL_DIR/scripts/tc.py" <명령> --work <작업폴더> …`
  - `SKILL_DIR` = 이 SKILL.md가 있는 폴더, `PROJECT` = 프로젝트 루트(`.venv`가 있는 곳). 패키지: `scripts/requirements.txt`(Pillow, openpyxl). 외부 도구: `sips`(macOS, HEIC 변환), `ffmpeg`·`ffprobe`, `say`(한국어 Yuna).
- 작업폴더: `work/<콘텐츠ID>_<장소>/` (예: `work/C-002_가우도/`). 콘텐츠ID는 `work/ledger.xlsx`의 마지막 번호 + 1. 대장은 `work/ledger.xlsx` 하나에 계속 쌓는다.
- 스크립트가 `거절:`로 끝나면 순서·조건 위반이다. 이유를 사용자에게 그대로 전하고 우회하지 않는다.
- **기본 설정** `references/settings.json` (인스타 표지 디자인, 블로그 배치, 숏폼 목소리·속도·자막). 콘텐츠별로 바꿀 값만 작업폴더 `settings.json`에 적는다. 같은 것을 매번 묻지 않는다.
- **채널별 작성 규칙** `references/prompts/`: `common.md`(공통) → `instagram.md`·`shorts.md`·`blog.md`. 해당 채널 문구를 쓰기 직전에 읽는다.
- **승인은 컨펌 카드로**: `tc.py review --work W --stage photos|instagram|youtube|tistory` 출력을 보여 주고 카드의 선택지로 답을 받는다. 규칙은 `references/prompts/confirm.md`.
- **멈춤 규칙**: 아래 ⏸ 표시에서는 **질문 하나만 하고 답을 기다린다.** 답을 추측해 다음 단계로 넘어가지 않는다. 사용자가 "싫어요/다른 거"라고 하면 그 단계에서 멈추고 그 단계 안에서만 다시 제안한다.

## 단계

### 0. 시작
사진 폴더 경로와 여행지 이름을 받는다(지역 2개·협찬 여부는 표지 단계에서 함께 확인). 그다음:
```
tc.py init --work W --id C-002 --place 가우도
```

### 인스타 (사용자가 사진을 고르는 과정)
1. **사진 추리기**
   - 20장 이하: `tc.py insta-pick --work W --src <사진폴더>` → 전부 `insta_pick/`에 복사(GPS 제거).
   - 20장 초과: `tc.py scan --work W --src <사진폴더>`로 흔들림·중복을 거른 후보 시트를 **Read로 모두 보고** 예쁜 사진 20장을 고른 뒤 `tc.py insta-pick --work W --src <사진폴더> --ids P003,P012,…`.
2. ⏸ **폴더 확인**: `tc.py review --work W --stage photos` 카드(폴더 위치 + 번호 시트)를 보여 주고 "이대로 진행할까요?"
   - 진행 → `tc.py insta-use --work W --dir insta_pick` 후 3번.
   - 싫다 → `tc.py insta-mine --work W` → "`<insta_mine 경로>`에 올릴 사진을 넣고 알려 주세요." ⏸ 사용자가 넣었다고 하면 `tc.py insta-use --work W --dir insta_mine` (0장이면 거절 메시지를 그대로 전한다). 파일 이름순이 기본 순서다.
3. ⏸ **표지 추천**: 확정 번호 시트(`contact/insta_fixed_01.jpg`)를 보고 **1장만** 추천한다(번호 + 한 줄 이유). 기준: 세로로 봐도 주제가 살아 있고, 아래쪽 왼편에 글자를 얹을 단순한 여백이 있다.
   - 마음에 안 든다 → "몇 번으로 할까요? 다른 추천을 원하시면 '다른 거'라고 해 주세요." '다른 거'면 이미 추천한 번호를 빼고 다음 후보 1장.
4. ⏸ **표지 문구**: "위 줄 `#전남 #강진`, 아래 줄 `가우도`로 할까요?"처럼 제안값과 함께 묻는다(지역 2개 = 시·도 + 시·군, 장소명은 짧게).
5. **표지 생성**: `tc.py insta-cover --work W --photo 3 --region 전남,강진 --title 가우도` → `instagram/cover_preview.jpg`를 보여 준다. ⏸ "이 표지로 할까요?" (아니면 3·4번으로)
6. ⏸ **올라가는 순서**: 확정 시트 번호로 순서를 묻는다(표지는 항상 1번, 빼고 싶은 번호는 안 적으면 빠진다). → `tc.py insta-order --work W --order 3,1,2,5,4` → 순서 시트(`contact/insta_order_01.jpg`)를 보여 준다.
7. **캡션**: `references/prompts/instagram.md`대로 캡션·해시태그를 쓴다. 여행지 정보·SEO(`content.json`의 `seo`·`info`, 형식은 `references/content_schema.md`)도 이때 채운다. `tc.py build --work W --ch instagram` — 점검 실패면 고쳐서 다시 build(같은 버전).
8. ⏸ **에디터 컨펌**: `tc.py review --work W --stage instagram` + 카드 이미지·캡션. → `tc.py confirm --work W --ch instagram` / 반려면 `tc.py reject --work W --ch instagram --reason "…"` 후 해당 부분만 고쳐 다시 build(v2).
9. ⏸ **대표 승인(배포 직전)**: 카드 아래 "배포 전 대표 승인" → `tc.py ceo --work W --ch instagram --approve` / `--reject --reason "…"`(반려면 고쳐서 다시 build → 에디터 컨펌 → 대표 승인).
10. **업로드**: `references/upload.md`의 인스타 절차. 로그인된 Chrome(Claude in Chrome)에서 사진을 순서대로 올리고 캡션까지 넣은 뒤 **멈춘다. 공유 버튼은 사용자가 누른다.** 게시 링크를 받으면 `tc.py publish --work W --ch instagram --url …`.

### 유튜브 숏폼
- 사진은 **확정된 인스타 사진과 순서 그대로**. 첫 장면은 표지 카드(`"photo": "cover"`).
- `references/prompts/shorts.md`대로 `content.youtube`(제목·설명·태그·`script.scenes`)를 쓰고 `tc.py build --work W --ch youtube`. 문장 단위 TTS 길이로 장면 길이가 정해지고, 자막·줌/팬·장면 전환이 들어간 1080×1920 MP4 + `voice.m4a`·`subtitles.srt`·`script.txt`가 나온다.
- ⏸ 에디터 컨펌(`review --stage youtube`, 영상 전달) → ⏸ 대표 승인(`ceo`) → 업로드(`upload.md`, 자동 업로드가 안 되면 업로드 패키지 안내) → `publish --url`(유튜브 링크는 티스토리 글에 들어간다).

### 티스토리
- 사진: `tc.py tistory-photos --work W --extra P007,…` — 인스타 사진(순서 그대로) + AI가 원본에서 고른 **정보 사진**(안내판·주차·메뉴판 등)을 뒤에 붙인다. 정보 사진이 없으면 `--extra` 없이.
- `references/prompts/blog.md`대로 `content.tistory`(`sections[].blocks`, 글→사진→글)를 쓰고 `tc.py build --work W --ch tistory`.
- ⏸ 에디터 컨펌 → ⏸ 대표 승인 → 업로드(Chrome으로 글쓰기 화면 채우기, **발행은 사용자**) → `publish --url`.

### 공통
- 바뀌는 정보(영업시간·요금·주차)는 출처와 함께 `info`에, 확인 안 된 값은 `info.unverified`("방문 전 확인").
- 언제든 `tc.py status --work W`로 진행 상황과 **결과물 위치**(✅/❌, `OUTPUTS.md`)를 보여 준다. ❌인 파일을 완료라고 말하지 않는다.
- 옛 흐름(`scan → catalog → select → plan` + 매니저 컨펌)으로 만든 작업폴더(C-001)는 그대로 열리지만, 새 콘텐츠는 위 흐름을 쓴다.

## 파일
| 파일 | 만드는 쪽 |
| --- | --- |
| `insta_pick/`(AI 후보), `insta_mine/`(사용자가 넣는 폴더) | 스크립트 / 사용자 |
| `best_insta/`(확정 사진, 올라가는 순서대로 01…), `best_tistory/`(인스타 + 정보 사진), `insta.json`(사진 출처·표지·순서) | 스크립트 |
| `photos.json`, `contact/*.jpg`(번호 시트), `usage.md`(사진 사용표), `OUTPUTS.md`(결과물 위치) | 스크립트 |
| `content.json`(표지 문구·캡션·대본·글) | AI (사용자 확인) |
| `<채널>/vN/` 결과물 + `check.md` + `content_snapshot.json` — 인스타 `card_*.jpg`·`caption.txt` / 유튜브 `shorts.mp4`·`voice.m4a`·`subtitles.srt`·`script.txt`·`meta.txt` / 티스토리 `post.html`·`article.md`·`preview.html`·`images/` | 스크립트 |
| `instagram/cover_preview.jpg`, `_cache/`, `contact/` | 미리보기·임시 (게시하지 않음) |
| `state.json`, `../ledger.xlsx` | 스크립트 |
