from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import Database
from games import Games
from config import EMOJI, DAILY_BONUS, MIN_BET

def main_keyboard():
    """Главное меню"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(f"{EMOJI['coin']} Баланс", callback_data="balance"),
        InlineKeyboardButton(f"{EMOJI['diamond']} Бонус", callback_data="daily"),
        InlineKeyboardButton(f"{EMOJI['dice']} Игры", callback_data="games"),
        InlineKeyboardButton(f"{EMOJI['trophy']} Лидеры", callback_data="leaderboard"),
        InlineKeyboardButton(f"{EMOJI['star']} История", callback_data="history")
    )
    return keyboard

def games_keyboard():
    """Меню игр"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(f"{EMOJI['coin']} Орёл/Решка", callback_data="game_coin"),
        InlineKeyboardButton(f"{EMOJI['dice']} Кости", callback_data="game_dice"),
        InlineKeyboardButton(f"{EMOJI['slot']} Слоты", callback_data="game_slot"),
        InlineKeyboardButton(f"{EMOJI['fire']} Больше/Меньше", callback_data="game_hl"),
        InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
    )
    return keyboard

def register_handlers(dp: Dispatcher):
    
    @dp.message_handler(commands=['start', 'help'])
    async def cmd_start(message: types.Message):
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        
        await Database.create_user(user_id, username, first_name)
        
        welcome_text = f"""
🎰 Добро пожаловать в КАЗИНО, {first_name}!

🪙 Твой баланс: {await Database.get_balance(user_id)} монет

🎮 Доступные игры:
• 🪙 Орёл/Решка - угадай сторону
• 🎲 Кости - угадай число от 1 до 6
• 🎰 Слоты - три в ряд
• 🔥 Больше/Меньше - угадай диапазон

💰 Ежедневный бонус: {DAILY_BONUS} монет
"""
        
        await message.answer(welcome_text, reply_markup=main_keyboard())
    
    @dp.callback_query_handler(lambda c: c.data == "main_menu")
    async def main_menu(callback: types.CallbackQuery):
        balance = await Database.get_balance(callback.from_user.id)
        await callback.message.edit_text(
            f"🎰 Главное меню\n\n🪙 Баланс: {balance} монет",
            reply_markup=main_keyboard()
        )
        await callback.answer()
    
    @dp.callback_query_handler(lambda c: c.data == "balance")
    async def show_balance(callback: types.CallbackQuery):
        balance = await Database.get_balance(callback.from_user.id)
        await callback.message.edit_text(
            f"💰 Твой баланс: {balance} монет",
            reply_markup=main_keyboard()
        )
        await callback.answer()
    
    @dp.callback_query_handler(lambda c: c.data == "daily")
    async def daily_bonus(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        
        if await Database.can_claim_daily(user_id):
            await Database.claim_daily(user_id)
            balance = await Database.get_balance(user_id)
            await callback.message.edit_text(
                f"🎉 Ты получил ежедневный бонус {DAILY_BONUS} монет!\n\n💰 Твой баланс: {balance} монет",
                reply_markup=main_keyboard()
            )
        else:
            await callback.message.edit_text(
                "⏳ Ты уже получил ежедневный бонус сегодня!\nПриходи завтра снова 🎰",
                reply_markup=main_keyboard()
            )
        await callback.answer()
    
    @dp.callback_query_handler(lambda c: c.data == "games")
    async def games_menu(callback: types.CallbackQuery):
        await callback.message.edit_text(
            "🎮 Выбери игру:",
            reply_markup=games_keyboard()
        )
        await callback.answer()
    
    @dp.callback_query_handler(lambda c: c.data == "leaderboard")
    async def leaderboard(callback: types.CallbackQuery):
        leaders = await Database.get_leaderboard(10)
        
        if not leaders:
            await callback.message.edit_text(
                "📊 Таблица лидеров пуста. Будь первым! 🏆",
                reply_markup=main_keyboard()
            )
            await callback.answer()
            return
        
        text = "🏆 ТАБЛИЦА ЛИДЕРОВ:\n\n"
        medals = ['🥇', '🥈', '🥉']
        
        for i, leader in enumerate(leaders):
            user_id, username, first_name, balance, wins, games = leader
            name = username if username else first_name
            medal = medals[i] if i < 3 else f"{i+1}."
            text += f"{medal} {name} - 💰{balance} (Побед: {wins})\n"
        
        await callback.message.edit_text(text, reply_markup=main_keyboard())
        await callback.answer()
    
    @dp.callback_query_handler(lambda c: c.data == "history")
    async def history(callback: types.CallbackQuery):
        await callback.message.edit_text(
            "📖 История игр будет доступна в следующей версии бота!",
            reply_markup=main_keyboard()
        )
        await callback.answer()
    
    # ОБРАБОТЧИКИ ИГР
    
    @dp.callback_query_handler(lambda c: c.data.startswith('game_'))
    async def game_handler(callback: types.CallbackQuery):
        game = callback.data.replace('game_', '')
        balance = await Database.get_balance(callback.from_user.id)
        
        if balance < MIN_BET:
            await callback.answer(f"❌ Недостаточно монет! Минимальная ставка: {MIN_BET}")
            return
        
        bets = [10, 50, 100, 500]
        keyboard = InlineKeyboardMarkup(row_width=2)
        
        for bet in bets:
            if bet <= balance:
                keyboard.insert(InlineKeyboardButton(
                    f"{bet}💰", 
                    callback_data=f"bet_{game}_{bet}"
                ))
        
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="games"))
        
        await callback.message.edit_text(
            f"🎮 {game.upper()}\n💰 Твой баланс: {balance}\n\nВыбери ставку:",
            reply_markup=keyboard
        )
        await callback.answer()
    
    @dp.callback_query_handler(lambda c: c.data.startswith('bet_'))
    async def play_game(callback: types.CallbackQuery):
        data = callback.data.split('_')
        game = data[1]
        bet = int(data[2])
        
        user_id = callback.from_user.id
        balance = await Database.get_balance(user_id)
        
        if balance < bet:
            await callback.answer("❌ Недостаточно монет!")
            return
        
        # Обработка разных игр
        if game == 'coin':
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton("🪙 Орёл", callback_data=f"play_coin_орел_{bet}"),
                InlineKeyboardButton("🪙 Решка", callback_data=f"play_coin_решка_{bet}")
            )
            keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="games"))
            
            await callback.message.edit_text(
                f"🪙 Орёл или Решка?\n💰 Ставка: {bet}",
                reply_markup=keyboard
            )
            await callback.answer()
            return
            
        elif game == 'dice':
            keyboard = InlineKeyboardMarkup(row_width=3)
            for i in range(1, 7):
                keyboard.insert(InlineKeyboardButton(
                    str(i), 
                    callback_data=f"play_dice_{i}_{bet}"
                ))
            keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="games"))
            
            await callback.message.edit_text(
                f"🎲 Угадай число (1-6)\n💰 Ставка: {bet}",
                reply_markup=keyboard
            )
            await callback.answer()
            return
            
        elif game == 'slot':
            win_amount, result_text = Games.slot_machine(bet)
            
            if win_amount > 0:
                await Database.update_balance(user_id, win_amount)
                await Database.update_stats(user_id, True)
                await Database.add_game_history(user_id, game, bet, win_amount, 'win')
                await callback.message.edit_text(
                    f"🎉 {result_text}\n\n💰 Баланс: {await Database.get_balance(user_id)}",
                    reply_markup=games_keyboard()
                )
            else:
                await Database.update_balance(user_id, win_amount)
                await Database.update_stats(user_id, False)
                await Database.add_game_history(user_id, game, bet, win_amount, 'loss')
                await callback.message.edit_text(
                    f"😢 {result_text}\n\n💰 Баланс: {await Database.get_balance(user_id)}",
                    reply_markup=games_keyboard()
                )
            await callback.answer()
            return
            
        elif game == 'hl':
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton("📈 Больше 50", callback_data=f"play_hl_higher_{bet}"),
                InlineKeyboardButton("📉 Меньше/равно 50", callback_data=f"play_hl_lower_{bet}")
            )
            keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="games"))
            
            await callback.message.edit_text(
                f"🔥 Больше или Меньше?\nЧисло от 1 до 100\n💰 Ставка: {bet}",
                reply_markup=keyboard
            )
            await callback.answer()
            return
    
    @dp.callback_query_handler(lambda c: c.data.startswith('play_'))
    async def play_game_choice(callback: types.CallbackQuery):
        data = callback.data.split('_')
        game = data[1]
        choice = data[2]
        bet = int(data[3])
        
        user_id = callback.from_user.id
        balance = await Database.get_balance(user_id)
        
        if balance < bet:
            await callback.answer("❌ Недостаточно монет!")
            return
        
        win_amount = 0
        result_text = ""
        
        if game == 'coin':
            win_amount, result_text = Games.coin_flip(bet, choice)
        elif game == 'dice':
            win_amount, result_text = Games.dice_game(bet, int(choice))
        elif game == 'hl':
            win_amount, result_text = Games.high_low(bet, choice)
        
        if win_amount > 0:
            await Database.update_balance(user_id, win_amount)
            await Database.update_stats(user_id, True)
            await Database.add_game_history(user_id, game, bet, win_amount, 'win')
            await callback.message.edit_text(
                f"🎉 {result_text}\n\n💰 Баланс: {await Database.get_balance(user_id)}",
                reply_markup=games_keyboard()
            )
        else:
            await Database.update_balance(user_id, win_amount)
            await Database.update_stats(user_id, False)
            await Database.add_game_history(user_id, game, bet, win_amount, 'loss')
            await callback.message.edit_text(
                f"😢 {result_text}\n\n💰 Баланс: {await Database.get_balance(user_id)}",
                reply_markup=games_keyboard()
            )
        await callback.answer()