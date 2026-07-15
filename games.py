import random
from typing import Tuple

class Games:
    @staticmethod
    def coin_flip(bet: int, choice: str) -> Tuple[int, str]:
        """Орёл или решка"""
        result = random.choice(['Орёл', 'Решка'])
        
        if choice.lower() == result.lower():
            return bet * 2, f"🪙 {result} - Вы выиграли! +{bet * 2}"
        else:
            return -bet, f"🪙 {result} - Вы проиграли! -{bet}"
    
    @staticmethod
    def dice_game(bet: int, guess: int) -> Tuple[int, str]:
        """Угадай число на кубике (1-6)"""
        if guess < 1 or guess > 6:
            return -bet, "❌ Число должно быть от 1 до 6!"
        
        result = random.randint(1, 6)
        if guess == result:
            return bet * 5, f"🎲 Выпало {result}! Вы угадали! +{bet * 5}"
        else:
            return -bet, f"🎲 Выпало {result}. Вы не угадали! -{bet}"
    
    @staticmethod
    def slot_machine(bet: int) -> Tuple[int, str]:
        """Игровой автомат"""
        symbols = ['🍒', '🍋', '🍊', '🍇', '🔔', '💎', '7️⃣']
        result = [random.choice(symbols) for _ in range(3)]
        
        if result[0] == result[1] == result[2]:
            if result[0] == '💎':
                return bet * 10, f"{' '.join(result)} 💎 ДЖЕКПОТ! +{bet * 10}"
            elif result[0] == '7️⃣':
                return bet * 7, f"{' '.join(result)} 🎰 СЕМЁРКИ! +{bet * 7}"
            else:
                return bet * 3, f"{' '.join(result)} 🎰 ТРИ В РЯД! +{bet * 3}"
        elif result[0] == result[1] or result[1] == result[2]:
            return bet, f"{' '.join(result)} 🔄 ДВА В РЯД! Возврат ставки"
        else:
            return -bet, f"{' '.join(result)} ❌ Ничего не совпало! -{bet}"
    
    @staticmethod
    def high_low(bet: int, guess: str) -> Tuple[int, str]:
        """Больше-меньше (число 1-100)"""
        number = random.randint(1, 100)
        if guess == 'higher':
            if number > 50:
                return bet * 2, f"📈 Число {number} (>50)! Вы выиграли! +{bet * 2}"
            else:
                return -bet, f"📉 Число {number} (<=50)! Вы проиграли! -{bet}"
        elif guess == 'lower':
            if number <= 50:
                return bet * 2, f"📉 Число {number} (<=50)! Вы выиграли! +{bet * 2}"
            else:
                return -bet, f"📈 Число {number} (>50)! Вы проиграли! -{bet}"
        else:
            return -bet, "❌ Неправильный выбор! Используйте 'higher' или 'lower'"