from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def tasks_keyboard(list_id, tasks):
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{'☑ ' if t.startswith('☑') else '☐ '}{t.lstrip('☑ ')}",
                callback_data=f"done:{list_id}:{i}",
            )
        ]
        for i, t in enumerate(tasks)
    ]
    buttons.append(
        [InlineKeyboardButton(text="+ Добавить", callback_data=f"add:{list_id}")]
    )
    buttons.append(
        [
            InlineKeyboardButton(
                text="✅ Завершить день", callback_data=f"finish:{list_id}"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)
