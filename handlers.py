from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import Text

from database import Database
from games import Games
from config import EMOJI, DAILY_BONUS, MIN_BET, MAX_BET, CLICK_COOLDOWN, MAX_CLICKS_PER_DAY, CLICK_REWARD
import time

# Хранилище для кулдауна кликов
user_cooldowns = {}

def main_keyboard():
    """Главное меню"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(f"{EMOJI['coin']} Баланс", callback_data="balance"),
        InlineKeyboardButton(f"{EMOJI['diamond']} Бонус", callback_data="daily"),
        InlineKeyboardButton(f"{EMOJI['games']} Игры", callback_data="games"),
        InlineKeyboardButton(f"{EMOJI['leaderboard']} Лидеры", callback_data="leaderboard"),
        InlineKeyboardButton(f"{EMOJI['click']} Кликер", callback_data="clicker")
    )
    return keyboard

def games_keyboard():
    """Меню игр"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(f"🎲 Кости (бот vs ты)", callback_data="game_dice"),
        InlineKeyboardButton(f"🪙 Орёл/Решка", callback_data="game_coin"),
        InlineKeyboardButton(f"🎰 Слоты", callback_data="game_slot"),
        InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
    )
    return keyboard

def bet_keyboard(game: str):
    """Клавиатура для ставок"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("1💰", callback_data=f"bet_{game}_1"),
        InlineKeyboardButton("5💰", callback_data=f"bet_{game}_5"),
        InlineKeyboardButton("10💰", callback_data=f"bet_{game}_10"),
        InlineKeyboardButton("25💰", callback_data=f"bet_{game}_25"),
        InlineKeyboardButton("50💰", callback_data=f"bet_{game}_50"),
        InlineKeyboardButton("100💰", callback_data=f"bet_{game}_100"),
        InlineKeyboardButton("250💰", callback_data=f"bet_{game}_250"),
        InlineKeyboardButton("500💰", callback_data=f"bet_{game}_500"),
        InlineKeyboardButton("1000💰", callback_data=f"bet_{game}_1000"),
        InlineKeyboardButton("🔙 Назад", callback_data="games")
    )
    return keyboard

def register_handlers(dp: Dispatcher):
    
    @dp.message_handler(commands=['start', 'help'])
    async def cmd_start(message: types.Message):
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        
        await Database.create_user(user_id, username, first_name)
        balance = await Database.get_balance(user_id)
        
        welcome_text = f"""
🎮 Добро пожаловать в FLOOD GAMES, {first_name}!

💰 Твой баланс: {balance} монет

🎯 Доступные игры:
• 🎲 Кости - сразись с ботом
• 🪙 Орёл/Решка - угадай сторону
• 🎰 Слоты - три в ряд

👆 Кликер - зарабатывай монеты!

💎 Ежедневный бонус: {DAILY_BONUS} монет
"""
        
        await message.answer(welcome_text, reply_markup=main_keyboard())
    
    @dp.callback_query_handler(lambda c: c.data == "main_menu")
    async def main_menu(callback: types.CallbackQuery):
        balance = await Database.get_balance(callback.from_user.id)
        await callback.message.edit_text(
            f"🎮 Главное меню\n\n💰 Баланс: {balance} монет",
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
                "⏳ Ты уже получил ежедневный бонус сегодня!\nПриходи завтра снова 💎",
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
    
    @dp.callback_query_handler(lambda c: c.data == "clicker")
    async def clicker(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        clicks_today = await Database.get_clicks_today(user_id)
        remaining = MAX_CLICKS_PER_DAY - clicks_today
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        if remaining > 0:
            keyboard.add(InlineKeyboardButton(f"👆 Кликнуть (+{CLICK_REWARD} монет)", callback_data="do_click"))
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
        
        status = "🟢 Доступно" if remaining > 0 else "🔴 Лимит исчерпан"
        await callback.message.edit_text(
            f"👆 КЛИКЕР\n\n"
            f"💰 За каждый клик: +{CLICK_REWARD} монет\n"
            f"⏱ Кулдаун: {CLICK_COOLDOWN} сек\n"
            f"📊 Кликов сегодня: {clicks_today}/{MAX_CLICKS_PER_DAY}\n"
            f"📈 Осталось: {remaining}\n"
            f"Статус: {status}",
            reply_markup=keyboard
        )
        await callback.answer()
    
    @dp.callback_query_handler(lambda c: c.data == "do_click")
    async def do_click(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        
        # Проверка кулдауна
        current_time = time.time()
        if user_id in user_cooldowns:
            if current_time - user_cooldowns[user_id] < CLICK_COOLDOWN:
                remaining = int(CLICK_COOLDOWN - (current_time - user_cooldowns[user_id]))
                await callback.answer(f"⏱ Подожди {remaining} сек!", show_alert=True)
                return
        
        # Проверка лимита на день
        clicks_today = await Database.get_clicks_today(user_id)
        if clicks_today >= MAX_CLICKS_PER_DAY:
            await callback.answer("❌ Лимит кликов на сегодня исчерпан!", show_alert=True)
            return
        
        # Выполняем клик
        await Database.add_click(user_id)
        user_cooldowns[user_id] = current_time
        balance = await Database.get_balance(user_id)
        clicks_today_new = await Database.get_clicks_today(user_id)
        remaining = MAX_CLICKS_PER_DAY - clicks_today_new
        
        await callback.answer(f"👆 +{CLICK_REWARD} монет! Баланс: {balance}", show_alert=False)
        
        # Обновляем сообщение
        keyboard = InlineKeyboardMarkup(row_width=1)
        if remaining > 0:
            keyboard.add(InlineKeyboardButton(f"👆 Кликнуть (+{CLICK_REWARD} монет)", callback_data="do_click"))
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
        
        await callback.message.edit_text(
            f"👆 КЛИКЕР\n\n"
            f"💰 За каждый клик: +{CLICK_REWARD} монет\n"
            f"⏱ Кулдаун: {CLICK_COOLDOWN} сек\n"
            f"📊 Кликов сегодня: {clicks_today_new}/{MAX_CLICKS_PER_DAY}\n"
            f"📈 Осталось: {remaining}\n"
            f"✅ Последний клик засчитан!",
            reply_markup=keyboard
        )
    
    # Обработчики игр
    @dp.callback_query_handler(lambda c: c.data.startswith('game_'))
    async def game_handler(callback: types.CallbackQuery):
        game = callback.data.replace('game_', '')
        balance = await Database.get_balance(callback.from_user.id)
        
        if balance < MIN_BET:
            await callback.answer(f"❌ Недостаточно монет! Минимальная ставка: {MIN_BET}")
            return
        
        await callback.message.edit_text(
            f"🎮 {game.upper()}\n💰 Твой баланс: {balance}\n\nВыбери ставку:",
            reply_markup=bet_keyboard(game)
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
        
        win_amount = 0
        result_text = ""
        is_win = False
        
        # Запуск игр
        if game == 'dice':
            # Для игры в кости - сразу кидаем
            win_amount, is_win, result_text = Games.dice_game(bet)
            
        elif game == 'coin':
            # Для орла/решки - просим выбрать
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
            
        elif game == 'slot':
            win_amount, result_text = Games.slot_machine(bet)
            is_win = win_amount > 0
        
        # Обновление баланса и статистики
        if win_amount > 0:
            await Database.update_balance(user_id, win_amount)
            await Database.update_stats(user_id, True)
            await Database.add_game_history(user_id, game, bet, win_amount, 'win')
        elif win_amount < 0:
            await Database.update_balance(user_id, win_amount)
            await Database.update_stats(user_id, False)
            await Database.add_game_history(user_id, game, bet, win_amount, 'loss')
        else:
            # Ничья
            await Database.add_game_history(user_id, game, bet, 0, 'draw')
        
        balance = await Database.get_balance(user_id)
        await callback.message.edit_text(
            f"{result_text}\n\n💰 Баланс: {balance} монет",
            reply_markup=games_keyboard()
        )
        await callback.answer()
    
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
        
        win_amount, result_text = Games.coin_flip(bet, choice)
        is_win = win_amount > 0
        
        if win_amount > 0:
            await Database.update_balance(user_id, win_amount)
            await Database.update_stats(user_id, True)
            await Database.add_game_history(user_id, game, bet, win_amount, 'win')
        else:
            await Database.update_balance(user_id, win_amount)
            await Database.update_stats(user_id, False)
            await Database.add_game_history(user_id, game, bet, win_amount, 'loss')
        
        balance = await Database.get_balance(user_id)
        await callback.message.edit_text(
            f"{result_text}\n\n💰 Баланс: {balance} монет",
            reply_markup=games_keyboard()
        )
        await callback.answer()
