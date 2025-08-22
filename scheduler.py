import asyncio
from datetime import datetime, timedelta
from storage import get_user
from keyboards import tasks_keyboard
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Создаём один глобальный планировщик
scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Moscow"))


# ─────────────────────────────
# 1. Универсальный планировщик задач
# ─────────────────────────────
async def schedule_at(when: datetime, coro):
    """Ждём указанное время, затем выполняем короутину."""
    delay = (when - datetime.now()).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
    await coro()


def plan_reminder_task(when: datetime, fn):
    """Создаёт задачу в event loop."""
    asyncio.create_task(schedule_at(when, fn))


# ─────────────────────────────
# 2. Напоминание о задачах
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


def schedule_tasks_reminder(bot, user_id, list_id, focus, time_str):
    h, m = map(int, time_str.split(":"))
    scheduler.add_job(
        send_task_reminder,
        trigger=CronTrigger(hour=h, minute=m),
        args=[bot, user_id, list_id],
        id=f"task_{user_id}_{list_id}",
        replace_existing=True,
    )
    print(f"✅ Добавлено напоминание для {user_id} в {time_str}")


# ─────────────────────────────
# 3. Планирование пробуждения
# ─────────────────────────────
def schedule_wakeup(bot, user_id, wake_time, hello_text_builder):
    """Планирует отправку приветственного сообщения утром и устанавливает состояние."""
    h, m = map(int, wake_time.split(":"))
    now = datetime.now()
    when = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if when <= now:
        when += timedelta(days=1)

    async def send():
        await bot.send_message(user_id, hello_text_builder())
        from storage import update_user

        update_user(user_id, {"state": "await_focus"})

    plan_reminder_task(when, send)
