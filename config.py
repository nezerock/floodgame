import os
import sys

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN не найден!")
    sys.exit(1)

# Настройки игры
DAILY_BONUS = 100
START_BALANCE = 50
MIN_BET = 1
MAX_BET = 1000

# Кликер
CLICK_REWARD = 0.1
CLICK_COOLDOWN = 5  # секунд
MAX_CLICKS_PER_DAY = 50

# Эмодзи для игр
EMOJI = {
    'dice': '🎲',
    'coin': '🪙',
    'slot': '🎰',
    'trophy': '🏆',
    'star': '⭐',
    'fire': '🔥',
    'diamond': '💎',
    'click': '👆',
    'games': '🎮',
    'leaderboard': '📊'
}
