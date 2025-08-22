import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from storage import get_user, update_user, get_all_users
from keyboards import tasks_keyboard

scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Moscow"))


# ─────────────────────────────
# Отправка напоминания
# ─────────────────────────────
async def send_task_reminder(bot, user_id, list_id):
    u = get_user(user_id)
    lst = u.get("lists", {}).get(list_id)
    if not lst:
        return
    tasks = lst.get("tasks", [])
    focus = u.get("focus", "💡 Сегодня нет фокуса")
    text = f"📌 <b>Фокус дня:</b> {focus}\n\n📝 <b>Список дел:</b>"
    await bot.send_message(user_id, text, reply_markup=tasks_keyboard(list_id, tasks))


# ─────────────────────────────
# Планирование напоминания
# ─────────────────────────────
def schedule_tasks_reminder(bot, user_id, list_id, time_str, save_to_json=True):
    h, m = map(int, time_str.split(":"))

    # Сохраняем в JSON
    if save_to_json:
        user_data = get_user(user_id)
        if "lists" not in user_data:
            user_data["lists"] = {}
        if list_id not in user_data["lists"]:
            user_data["lists"][list_id] = {}
        user_data["lists"][list_id]["reminder"] = time_str
        update_user(user_id, user_data)

    job_id = f"task_{user_id}_{list_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    scheduler.add_job(
        send_task_reminder,
        trigger=CronTrigger(hour=h, minute=m),
        args=[bot, user_id, list_id],
        id=job_id,
        replace_existing=True,
    )
    print(f"✅ Напоминание для {user_id} ({list_id}) на {time_str} запланировано")


# ─────────────────────────────
# Восстановление всех напоминаний при старте
# ─────────────────────────────
def restore_reminders(bot):
    users = get_all_users()
    for user_id, u in users.items():
        lists = u.get("lists", {})
        for list_id, lst in lists.items():
            time_str = lst.get("reminder")
            if time_str:
                schedule_tasks_reminder(
                    bot, user_id, list_id, time_str, save_to_json=False
                )


# ─────────────────────────────
# Планирование пробуждения
# ─────────────────────────────
def schedule_wakeup(bot, user_id, wake_time, hello_text_builder):
    h, m = map(int, wake_time.split(":"))
    now = datetime.now()
    when = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if when <= now:
        when += timedelta(days=1)

    async def send():
        await bot.send_message(user_id, hello_text_builder())
        update_user(user_id, {"state": "await_focus"})

    asyncio.create_task(schedule_at(when, send))


async def schedule_at(when: datetime, coro):
    delay = (when - datetime.now()).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
    await coro()
