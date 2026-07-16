import random
from typing import Tuple

class Games:
    @staticmethod
    def dice_game(bet: int) -> Tuple[int, int, str]:
        """Игра в кости: бот и игрок кидают кубики"""
        player_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)
        
        # Анимированные эмодзи для кубиков
        dice_emojis = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅']
        
        if player_roll > bot_roll:
            win_amount = bet * 2
            result = f"🎲 Твой бросок: {dice_emojis[player_roll-1]} {player_roll}\n🤖 Бросок бота: {dice_emojis[bot_roll-1]} {bot_roll}\n\n🏆 ТЫ ПОБЕДИЛ! +{win_amount} монет!"
            return win_amount, True, result
        elif player_roll < bot_roll:
            win_amount = -bet
            result = f"🎲 Твой бросок: {dice_emojis[player_roll-1]} {player_roll}\n🤖 Бросок бота: {dice_emojis[bot_roll-1]} {bot_roll}\n\n😢 БОТ ПОБЕДИЛ! -{bet} монет!"
            return win_amount, False, result
        else:
            result = f"🎲 Твой бросок: {dice_emojis[player_roll-1]} {player_roll}\n🤖 Бросок бота: {dice_emojis[bot_roll-1]} {bot_roll}\n\n🤝 НИЧЬЯ! Ставка возвращена!"
            return 0, False, result
    
    @staticmethod
    def coin_flip(bet: int, choice: str) -> Tuple[int, str]:
        """Орёл или решка с анимацией"""
        result = random.choice(['Орёл', 'Решка'])
        coin = '🪙'
        
        if choice.lower() == result.lower():
            win_amount = bet * 2
            return win_amount, f"{coin} {result}! 🎉 Ты выиграл! +{win_amount} монет!"
        else:
            return -bet, f"{coin} {result}! 😢 Ты проиграл! -{bet} монет!"
    
    @staticmethod
    def slot_machine(bet: int) -> Tuple[int, str]:
        """Игровой автомат с анимацией"""
        symbols = ['🍒', '🍋', '🍊', '🍇', '🔔', '💎', '7️⃣']
        result = [random.choice(symbols) for _ in range(3)]
        
        if result[0] == result[1] == result[2]:
            if result[0] == '💎':
                return bet * 10, f"🎰 {' '.join(result)} 💎 ДЖЕКПОТ! +{bet * 10}"
            elif result[0] == '7️⃣':
                return bet * 7, f"🎰 {' '.join(result)} 🎰 СЕМЁРКИ! +{bet * 7}"
            else:
                return bet * 3, f"🎰 {' '.join(result)} 🎰 ТРИ В РЯД! +{bet * 3}"
        elif result[0] == result[1] or result[1] == result[2]:
            return bet, f"🎰 {' '.join(result)} 🔄 ДВА В РЯД! Возврат ставки"
        else:
            return -bet, f"🎰 {' '.join(result)} ❌ Ничего не совпало! -{bet}"
