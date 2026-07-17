import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database import init_db
from handlers import register_handlers

if not BOT_TOKEN:
    logging.error("❌ BOT_TOKEN не найден!")
    exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

register_handlers(dp)

async def on_startup():
    await init_db()
    logging.info("✅ База данных инициализирована")
    logging.info("✅ Бот запущен!")

async def main():
    await on_startup()
    
    try:
        # Проверяем, нет ли вебхука
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url:
            logging.info(f"🔄 Удаляем вебхук: {webhook_info.url}")
            await bot.delete_webhook()
        
        logging.info("🔄 Запускаем polling...")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logging.info("⏹ Бот остановлен")
    except Exception as e:
        logging.error(f"❌ Ошибка: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("⏹ Бот остановлен")
