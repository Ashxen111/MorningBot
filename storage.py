import json
import os
from threading import Lock

DATA_FILE = "data.json"
lock = Lock()

data = {}

# Загружаем данные при старте
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)


def save_data():
    with lock:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def get_user(user_id):
    return data.setdefault(str(user_id), {})


def update_user(user_id, info: dict):
    u = get_user(user_id)
    u.update(info)
    save_data()


def upsert_list(user_id, list_id, tasks):
    u = get_user(user_id)
    u.setdefault("lists", {})[list_id] = {"tasks": tasks}
    save_data()


def get_list(user_id, list_id):
    return get_user(user_id).get("lists", {}).get(list_id)
