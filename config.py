import os
import sys

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN не найден!")
    sys.exit(1)

# Настройки игры
DAILY_BONUS = 5
START_BALANCE = 50
MIN_BET = 1
MAX_BET = 1000

# Множители выигрышей
SLOT_MULTIPLIER = 20  # 20x
DICE_MULTIPLIER = 1.7  # 1.7x

# Кликер
CLICK_REWARD = 0.1
CLICK_COOLDOWN = 5
MAX_CLICKS_PER_DAY = 50

# Магазин бонусов
SHOP_ITEMS = {
    '1.3x': {'price': 25, 'multiplier': 1.3},
    '1.5x': {'price': 40, 'multiplier': 1.5},
    '2.0x': {'price': 70, 'multiplier': 2.0}
}

# Эмодзи
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
    'leaderboard': '📊',
    'shop': '🏪'
}
