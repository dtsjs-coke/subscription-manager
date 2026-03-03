import yaml
from datetime import date
from src.github_manager import get_file, update_file
from src.utils import hash_password, verify_password

USERS_PATH = "data/users.yaml"
SUBS_PATH = "data/subscriptions.yaml"


def _load_users() -> tuple[list, str]:
    content, sha = get_file(USERS_PATH)
    data = yaml.safe_load(content)
    return data.get("users", []), sha


def _save_users(users: list, sha: str, message: str) -> bool:
    content = yaml.dump({"users": users}, allow_unicode=True, default_flow_style=False)
    return update_file(USERS_PATH, content, sha, message)


def register_user(user_id: str, password: str, telegram_chat_id: str = "") -> tuple[bool, str]:
    try:
        users, sha = _load_users()
        if any(u["id"] == user_id for u in users):
            return False, "이미 사용 중인 아이디입니다."

        new_user = {
            "id": user_id,
            "password_hash": hash_password(password),
            "telegram_chat_id": telegram_chat_id.strip(),
            "created_at": str(date.today()),
        }
        users.append(new_user)
        ok = _save_users(users, sha, f"feat: 신규 사용자 등록 - {user_id}")
        if not ok:
            return False, "사용자 저장에 실패했습니다."

        # subscriptions.yaml에 빈 키 생성
        subs_content, subs_sha = get_file(SUBS_PATH)
        subs_data = yaml.safe_load(subs_content)
        if subs_data is None:
            subs_data = {}
        subs = subs_data.get("subscriptions", {})
        if user_id not in subs:
            subs[user_id] = []
        new_subs_content = yaml.dump(
            {"subscriptions": subs}, allow_unicode=True, default_flow_style=False
        )
        update_file(SUBS_PATH, new_subs_content, subs_sha, f"feat: 구독 키 생성 - {user_id}")
        return True, "회원가입이 완료되었습니다."
    except Exception as e:
        return False, f"오류 발생: {str(e)}"


def login(user_id: str, password: str) -> tuple[bool, dict]:
    try:
        users, _ = _load_users()
        for user in users:
            if user["id"] == user_id:
                if verify_password(password, user["password_hash"]):
                    return True, {k: v for k, v in user.items() if k != "password_hash"}
                return False, {}
        return False, {}
    except Exception:
        return False, {}


def update_user(user_id: str, new_password: str = "", telegram_chat_id: str = None) -> tuple[bool, str]:
    try:
        users, sha = _load_users()
        for user in users:
            if user["id"] == user_id:
                if new_password:
                    user["password_hash"] = hash_password(new_password)
                if telegram_chat_id is not None:
                    user["telegram_chat_id"] = telegram_chat_id.strip()
                ok = _save_users(users, sha, f"feat: 사용자 정보 수정 - {user_id}")
                return (True, "정보가 수정되었습니다.") if ok else (False, "저장에 실패했습니다.")
        return False, "사용자를 찾을 수 없습니다."
    except Exception as e:
        return False, f"오류 발생: {str(e)}"


def get_user(user_id: str) -> dict:
    try:
        users, _ = _load_users()
        for user in users:
            if user["id"] == user_id:
                return {k: v for k, v in user.items() if k != "password_hash"}
    except Exception:
        pass
    return {}