# content.json 형식

```json
{
  "id": "C-001",
  "place": "동막해변",
  "region": ["인천", "강화도"],
  "sponsored": false,
  "seo": {
    "main": "강화도 동막해변",
    "sub": ["강화도 가볼만한곳", "인천 겨울 여행", "동막해변 갯벌"],
    "longtail": ["강화도 동막해변 겨울 얼음 바다"]
  },
  "info": {
    "address": "인천 강화군 화도면 …",
    "hours": "상시 개방",
    "fee": "무료",
    "parking": "해변 앞 공영주차장",
    "best_time": "1~2월 한파 뒤",
    "tips": ["바람이 세니 방풍 외투"],
    "sources": ["https://…"],
    "unverified": ["parking"]
  },
  "instagram": {
    "cover_title": "동막해변",
    "cards": [
      {"photo": "01_cover_P012.jpg"},
      {"photo": "02_P003.jpg", "text": "겨울에만 보이는 얼음 갯벌"}
    ],
    "caption": "…",
    "hashtags": ["#강화도동막해변", "#강화도가볼만한곳", "…"]
  },
  "youtube": {
    "title": "강화도 동막해변 겨울에만 볼 수 있는 얼음 바다 #shorts",
    "description": "…",
    "tags": ["강화도", "동막해변", "…"],
    "url": null
  },
  "tistory": {
    "title": "강화도 동막해변 겨울 얼음 바다 여행 (주차·가는 길)",
    "intro": "첫 문단 — 메인 키워드 포함",
    "sections": [
      {"h2": "얼음 바다 풍경", "photos": ["01_P012.jpg", "02_P014.jpg"], "text": ["…"], "alt": "강화도 동막해변 얼음 갯벌"}
    ],
    "tags": ["강화도", "동막해변", "…"],
    "outro": "…"
  }
}
```

- `instagram.cards[].photo`는 `best_insta/` 파일명, `tistory.sections[].photos`는 `best_tistory/` 파일명.
- 카드 첫 장은 표지다. 표지에는 `region`이 `#인천 #강화도`로, `cover_title`이 큰 제목으로 들어간다.
- `info`의 키: `address`(위치), `hours`(운영 시간), `fee`(요금), `parking`(주차), `best_time`(추천 시기), `contact`(문의). 값이 없으면 뺀다.
- 게시 규칙(카드 장수, 해시태그 개수, 제목 길이, 금지 표현 등)은 `rules.json`.
