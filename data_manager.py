import uuid
import yaml
from src.github_manager import get_file, update_file

SUBS_PATH = "data/subscriptions.yaml"


def _load_all() -> tuple[dict, str]:
    content, sha = get_file(SUBS_PATH)
    data = yaml.safe_load(content)
    if data is None:
        data = {}
    return data.get("subscriptions", {}), sha


def _save_all(subs: dict, sha: str, message: str) -> bool:
    content = yaml.dump({"subscriptions": subs}, allow_unicode=True, default_flow_style=False)
    return update_file(SUBS_PATH, content, sha, message)


def load_subscriptions(user_id: str) -> list:
    subs, _ = _load_all()
    return subs.get(user_id, [])


def add_subscription(user_id: str, item: dict) -> bool:
    subs, sha = _load_all()
    item["id"] = str(uuid.uuid4())
    item["notify_sent"] = []
    if user_id not in subs:
        subs[user_id] = []
    subs[user_id].append(item)
    return _save_all(subs, sha, f"feat: 구독 추가 - {user_id} / {item.get('name', '')}")


def update_subscription(user_id: str, item_id: str, new_item: dict) -> bool:
    subs, sha = _load_all()
    items = subs.get(user_id, [])
    for i, item in enumerate(items):
        if item["id"] == item_id:
            # 만료일 변경 시 notify_sent 초기화
            if item.get("end_date") != new_item.get("end_date"):
                new_item["notify_sent"] = []
            else:
                new_item["notify_sent"] = item.get("notify_sent", [])
            new_item["id"] = item_id
            items[i] = new_item
            subs[user_id] = items
            return _save_all(subs, sha, f"feat: 구독 수정 - {user_id} / {new_item.get('name', '')}")
    return False


def delete_subscription(user_id: str, item_id: str) -> bool:
    subs, sha = _load_all()
    items = subs.get(user_id, [])
    name = next((i.get("name", "") for i in items if i["id"] == item_id), "")
    subs[user_id] = [i for i in items if i["id"] != item_id]
    return _save_all(subs, sha, f"feat: 구독 삭제 - {user_id} / {name}")