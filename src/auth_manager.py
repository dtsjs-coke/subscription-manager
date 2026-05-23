from datetime import date
import requests
from src.utils import hash_password, verify_password

BUTLER_API_URL = "https://distributed-permanent-macro-medicine.trycloudflare.com"

def _get_user_from_api(user_id: str) -> dict:
    try:
        resp = requests.get(f"{BUTLER_API_URL}/users/{user_id}", timeout=10)
        return resp.json() if resp.status_code == 200 else {}
    except Exception:
        return {}


def register_user(user_id: str, password: str, telegram_chat_id: str = "") -> tuple[bool, str]:
    try:
        existing_user = _get_user_from_api(user_id)
        if existing_user:
            return False, "이미 사용 중인 아이디입니다."

        new_user = {
            "id": user_id,
            "password_hash": hash_password(password),
            "telegram_chat_id": telegram_chat_id.strip(),
            "created_at": str(date.today()),
        }
        
        resp = requests.post(f"{BUTLER_API_URL}/users/{user_id}", json=new_user, timeout=10)
        if resp.status_code != 200:
            return False, "사용자 저장에 실패했습니다."
            
        return True, "회원가입이 완료되었습니다."
    except Exception as e:
        return False, f"오류 발생: {str(e)}"


def login(user_id: str, password: str) -> tuple[bool, dict]:
    try:
        user = _get_user_from_api(user_id)
        if user and verify_password(password, user.get("password_hash", "")):
            return True, {k: v for k, v in user.items() if k != "password_hash"}
        return False, {}
    except Exception:
        return False, {}


def update_user(user_id: str, new_password: str = "", telegram_chat_id: str = None) -> tuple[bool, str]:
    try:
        user = _get_user_from_api(user_id)
        if not user:
            return False, "사용자를 찾을 수 없습니다."
            
        if new_password:
            user["password_hash"] = hash_password(new_password)
        if telegram_chat_id is not None:
            user["telegram_chat_id"] = telegram_chat_id.strip()
            
        resp = requests.post(f"{BUTLER_API_URL}/users/{user_id}", json=user, timeout=10)
        if resp.status_code == 200:
            return True, "정보가 수정되었습니다."
        return False, "저장에 실패했습니다."
    except Exception as e:
        return False, f"오류 발생: {str(e)}"


def get_user(user_id: str) -> dict:
    user = _get_user_from_api(user_id)
    return {k: v for k, v in user.items() if k != "password_hash"}
