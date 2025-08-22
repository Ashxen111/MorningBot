import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from handlers import router
from scheduler import scheduler


# ─────────────────────────────
# Настройка логирования
# ─────────────────────────────
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# ─────────────────────────────
# Загрузка переменных окружения
# ─────────────────────────────
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env")


# ─────────────────────────────
# Инициализация бота и диспетчера
# ─────────────────────────────
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)


# ─────────────────────────────
# Основной запуск
# ─────────────────────────────
async def main():
    logging.info("🚀 Бот запускается...")

    # Запуск планировщика
    if not scheduler.running:
        scheduler.start()
        logging.info("✅ Планировщик запущен")

    # Запуск бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("🛑 Бот остановлен вручную")
