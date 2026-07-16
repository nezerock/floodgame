import os
import sys

# Берем токен ТОЛЬКО из переменных окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN не найден в переменных окружения!")
    print(f"Доступные переменные: {list(os.environ.keys())}")
    print("На Railway: добавьте переменную BOT_TOKEN в Dashboard")
    sys.exit(1)

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
