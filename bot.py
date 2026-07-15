import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from config import BOT_TOKEN
from database import init_db
from handlers import register_handlers

# Проверка токена
if not BOT_TOKEN:
    logging.error("❌ Токен не найден! Создайте файл .env с BOT_TOKEN")
    exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Инициализация бота
bot = Bot(token=BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Регистрация обработчиков
register_handlers(dp)

async def on_startup():
    """Действия при запуске бота"""
    await init_db()
    logging.info("✅ База данных инициализирована")
    logging.info("✅ Бот запущен!")

async def main():
    """Главная функция"""
    await on_startup()
    
    try:
        await dp.start_polling()
    except KeyboardInterrupt:
        logging.info("⏹ Бот остановлен")
    finally:
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("⏹ Бот остановлен")