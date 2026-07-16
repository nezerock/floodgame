import os
from dotenv import load_dotenv

# Загружаем переменные из .env (для локального запуска)
load_dotenv()

# Токен бота - сначала из переменных окружения, потом из .env
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Проверка токена
if not BOT_TOKEN:
    print("❌ BOT_TOKEN не найден!")
    print("Для локального запуска: создайте файл .env с BOT_TOKEN")
    print("Для Railway: добавьте переменную BOT_TOKEN в Dashboard")
    exit(1)

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
