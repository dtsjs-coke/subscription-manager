import uuid
import requests
import streamlit as st

BUTLER_API_URL = "https://distributed-permanent-macro-medicine.trycloudflare.com"


def load_subscriptions(user_id: str) -> list:
    try:
        resp = requests.get(f"{BUTLER_API_URL}/subscriptions/{user_id}", timeout=10)
        return resp.json() if resp.status_code == 200 else []
    except Exception as e:
        st.error(f"S9 서버 연결 실패: {e}")
        return []


def _save_subscriptions(user_id: str, items: list) -> bool:
    try:
        resp = requests.post(f"{BUTLER_API_URL}/subscriptions/{user_id}", json=items, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        st.error(f"데이터 저장 실패: {e}")
        return False


def add_subscription(user_id: str, item: dict) -> bool:
    items = load_subscriptions(user_id)
    item["id"] = str(uuid.uuid4())
    item["notify_sent"] = []
    items.append(item)
    return _save_subscriptions(user_id, items)


def update_subscription(user_id: str, item_id: str, new_item: dict) -> bool:
    items = load_subscriptions(user_id)
    for i, item in enumerate(items):
        if item["id"] == item_id:
            # 만료일 변경 시 notify_sent 초기화
            if item.get("end_date") != new_item.get("end_date"):
                new_item["notify_sent"] = []
            else:
                new_item["notify_sent"] = item.get("notify_sent", [])
            new_item["id"] = item_id
            items[i] = new_item
            return _save_subscriptions(user_id, items)
    return False


def delete_subscription(user_id: str, item_id: str) -> bool:
    items = load_subscriptions(user_id)
    items = [i for i in items if i["id"] != item_id]
    return _save_subscriptions(user_id, items)
