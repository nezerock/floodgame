import random
import asyncio
from typing import Tuple

class Games:
    @staticmethod
    async def dice_game(bet: int, multiplier: float = 1.0) -> Tuple[float, bool, str]:
        """Игра в кости с анимацией Telegram"""
        player_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)
        
        # Используем анимированный эмодзи кубика 🎲
        # Он автоматически покажет анимацию броска в Telegram!
        
        if player_roll > bot_roll:
            win_amount = bet * 1.7 * multiplier
            result = (
                f"🎲 ТВОЙ БРОСОК: {player_roll}\n"
                f"🤖 БРОСОК БОТА: {bot_roll}\n\n"
                f"🏆 ТЫ ПОБЕДИЛ! +{win_amount:.1f} монет! (x{1.7 * multiplier:.1f})"
            )
            return win_amount, True, result
        elif player_roll < bot_roll:
            win_amount = -bet
            result = (
                f"🎲 ТВОЙ БРОСОК: {player_roll}\n"
                f"🤖 БРОСОК БОТА: {bot_roll}\n\n"
                f"😢 БОТ ПОБЕДИЛ! -{bet} монет!"
            )
            return win_amount, False, result
        else:
            result = (
                f"🎲 ТВОЙ БРОСОК: {player_roll}\n"
                f"🤖 БРОСОК БОТА: {bot_roll}\n\n"
                f"🤝 НИЧЬЯ! Ставка возвращена!"
            )
            return 0, False, result
    
    @staticmethod
    async def slot_machine(bet: int, multiplier: float = 1.0) -> Tuple[float, str]:
        """Игровой автомат с анимацией"""
        symbols = ['🍒', '🍋', '🍊', '🍇', '🔔', '💎', '7️⃣']
        result = [random.choice(symbols) for _ in range(3)]
        
        if result[0] == result[1] == result[2]:
            if result[0] == '💎':
                win = bet * 20 * multiplier
                return win, f"🎰 {' '.join(result)} 💎 ДЖЕКПОТ! +{win:.1f} монет! (x{20 * multiplier:.1f})"
            elif result[0] == '7️⃣':
                win = bet * 15 * multiplier
                return win, f"🎰 {' '.join(result)} 🎰 СЕМЁРКИ! +{win:.1f} монет! (x{15 * multiplier:.1f})"
            else:
                win = bet * 10 * multiplier
                return win, f"🎰 {' '.join(result)} 🎰 ТРИ В РЯД! +{win:.1f} монет! (x{10 * multiplier:.1f})"
        elif result[0] == result[1] or result[1] == result[2]:
            return bet, f"🎰 {' '.join(result)} 🔄 ДВА В РЯД! Возврат ставки"
        else:
            return -bet, f"🎰 {' '.join(result)} ❌ Ничего не совпало! -{bet}"
