import uuid
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from storage import update_user, get_user, upsert_list, get_list
from utils import get_time_info, get_random_quote, parse_hhmm, next_datetime_from_hhmm
from keyboards import tasks_keyboard
from scheduler import schedule_tasks_reminder, schedule_wakeup


router = Router()


def get_user_state(user_id):
    return get_user(user_id).get("state")


# 1️⃣ Приветствие и фокус
@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    text = f"{get_time_info()}\n\nПриветствую тебя на планете Земля!\n\nЦитата для размышления:\n<i>{get_random_quote()}</i>\n\n☕ Выпей чашечку кофе или чаю.\nСосредоточься: какая у тебя глобальная цель?\nВ чем твоя основная задача на сегодня?\n\n✍️ Напиши одну фразу — твой <b>Фокус дня</b>."
    update_user(user_id, {"state": "await_focus"})
    await message.answer(text)


@router.message(F.text)
async def handle_text(message: Message):
    user_id = message.from_user.id
    state = get_user_state(user_id)
    text = message.text.strip()

    if state == "await_focus":
        update_user(user_id, {"focus": text, "state": "await_tasks"})
        await message.answer(
            f"Фокус дня сохранен: <b>{text}</b>\n\nТеперь введи список дел на сегодня через запятую:"
        )
        return

    if state == "await_tasks":
        tasks = [t.strip() for t in text.split(",") if t.strip()]
        if not tasks:
            await message.answer("❌ Список дел пуст. Введи хотя бы одно задание.")
            return
        list_id = str(uuid.uuid4())
        upsert_list(user_id, list_id, tasks)
        update_user(user_id, {"current_list": list_id, "state": "await_time"})
        await message.answer(
            "✅ Список дел сохранен.\n\n⏰ Во сколько прислать напоминание?\nФормат времени: ЧЧ:ММ (например, 09:30)"
        )
        return

    if state == "await_time":
        if not parse_hhmm(text):
            await message.answer("❌ Неверный формат. Введи время в формате ЧЧ:ММ.")
            return
        u = get_user(user_id)
        list_id = u.get("current_list")
        focus = u.get("focus")
        schedule_tasks_reminder(message.bot, user_id, list_id, focus, text)
        update_user(user_id, {"state": None})
        await message.answer(
            f"⏳ Отлично! Я напомню тебе о делах в <b>{text}</b>.\nТы всегда сможешь добавить новые задачи позже."
        )
        return

    if state and state.startswith("await_add:"):
        list_id = state.split(":")[1]
        new_tasks = [t.strip() for t in text.split(",") if t.strip()]
        lst = get_list(user_id, list_id)
        if lst:
            all_tasks = lst.get("tasks", []) + new_tasks
            upsert_list(user_id, list_id, all_tasks)
            update_user(user_id, {"state": "await_time"})
            await message.answer(
                "✅ Задачи добавлены!\n\n⏰ Во сколько прислать напоминание по ним? (ЧЧ:ММ)"
            )
        return

    if state == "await_wakeup":
        if not parse_hhmm(text):
            await message.answer("❌ Неверный формат. Введи время в формате ЧЧ:ММ.")
            return

        def build_hello():
            return f"{get_time_info()}\n\nПриветствую тебя на планете Земля!\n\nЦитата для размышления:\n<i>{get_random_quote()}</i>\n\n☕ Выпей чашечку кофе или чаю.\nНапиши свой новый <b>Фокус дня</b>."

        schedule_wakeup(message.bot, user_id, text, build_hello)
        update_user(user_id, {"state": None})
        await message.answer(f"✅ Отлично! Завтра я разбужу тебя в <b>{text}</b> 🌅")
        return


# 3️⃣ Кнопки задач
@router.callback_query(F.data.startswith("done:"))
async def mark_task_done(callback: CallbackQuery):
    _, list_id, idx = callback.data.split(":")
    idx = int(idx)
    user_id = callback.from_user.id
    lst = get_list(user_id, list_id)
    if not lst:
        await callback.answer("❌ Список не найден.", show_alert=True)
        return
    tasks = lst.get("tasks", [])
    if 0 <= idx < len(tasks):
        task = tasks[idx]
        tasks[idx] = task[2:] if task.startswith("☑") else "☑ " + task
    upsert_list(user_id, list_id, tasks)
    await callback.message.edit_reply_markup(
        reply_markup=tasks_keyboard(list_id, tasks)
    )
    await callback.answer("Обновлено ✅")


@router.callback_query(F.data.startswith("add:"))
async def add_task_prompt(callback: CallbackQuery):
    _, list_id = callback.data.split(":")
    update_user(callback.from_user.id, {"state": f"await_add:{list_id}"})
    await callback.message.answer("✍️ Введи новые задачи через запятую:")
    await callback.answer()


@router.callback_query(F.data.startswith("finish:"))
async def finish_day(callback: CallbackQuery):
    update_user(callback.from_user.id, {"state": "await_wakeup"})
    await callback.message.answer(
        "🌙 День завершен.\n\n⏰ Во сколько тебя разбудить завтра?\nФормат ЧЧ:ММ (например, 07:00)"
    )
    await callback.answer()
