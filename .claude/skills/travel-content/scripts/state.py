"""진행 상태 state.json — 단계 순서를 강제하고 버전을 관리한다."""
from common import CHANNELS, CHANNEL_KO, load, now, save, work_paths
import ledger

PHOTO_STEPS = ["none", "scanned", "cataloged", "selected"]


class Refused(SystemExit):
    pass


def init(work, content_id, place):
    p = work_paths(work)
    st = load(p["state"])
    if st:
        return st
    st = {"id": content_id, "place": place, "created": now(), "photos": "none",
          "plan": {"status": "none"},
          "channels": {c: {"version": 0, "status": "none", "url": None} for c in CHANNELS}}
    save(p["state"], st)
    ledger.append(p["ledger"], content_id, place, "all", 0, "작업 시작", "에디터")
    return st


def get(work):
    st = load(work_paths(work)["state"])
    if not st:
        raise Refused("state.json이 없습니다. 먼저 init을 실행하세요.")
    return st


def put(work, st):
    save(work_paths(work)["state"], st)


def log(work, st, channel, version, event, actor, memo="", result="", link=""):
    ledger.append(work_paths(work)["ledger"], st["id"], st["place"], channel, version, event, actor, memo, result, link)


def photos_step(work, step, actor="시스템", memo=""):
    st = get(work)
    if PHOTO_STEPS.index(step) > PHOTO_STEPS.index(st["photos"]) + 1:
        raise Refused(f"사진 단계 순서 위반: 현재 '{st['photos']}' → '{step}' 불가")
    if st["plan"]["status"] == "approved" and step != st["photos"]:
        raise Refused("대표 기획안 승인 뒤에는 사진을 다시 정리·선택할 수 없습니다. 새 콘텐츠ID로 시작하세요.")
    st["photos"] = step
    put(work, st)
    log(work, st, "photos", 0, {"scanned": "사진 스캔", "cataloged": "사진 정리", "selected": "사진 선택"}[step], actor, memo)


def plan(work, approve, actor="대표", reason=""):
    st = get(work)
    if st["photos"] != "selected":
        raise Refused("사진 선택이 끝나야 기획안을 승인할 수 있습니다.")
    if not load(work_paths(work)["content"]):
        raise Refused("content.json(여행지 정보·SEO)이 없습니다.")
    st["plan"] = {"status": "approved" if approve else "rejected", "by": actor, "at": now(), "reason": reason}
    put(work, st)
    log(work, st, "plan", 0, "대표 승인" if approve else "대표 반려", actor, reason)


def start_build(work, ch):
    """생성 전에 순서를 확인하고 이번 버전 번호를 돌려준다."""
    st = get(work)
    if st["plan"]["status"] != "approved":
        raise Refused("대표 기획안 승인 전에는 채널 콘텐츠를 만들 수 없습니다.")
    i = CHANNELS.index(ch)
    if i > 0:
        prev = st["channels"][CHANNELS[i - 1]]["status"]
        if prev not in ("confirmed", "published"):
            raise Refused(f"{CHANNEL_KO[CHANNELS[i - 1]]} 컨펌 전에는 {CHANNEL_KO[ch]}를 만들 수 없습니다 (현재: {prev}).")
    c = st["channels"][ch]
    if c["status"] in ("confirmed", "published"):
        raise Refused(f"{CHANNEL_KO[ch]}는 이미 컨펌되었습니다. 다시 만들려면 반려를 먼저 기록하세요.")
    if c["status"] in ("none", "rejected"):
        c["version"] += 1  # 반려되었거나 처음이면 새 버전
    put(work, st)
    return c["version"]


def built(work, ch, version, passed, result):
    st = get(work)
    c = st["channels"][ch]
    c["status"] = "awaiting_confirm" if passed else "check_failed"
    put(work, st)
    log(work, st, ch, version, "생성", "시스템", "", result)
    log(work, st, ch, version, "점검 통과" if passed else "점검 실패", "시스템", "" if passed else "check.md 참고", result)


def confirm(work, ch, approve, actor="매니저", reason=""):
    st = get(work)
    c = st["channels"][ch]
    if c["status"] != "awaiting_confirm":
        raise Refused(f"{CHANNEL_KO[ch]}는 컨펌 대기 상태가 아닙니다 (현재: {c['status']}).")
    if not approve and not reason:
        raise Refused("반려할 때는 사유를 적어야 합니다.")
    c["status"] = "confirmed" if approve else "rejected"
    put(work, st)
    log(work, st, ch, c["version"], "컨펌" if approve else "반려", actor, reason)


def published(work, ch, url, actor="에디터", memo=""):
    st = get(work)
    c = st["channels"][ch]
    if c["status"] not in ("confirmed", "published"):
        raise Refused(f"{CHANNEL_KO[ch]}는 컨펌 전이라 게시할 수 없습니다 (현재: {c['status']}).")
    c["status"], c["url"] = "published", url
    put(work, st)
    log(work, st, ch, c["version"], "게시 완료", actor, memo, "", url)
