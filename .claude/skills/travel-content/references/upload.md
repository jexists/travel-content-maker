# 업로드 방법

공통: **대표 승인(`approved`) 뒤에만** 올린다. Claude는 입력까지만 하고, 공유·발행 버튼은 사용자가 누른다. 게시 링크를 받으면 `tc.py publish --ch … --url …`.
실패하면(로그인 안 됨, 버튼·입력칸을 못 찾음) 성공했다고 말하지 않는다. 결과 폴더 경로를 "업로드 패키지"로 알려 주고 수동 업로드를 안내한다.

## 인스타그램 (API 미설정 → 로그인된 Chrome)
1. Claude in Chrome 도구를 한 번에 불러온다(tabs_context·tabs_create·navigate·find·computer·file_upload·read_page). 작업 탭은 끝까지 탭 그룹 안에 둔다(첫 탭을 닫으면 그룹이 사라짐).
2. `https://www.instagram.com/` → 로그인 확인(안 되어 있으면 사용자에게 로그인을 부탁하고 멈춘다).
3. 왼쪽 메뉴 **만들기(+)** → **게시물** → "컴퓨터에서 선택"의 파일 입력에 `instagram/vN/card_01.jpg … card_NN.jpg`를 **번호 순서대로 한 번에** 올린다 (`file_upload`).
4. 자르기 화면: 비율 버튼에서 **원본**을 고른다(카드가 원본 비율). 순서가 맞는지 확인 → 다음 → (필터 없음) 다음.
5. 캡션 칸에 `instagram/vN/caption.txt` 내용을 그대로 입력.
6. **여기서 멈춘다.** 화면을 캡처해 사용자에게 보여 주고 "공유 버튼을 눌러 주세요"라고 안내한다.
7. 사용자가 공유 후 게시물 링크(`https://www.instagram.com/p/…`)를 주면 `tc.py publish --work W --ch instagram --url …`.

## 유튜브 숏폼
- Data API v3 + OAuth(`client_secret.json`)가 없으면 자동 업로드하지 않는다. `youtube/vN/`의 `shorts.mp4`와 `meta.txt`(제목·설명·태그)를 업로드 패키지로 안내한다.
- 사용자가 원하면 Chrome으로 YouTube Studio 업로드 화면에 파일·제목·설명까지 넣고, **게시는 사용자**.

## 티스토리
- Open API 종료 → Chrome으로 `https://<블로그>.tistory.com/manage/newpost`에서 제목·본문(`post.html`)·사진·태그를 채운다. **발행은 사용자**.
