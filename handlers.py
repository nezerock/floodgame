from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
import logging
import time
import random
import asyncio
import aiosqlite

from database import Database
from config import EMOJI, DAILY_BONUS, MIN_BET, MAX_BET, CLICK_COOLDOWN, MAX_CLICKS_PER_DAY, CLICK_REWARD, SHOP_ITEMS

user_cooldowns = {}
user_sessions = {}
user_messages = {}

class GameStates(StatesGroup):
    waiting_for_bet = State()
    waiting_for_hours = State()

async def save_message(user_id: int, msg):
    if user_id not in user_messages:
        user_messages[user_id] = []
    user_messages[user_id].append(msg)

async def clear_user_messages(user_id: int):
    if user_id in user_messages:
        for msg in user_messages[user_id]:
            try:
                await msg.delete()
            except:
                pass
        user_messages[user_id] = []

def main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"{EMOJI['coin']} Баланс", callback_data="balance"),
                InlineKeyboardButton(text=f"{EMOJI['diamond']} Бонус", callback_data="daily")
            ],
            [
                InlineKeyboardButton(text=f"{EMOJI['games']} Игры", callback_data="games"),
                InlineKeyboardButton(text=f"{EMOJI['leaderboard']} Лидеры", callback_data="leaderboard")
            ],
            [
                InlineKeyboardButton(text=f"{EMOJI['click']} Кликер", callback_data="clicker"),
                InlineKeyboardButton(text=f"{EMOJI['shop']} Магазин", callback_data="shop")
            ]
        ],
        row_width=2
    )

def games_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎲 Кости (1.7x)", callback_data="game_dice"),
                InlineKeyboardButton(text="🎰 Слоты (20x)", callback_data="game_slot")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
            ]
        ],
        row_width=2
    )

def bet_keyboard(game: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1💰", callback_data=f"bet_{game}_1"),
                InlineKeyboardButton(text="5💰", callback_data=f"bet_{game}_5"),
                InlineKeyboardButton(text="10💰", callback_data=f"bet_{game}_10")
            ],
            [
                InlineKeyboardButton(text="25💰", callback_data=f"bet_{game}_25"),
                InlineKeyboardButton(text="50💰", callback_data=f"bet_{game}_50"),
                InlineKeyboardButton(text="100💰", callback_data=f"bet_{game}_100")
            ],
            [
                InlineKeyboardButton(text="250💰", callback_data=f"bet_{game}_250"),
                InlineKeyboardButton(text="500💰", callback_data=f"bet_{game}_500"),
                InlineKeyboardButton(text="1000💰", callback_data=f"bet_{game}_1000")
            ],
            [
                InlineKeyboardButton(text="✏️ Ввести ставку", callback_data=f"custom_bet_{game}"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="games")
            ]
        ],
        row_width=3
    )

def shop_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1.3x (25💰)", callback_data="shop_1.3x"),
                InlineKeyboardButton(text="1.5x (40💰)", callback_data="shop_1.5x"),
                InlineKeyboardButton(text="2.0x (70💰)", callback_data="shop_2.0x")
            ],
            [
                InlineKeyboardButton(text="⏱ Ввести часы", callback_data="shop_time"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
            ]
        ],
        row_width=3
    )

async def get_boost(user_id):
    async with aiosqlite.connect("casino.db") as db:
        async with db.execute('SELECT boost_multiplier, boost_expiry FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0] and row[1]:
                expiry = datetime.fromisoformat(row[1])
                if datetime.now() < expiry:
                    return row[0]
    return 1.0

def register_handlers(dp: Dispatcher):

    @dp.message(Command("start", "help"))
    async def cmd_start(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        await state.clear()
        await clear_user_messages(user_id)
        user_sessions[user_id] = True
        
        await Database.create_user(user_id, message.from_user.username, message.from_user.first_name)
        balance = await Database.get_balance(user_id)
        boost = await get_boost(user_id)
        boost_text = f"\n🔥 Активный бонус: x{boost}" if boost > 1.0 else ""
        
        msg = await message.answer(
            text=f"🎮 Добро пожаловать в FLOOD GAMES, {message.from_user.first_name}!\n\n💰 Баланс: {balance} монет{boost_text}\n\n🎯 Доступные игры:\n• 🎲 Кости (x1.7)\n• 🎰 Слоты (x20)\n\n👆 Кликер - зарабатывай монеты!\n💎 Ежедневный бонус: {DAILY_BONUS} монет",
            reply_markup=main_keyboard()
        )
        await save_message(user_id, msg)
        await save_message(user_id, message)

    @dp.callback_query(F.data == "main_menu")
    async def main_menu(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        await state.clear()
        await clear_user_messages(user_id)
        balance = await Database.get_balance(user_id)
        msg = await callback.message.edit_text(
            text=f"🎮 Главное меню\n\n💰 Баланс: {balance} монет",
            reply_markup=main_keyboard()
        )
        await save_message(user_id, msg)
        await callback.answer()

    @dp.callback_query(F.data == "balance")
    async def show_balance(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        balance = await Database.get_balance(user_id)
        boost = await get_boost(user_id)
        boost_text = f"\n🔥 Активный бонус: x{boost}" if boost > 1.0 else ""
        msg = await callback.message.edit_text(
            text=f"💰 Баланс: {balance} монет{boost_text}",
            reply_markup=main_keyboard()
        )
        await save_message(user_id, msg)
        await callback.answer()

    @dp.callback_query(F.data == "daily")
    async def daily_bonus(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        if await Database.can_claim_daily(user_id):
            await Database.claim_daily(user_id)
            balance = await Database.get_balance(user_id)
            msg = await callback.message.edit_text(
                text=f"🎉 Бонус {DAILY_BONUS} монет получен!\n\n💰 Баланс: {balance} монет",
                reply_markup=main_keyboard()
            )
        else:
            msg = await callback.message.edit_text(
                text="⏳ Бонус уже получен сегодня!\nПриходи завтра.",
                reply_markup=main_keyboard()
            )
        await save_message(user_id, msg)
        await callback.answer()

    @dp.callback_query(F.data == "games")
    async def games_menu(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        await clear_user_messages(user_id)
        msg = await callback.message.edit_text(
            text="🎮 Выбери игру:",
            reply_markup=games_keyboard()
        )
        await save_message(user_id, msg)
        await callback.answer()

    @dp.callback_query(F.data == "leaderboard")
    async def leaderboard(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        leaders = await Database.get_leaderboard(10)
        if not leaders:
            msg = await callback.message.edit_text(
                text="📊 Таблица лидеров пуста!",
                reply_markup=main_keyboard()
            )
            await save_message(user_id, msg)
            await callback.answer()
            return
        text = "🏆 ТАБЛИЦА ЛИДЕРОВ:\n\n"
        medals = ['🥇', '🥈', '🥉']
        for i, leader in enumerate(leaders):
            user_id_db, username, first_name, balance, wins, games = leader
            name = username if username else first_name
            medal = medals[i] if i < 3 else f"{i+1}."
            text += f"{medal} {name} - 💰{balance:.1f} (Побед: {wins})\n"
        msg = await callback.message.edit_text(text=text, reply_markup=main_keyboard())
        await save_message(user_id, msg)
        await callback.answer()

    @dp.callback_query(F.data == "clicker")
    async def clicker(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        clicks_today = await Database.get_clicks_today(user_id)
        remaining = MAX_CLICKS_PER_DAY - clicks_today
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        if remaining > 0:
            keyboard.inline_keyboard.append([InlineKeyboardButton(text=f"👆 Кликнуть (+{CLICK_REWARD} монет)", callback_data="do_click")])
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])
        status = "🟢 Доступно" if remaining > 0 else "🔴 Лимит исчерпан"
        msg = await callback.message.edit_text(
            text=f"👆 КЛИКЕР\n\n💰 За клик: +{CLICK_REWARD} монет\n⏱ Кулдаун: {CLICK_COOLDOWN} сек\n📊 Сегодня: {clicks_today}/{MAX_CLICKS_PER_DAY}\n📈 Осталось: {remaining}\nСтатус: {status}",
            reply_markup=keyboard
        )
        await save_message(user_id, msg)
        await callback.answer()

    @dp.callback_query(F.data == "do_click")
    async def do_click(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        current_time = time.time()
        if user_id in user_cooldowns:
            if current_time - user_cooldowns[user_id] < CLICK_COOLDOWN:
                remaining = int(CLICK_COOLDOWN - (current_time - user_cooldowns[user_id]))
                await callback.answer(f"⏱ Подожди {remaining} сек!", show_alert=True)
                return
        clicks_today = await Database.get_clicks_today(user_id)
        if clicks_today >= MAX_CLICKS_PER_DAY:
            await callback.answer("❌ Лимит на сегодня!", show_alert=True)
            return
        await Database.add_click(user_id)
        user_cooldowns[user_id] = current_time
        balance = await Database.get_balance(user_id)
        clicks_today_new = await Database.get_clicks_today(user_id)
        remaining = MAX_CLICKS_PER_DAY - clicks_today_new
        await callback.answer(f"👆 +{CLICK_REWARD} монет! Баланс: {balance:.1f}", show_alert=False)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        if remaining > 0:
            keyboard.inline_keyboard.append([InlineKeyboardButton(text=f"👆 Кликнуть (+{CLICK_REWARD} монет)", callback_data="do_click")])
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])
        msg = await callback.message.edit_text(
            text=f"👆 КЛИКЕР\n\n✅ Клик засчитан!\n💰 Баланс: {balance:.1f}\n📊 Осталось: {remaining}",
            reply_markup=keyboard
        )
        await save_message(user_id, msg)

    @dp.callback_query(F.data == "shop")
    async def shop_menu(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        balance = await Database.get_balance(user_id)
        boost = await get_boost(user_id)
        boost_text = f"\n🔥 Активный бонус: x{boost}" if boost > 1.0 else "\n❌ Бонус не активен"
        msg = await callback.message.edit_text(
            text=f"🏪 МАГАЗИН\n\n💰 Баланс: {balance} монет{boost_text}\n\nВыбери бонус:",
            reply_markup=shop_keyboard()
        )
        await save_message(user_id, msg)
        await callback.answer()

    @dp.callback_query(F.data.startswith("shop_"))
    async def shop_buy(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        item_name = callback.data.replace('shop_', '')
        if item_name == 'time':
            await state.set_state(GameStates.waiting_for_hours)
            msg = await callback.message.edit_text(
                text="⏱ Отправь число часов (1-24):",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="shop")]]
                )
            )
            await save_message(user_id, msg)
            await callback.answer()
            return
        if item_name not in SHOP_ITEMS:
            await callback.answer("❌ Неверный выбор!")
            return
        item = SHOP_ITEMS[item_name]
        balance = await Database.get_balance(user_id)
        if balance < item['price']:
            await callback.answer(f"❌ Нужно: {item['price']} монет", show_alert=True)
            return
        await Database.update_balance(user_id, -item['price'])
        expiry = datetime.now() + timedelta(hours=1)
        async with aiosqlite.connect("casino.db") as db:
            await db.execute('UPDATE users SET boost_multiplier = ?, boost_expiry = ? WHERE user_id = ?', 
                            (item['multiplier'], expiry.isoformat(), user_id))
            await db.commit()
        balance = await Database.get_balance(user_id)
        msg = await callback.message.edit_text(
            text=f"✅ Куплен бонус x{item['multiplier']} на 1 час!\n\n💰 Баланс: {balance} монет",
            reply_markup=shop_keyboard()
        )
        await save_message(user_id, msg)
        await callback.answer()

    @dp.message(GameStates.waiting_for_hours)
    async def process_hours_input(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        try:
            hours = int(message.text.strip())
            if 1 <= hours <= 24:
                await message.delete()
                await message.answer(
                    text=f"⏱ Выбрано {hours} час(ов). Теперь выбери бонус в магазине!\n💡 Цена: бонус × {hours}",
                    reply_markup=shop_keyboard()
                )
                return
            else:
                await message.answer("❌ Введи число от 1 до 24!")
        except:
            await message.answer("❌ Введи число!")

    async def process_game(message: types.Message, game: str, bet: int, bot: Bot):
        user_id = message.from_user.id
        balance = await Database.get_balance(user_id)
        if balance < bet:
            await message.answer("❌ Недостаточно монет!")
            return
        boost = await get_boost(user_id)
        
        if game == 'dice':
            start_msg = await message.answer("🎲 НАЧИНАЕМ ИГРУ!")
            await save_message(user_id, start_msg)
            await asyncio.sleep(0.5)
            bot_dice = await bot.send_dice(chat_id=message.chat.id, emoji="🎲")
            await save_message(user_id, bot_dice)
            await asyncio.sleep(2.5)
            bot_roll = bot_dice.dice.value
            player_dice = await bot.send_dice(chat_id=message.chat.id, emoji="🎲")
            await save_message(user_id, player_dice)
            await asyncio.sleep(2.5)
            player_roll = player_dice.dice.value
            result_text = f"🤖 Бот: {bot_roll}\n🎯 Ты: {player_roll}\n\n"
            
            if player_roll > bot_roll:
                win = bet * 1.7 * boost
                await Database.update_balance(user_id, win)
                await Database.add_history(user_id, "dice", bet, win, "win")
                balance = await Database.get_balance(user_id)
                result_msg = await message.answer(
                    text=f"🏆 ТЫ ПОБЕДИЛ!\n{result_text}💰 +{win:.1f} монет! (x{1.7 * boost:.1f})\n\n💳 Баланс: {balance:.1f} монет",
                    reply_markup=games_keyboard()
                )
            elif player_roll < bot_roll:
                win = -bet
                await Database.update_balance(user_id, win)
                await Database.add_history(user_id, "dice", bet, win, "loss")
                balance = await Database.get_balance(user_id)
                result_msg = await message.answer(
                    text=f"😢 БОТ ПОБЕДИЛ!\n{result_text}💸 -{bet} монет!\n\n💳 Баланс: {balance:.1f} монет",
                    reply_markup=games_keyboard()
                )
            else:
                await Database.add_history(user_id, "dice", bet, 0, "draw")
                balance = await Database.get_balance(user_id)
                result_msg = await message.answer(
                    text=f"🤝 НИЧЬЯ!\n{result_text}💳 Баланс: {balance:.1f} монет",
                    reply_markup=games_keyboard()
                )
            await save_message(user_id, result_msg)
        
        elif game == 'slot':
            start_msg = await message.answer("🎰 КРУТИМ БАРАБАНЫ...")
            await save_message(user_id, start_msg)
            await asyncio.sleep(0.5)
            slot_msg = await bot.send_dice(chat_id=message.chat.id, emoji="🎰")
            await save_message(user_id, slot_msg)
            await asyncio.sleep(3.0)
            slot_value = slot_msg.dice.value
            
            slot_combinations = {
                1: ['🍋', '🍋', '🍋'],
                2: ['🍇', '🍇', '🍇'],
                3: ['📼', '📼', '📼'],
                4: ['7️⃣', '7️⃣', '7️⃣'],
            }
            slot1, slot2, slot3 = slot_combinations[slot_value]
            
            if slot1 == slot2 == slot3:
                if slot1 == '7️⃣':
                    win = bet * 20 * boost
                    text = f"🎰 ДЖЕКПОТ!\n💰 +{win:.1f} монет! (x{20 * boost:.1f})"
                elif slot1 == '📼':
                    win = bet * 10 * boost
                    text = f"📼 ТРИ БАРА!\n💰 +{win:.1f} монет! (x{10 * boost:.1f})"
                else:
                    win = bet * 5 * boost
                    text = f"🎰 ТРИ В РЯД!\n💰 +{win:.1f} монет! (x{5 * boost:.1f})"
                await Database.update_balance(user_id, win)
                await Database.add_history(user_id, "slot", bet, win, "win")
            elif slot1 == slot2 or slot2 == slot3:
                win = bet
                text = f"🔄 ДВА В РЯД!\nВозврат ставки"
                await Database.add_history(user_id, "slot", bet, win, "draw")
            else:
                win = -bet
                await Database.update_balance(user_id, win)
                text = f"❌ Нет совпадений!\n💸 -{bet} монет!"
                await Database.add_history(user_id, "slot", bet, win, "loss")
            
            balance = await Database.get_balance(user_id)
            result_msg = await message.answer(
                text=f"🎰 {slot1} {slot2} {slot3}\n\n{text}\n\n💳 Баланс: {balance:.1f} монет",
                reply_markup=games_keyboard()
            )
            await save_message(user_id, result_msg)

    @dp.callback_query(F.data.startswith("game_"))
    async def game_handler(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        game = callback.data.replace('game_', '')
        balance = await Database.get_balance(user_id)
        if balance < MIN_BET:
            await callback.answer(f"❌ Минимальная ставка: {MIN_BET}", show_alert=True)
            return
        msg = await callback.message.edit_text(
            text=f"🎮 {game.upper()}\n💰 Баланс: {balance:.1f} монет\n\nВыбери ставку:",
            reply_markup=bet_keyboard(game)
        )
        await save_message(user_id, msg)
        await callback.answer()

    @dp.callback_query(F.data.startswith("bet_"))
    async def play_game(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        
        data = callback.data.split('_')
        game = data[1]
        bet = int(data[2])
        
        balance = await Database.get_balance(user_id)
        if balance < bet:
            await callback.answer("❌ Недостаточно монет!", show_alert=True)
            return
        
        await state.clear()
        
        # НЕ УДАЛЯЕМ СООБЩЕНИЕ, А РЕДАКТИРУЕМ ЕГО!
        msg = await callback.message.edit_text("🎮 Начинаем игру...")
        await save_message(user_id, msg)
        
        await process_game(msg, game, bet, callback.bot)
        await callback.answer()

    @dp.callback_query(F.data.startswith("custom_bet_"))
    async def custom_bet(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        game = callback.data.replace('custom_bet_', '')
        await state.set_state(GameStates.waiting_for_bet)
        await state.update_data(game=game)
        msg = await callback.message.edit_text(
            text=f"✏️ Введи ставку от {MIN_BET} до {MAX_BET}:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="games")]]
            )
        )
        await save_message(user_id, msg)
        await callback.answer()

    @dp.message(GameStates.waiting_for_bet)
    async def process_bet_input(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        try:
            bet = int(message.text.strip())
            if MIN_BET <= bet <= MAX_BET:
                if user_id not in user_sessions:
                    await message.answer("❌ Напиши /start!")
                    await state.clear()
                    return
                data = await state.get_data()
                game = data.get('game', 'dice')
                await state.clear()
                await message.delete()
                msg = await message.answer("🎮 Начинаем игру...")
                await save_message(user_id, msg)
                await process_game(msg, game, bet, message.bot)
                return
            else:
                await message.answer(f"❌ Ставка от {MIN_BET} до {MAX_BET}!")
        except:
            await message.answer("❌ Введи число!")
