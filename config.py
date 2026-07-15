import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Токен бота из .env
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError(
        "❌ BOT_TOKEN не найден!\n"
        "Создайте файл .env и добавьте: BOT_TOKEN=ваш_токен"
    )

# Настройки игры
DAILY_BONUS = 100
START_BALANCE = 50
MIN_BET = 10
MAX_BET = 1000

# Эмодзи для игр
EMOJI = {
    'dice': '🎲',
    'slot': '🎰',
    'coin': '🪙',
    'trophy': '🏆',
    'star': '⭐',
    'fire': '🔥',
    'diamond': '💎'
}