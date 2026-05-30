import os
import requests
from datetime import date, datetime
from src.auth_manager import BUTLER_API_URL
from src.data_manager import load_subscriptions, _save_subscriptions

def send_telegram(chat_id: str, message: str) -> bool:
    token = os.getenv("TELEGRAM_TOKEN")
    if not token or not chat_id:
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"텔레그램 발송 실패: {e}")
        return False

def check_and_notify():
    # 1. 모든 사용자 목록 가져오기
    try:
        resp = requests.get(f"{BUTLER_API_URL}/users/all", timeout=10)
        if resp.status_code != 200:
            # 전체 사용자 목록 API가 없을 경우를 대비해 subscriptions에서 유저 목록 추출 시도
            # (또는 data/users.yaml을 직접 읽어야 할 수도 있으나 API 우선 사용)
            print("사용자 목록을 가져오는데 실패했습니다.")
            return
        users = resp.json()
    except Exception as e:
        print(f"API 연결 실패: {e}")
        return

    today = date.today()
    
    for user in users:
        user_id = user.get("id")
        chat_id = user.get("telegram_chat_id")
        
        if not chat_id:
            continue
            
        items = load_subscriptions(user_id)
        updated = False
        
        for item in items:
            if item.get("status") != "active" or item.get("auto_renew"):
                continue
                
            end_date_str = item.get("end_date")
            if not end_date_str:
                continue
                
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except ValueError:
                continue
                
            days_left = (end_date - today).days
            notify_sent = item.get("notify_sent", [])
            
            # 알림 조건 체크
            target_t = None
            if days_left == 30: target_t = "30d"
            elif days_left == 7: target_t = "7d"
            elif days_left == 1: target_t = "1d"
            elif days_left == 0: target_t = "0d"
            
            if target_t and target_t not in notify_sent:
                # 메시지 구성
                msg = (
                    f"🔔 <b>구독 만료 알림</b>\n\n"
                    f"📦 <b>서비스:</b> {item.get('name')}\n"
                    f"📅 <b>만료일:</b> {end_date_str} (D-{days_left})\n"
                    f"💳 <b>결제일:</b> {item.get('payment_date')}일\n"
                    f"💰 <b>금액:</b> {item.get('total_price', 0):,}원"
                )
                if days_left == 0:
                    msg = msg.replace("🔔 구독 만료 알림", "🚨 <b>오늘 구독 만료</b>")
                
                if send_telegram(chat_id, msg):
                    notify_sent.append(target_t)
                    item["notify_sent"] = notify_sent
                    updated = True
                    print(f"[{user_id}] {item.get('name')} {target_t} 알림 발송 완료")

        if updated:
            _save_subscriptions(user_id, items)
