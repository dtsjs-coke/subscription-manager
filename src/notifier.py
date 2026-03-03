import os
import yaml
import requests
import streamlit as st
from src.github_manager import get_file, update_file
from src.utils import days_until_expiry, format_price

USERS_PATH = "data/users.yaml"
SUBS_PATH = "data/subscriptions.yaml"

NOTIFY_DAYS = {30: "30d", 7: "7d", 1: "1d", 0: "0d"}


def _get_token():
    try:
        return st.secrets["telegram"]["token"]
    except Exception:
        return os.environ.get("TELEGRAM_TOKEN", "")


def send_telegram(chat_id: str, message: str) -> bool:
    token = _get_token()
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
    return resp.status_code == 200


def _build_message(item: dict, days: int) -> str:
    if days == 0:
        badge = "📛 만료 당일"
    else:
        badge = f"⏰ D-{days}"

    payment_date = item.get("payment_date", "-")
    if str(payment_date).isdigit():
        payment_date = f"매월 {payment_date}일"

    lines = [
        "🔔 <b>구독 만료 알림</b>",
        "",
        f"📦 서비스: {item.get('name', '-')}",
        f"📅 만료일: {item.get('end_date', '-')} ({badge})",
        f"💳 결제일: {payment_date}",
        f"💰 총 가격: {format_price(item.get('total_price', 0))}",
        f"📆 월 환산: {format_price(item.get('monthly_price', 0))}",
    ]
    return "\n".join(lines)


def check_and_notify():
    # users 로드
    users_content, _ = get_file(USERS_PATH)
    users_data = yaml.safe_load(users_content)
    users = users_data.get("users", [])

    # subscriptions 로드
    subs_content, subs_sha = get_file(SUBS_PATH)
    subs_data = yaml.safe_load(subs_content)
    subs = subs_data.get("subscriptions", {})

    changed = False

    for user in users:
        user_id = user["id"]
        chat_id = user.get("telegram_chat_id", "").strip()
        if not chat_id:
            continue

        items = subs.get(user_id, [])
        for item in items:
            if item.get("status") == "paused":
                continue
            try:
                days = days_until_expiry(item["end_date"])
            except Exception:
                continue

            for threshold, key in NOTIFY_DAYS.items():
                if days == threshold and key not in item.get("notify_sent", []):
                    msg = _build_message(item, days)
                    if send_telegram(chat_id, msg):
                        item.setdefault("notify_sent", []).append(key)
                        changed = True
                        print(f"✅ 알림 발송: {user_id} / {item.get('name')} / {key}")
                    else:
                        print(f"❌ 알림 실패: {user_id} / {item.get('name')} / {key}")

    if changed:
        new_content = yaml.dump(
            {"subscriptions": subs}, allow_unicode=True, default_flow_style=False
        )
        update_file(SUBS_PATH, new_content, subs_sha, "chore: 알림 발송 이력 업데이트")
        print("✅ subscriptions.yaml 업데이트 완료")