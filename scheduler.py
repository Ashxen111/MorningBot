import asyncio
from datetime import datetime
from storage import get_user, update_user
from keyboards import tasks_keyboard
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz


# ─────────────────────────────
# 1. Глобальный планировщик
# ─────────────────────────────
scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Moscow"))


# ─────────────────────────────
# 2. Напоминание о задачах
# ─────────────────────────────
async def send_task_reminder(bot, user_id, list_id):
    """Отправляет список задач пользователю"""
    u = get_user(user_id)
    lst = u.get("lists", {}).get(list_id)
    if not lst:
        return

    tasks = lst.get("tasks", [])
    focus = u.get("focus", "💡 Сегодня нет фокуса")
    text = f"📌 <b>Фокус дня:</b> {focus}\n\n📝 <b>Список дел:</b>"

    await bot.send_message(user_id, text, reply_markup=tasks_keyboard(list_id, tasks))


def schedule_tasks_reminder(bot, user_id, list_id, time_str: str):
    """Запланировать ежедневное напоминание со списком задач"""
    h, m = map(int, time_str.split(":"))

    async def job():
        await send_task_reminder(bot, user_id, list_id)

    scheduler.add_job(
        lambda: asyncio.create_task(job()),
        trigger=CronTrigger(hour=h, minute=m),
        id=f"task_{user_id}_{list_id}",
        replace_existing=True,
    )
    print(f"✅ Добавлено напоминание для {user_id} в {time_str}")


# ─────────────────────────────
# 3. Утреннее приветствие
# ─────────────────────────────
def schedule_wakeup(bot, user_id, wake_time: str, hello_text_builder):
    """Запланировать отправку утреннего приветствия"""
    h, m = map(int, wake_time.split(":"))

    async def job():
        await bot.send_message(user_id, hello_text_builder())
        update_user(user_id, {"state": "await_focus"})

    scheduler.add_job(
        lambda: asyncio.create_task(job()),
        trigger=CronTrigger(hour=h, minute=m),
        id=f"wakeup_{user_id}",
        replace_existing=True,
    )
    print(f"🌞 Установлено пробуждение для {user_id} в {wake_time}")
