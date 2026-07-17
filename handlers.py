from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import logging

from database import Database
from config import EMOJI, DAILY_BONUS, MIN_BET, MAX_BET, CLICK_COOLDOWN, MAX_CLICKS_PER_DAY, CLICK_REWARD, SHOP_ITEMS
import time
import random
import asyncio

user_cooldowns = {}
user_sessions = {}
user_messages = {}  # user_id -> список сообщений для удаления

class GameStates(StatesGroup):
    waiting_for_bet = State()
    waiting_for_hours = State()
    waiting_for_shop_confirm = State()

async def save_message(user_id: int, msg):
    """Сохраняем сообщение для последующего удаления"""
    if user_id not in user_messages:
        user_messages[user_id] = []
    user_messages[user_id].append(msg)

async def clear_user_messages(user_id: int, keep_last: int = 0):
    """Удаляем все сообщения пользователя, кроме последних keep_last"""
    if user_id in user_messages:
        # Оставляем только последние keep_last сообщений
        if keep_last > 0 and len(user_messages[user_id]) > keep_last:
            to_delete = user_messages[user_id][:-keep_last]
            for msg in to_delete:
                try:
                    await msg.delete()
                except:
                    pass
            user_messages[user_id] = user_messages[user_id][-keep_last:]
        else:
            for msg in user_messages[user_id]:
                try:
                    await msg.delete()
                except:
                    pass
            user_messages[user_id] = []

async def delete_message_later(msg, delay: int):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass

def main_keyboard():
    keyboard = InlineKeyboardMarkup(
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
    return keyboard

def games_keyboard():
    keyboard = InlineKeyboardMarkup(
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
    return keyboard

def bet_keyboard(game: str):
    keyboard = InlineKeyboardMarkup(
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
    return keyboard

def shop_keyboard():
    keyboard = InlineKeyboardMarkup(
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
    return keyboard

def register_handlers(dp: Dispatcher):
    
    @dp.message(Command("start", "help"))
    async def cmd_start(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        
        await state.clear()
        
        # Удаляем старые сообщения
        await clear_user_messages(user_id)
        
        # Создаём новую сессию (удаляем старую)
        user_sessions[user_id] = True
        
        username = message.from_user.username
        first_name = message.from_user.first_name
        
        await Database.create_user(user_id, username, first_name)
        balance = await Database.get_balance(user_id)
        boost, _ = await Database.get_boost(user_id)
        
        boost_text = f"\n🔥 Активный бонус: x{boost}" if boost > 1.0 else ""
        
        welcome_text = f"""
🎮 Добро пожаловать в FLOOD GAMES, {first_name}!

💰 Баланс: {balance} монет{boost_text}

🎯 Доступные игры:
• 🎲 Кости (x1.7) - сразись с ботом
• 🎰 Слоты (x20) - три в ряд

👆 Кликер - зарабатывай монеты!

💎 Ежедневный бонус: {DAILY_BONUS} монет
"""
        
        msg = await message.answer(welcome_text, reply_markup=main_keyboard())
        await save_message(user_id, msg)
        await save_message(user_id, message)
        logging.info(f"📩 /start от {user_id}")
    
    @dp.callback_query(F.data == "main_menu")
    async def main_menu(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        await state.clear()
        
        # Удаляем все сообщения, кроме последнего
        await clear_user_messages(user_id, keep_last=1)
        
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
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        balance = await Database.get_balance(user_id)
        boost, _ = await Database.get_boost(user_id)
        boost_text = f"\n🔥 Активный бонус: x{boost}" if boost > 1.0 else ""
        
        await callback.message.edit_text(
            text=f"💰 Баланс: {balance} монет{boost_text}",
            reply_markup=main_keyboard()
        )
        await callback.answer()
    
    @dp.callback_query(F.data == "daily")
    async def daily_bonus(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        if await Database.can_claim_daily(user_id):
            await Database.claim_daily(user_id)
            balance = await Database.get_balance(user_id)
            await callback.message.edit_text(
                text=f"🎉 Ты получил ежедневный бонус {DAILY_BONUS} монет!\n\n💰 Баланс: {balance} монет",
                reply_markup=main_keyboard()
            )
        else:
            await callback.message.edit_text(
                text="⏳ Ты уже получил ежедневный бонус сегодня!\nПриходи завтра снова 💎",
                reply_markup=main_keyboard()
            )
        await callback.answer()
    
    @dp.callback_query(F.data == "games")
    async def games_menu(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        await callback.message.edit_text(
            text="🎮 Выбери игру:",
            reply_markup=games_keyboard()
        )
        await callback.answer()
    
    @dp.callback_query(F.data == "leaderboard")
    async def leaderboard(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        leaders = await Database.get_leaderboard(10)
        
        if not leaders:
            await callback.message.edit_text(
                text="📊 Таблица лидеров пуста. Будь первым! 🏆",
                reply_markup=main_keyboard()
            )
            await callback.answer()
            return
        
        text = "🏆 ТАБЛИЦА ЛИДЕРОВ:\n\n"
        medals = ['🥇', '🥈', '🥉']
        
        for i, leader in enumerate(leaders):
            user_id_db, username, first_name, balance, wins, games = leader
            name = username if username else first_name
            medal = medals[i] if i < 3 else f"{i+1}."
            text += f"{medal} {name} - 💰{balance:.1f} (Побед: {wins})\n"
        
        await callback.message.edit_text(text=text, reply_markup=main_keyboard())
        await callback.answer()
    
    @dp.callback_query(F.data == "clicker")
    async def clicker(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        clicks_today = await Database.get_clicks_today(user_id)
        remaining = MAX_CLICKS_PER_DAY - clicks_today
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        if remaining > 0:
            keyboard.inline_keyboard.append([InlineKeyboardButton(text=f"👆 Кликнуть (+{CLICK_REWARD} монет)", callback_data="do_click")])
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])
        
        status = "🟢 Доступно" if remaining > 0 else "🔴 Лимит исчерпан"
        await callback.message.edit_text(
            text=f"👆 КЛИКЕР\n\n"
            f"💰 За каждый клик: +{CLICK_REWARD} монет\n"
            f"⏱ Кулдаун: {CLICK_COOLDOWN} сек\n"
            f"📊 Кликов сегодня: {clicks_today}/{MAX_CLICKS_PER_DAY}\n"
            f"📈 Осталось: {remaining}\n"
            f"Статус: {status}",
            reply_markup=keyboard
        )
        await callback.answer()
    
    @dp.callback_query(F.data == "do_click")
    async def do_click(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        current_time = time.time()
        if user_id in user_cooldowns:
            if current_time - user_cooldowns[user_id] < CLICK_COOLDOWN:
                remaining = int(CLICK_COOLDOWN - (current_time - user_cooldowns[user_id]))
                await callback.answer(f"⏱ Подожди {remaining} сек!", show_alert=True)
                return
        
        clicks_today = await Database.get_clicks_today(user_id)
        if clicks_today >= MAX_CLICKS_PER_DAY:
            await callback.answer("❌ Лимит кликов на сегодня исчерпан!", show_alert=True)
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
        
        await callback.message.edit_text(
            text=f"👆 КЛИКЕР\n\n"
            f"💰 За каждый клик: +{CLICK_REWARD} монет\n"
            f"⏱ Кулдаун: {CLICK_COOLDOWN} сек\n"
            f"📊 Кликов сегодня: {clicks_today_new}/{MAX_CLICKS_PER_DAY}\n"
            f"📈 Осталось: {remaining}\n"
            f"✅ Последний клик засчитан!",
            reply_markup=keyboard
        )
    
    @dp.callback_query(F.data == "shop")
    async def shop_menu(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        balance = await Database.get_balance(user_id)
        boost, expiry = await Database.get_boost(user_id)
        
        boost_text = f"\n🔥 Активный бонус: x{boost}" if boost > 1.0 else "\n❌ Бонус не активен"
        if boost > 1.0 and expiry:
            expiry_time = datetime.fromisoformat(expiry)
            remaining = expiry_time - datetime.now()
            boost_text += f"\n⏱ Осталось: {remaining.seconds // 3600}ч {remaining.seconds % 3600 // 60}м"
        
        await callback.message.edit_text(
            text=f"🏪 МАГАЗИН БОНУСОВ\n\n"
            f"💰 Баланс: {balance} монет{boost_text}\n\n"
            f"Выбери бонус к выигрышу (действует 1 час):",
            reply_markup=shop_keyboard()
        )
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("shop_"))
    async def shop_buy(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        item_name = callback.data.replace('shop_', '')
        
        if item_name == 'time':
            await state.set_state(GameStates.waiting_for_hours)
            await callback.message.edit_text(
                text="⏱ Отправь сообщением количество часов (1-24):\n\n"
                "💡 Стоимость: цена бонуса × количество часов\n"
                "Пример: для бонуса x1.3 (25💰) на 3 часа = 75💰",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="shop")]],
                    row_width=1
                )
            )
            await callback.answer()
            return
        
        if item_name not in SHOP_ITEMS:
            await callback.answer("❌ Неверный выбор!")
            return
        
        await state.update_data(item=item_name, hours=1)
        await state.set_state(GameStates.waiting_for_shop_confirm)
        
        item = SHOP_ITEMS[item_name]
        balance = await Database.get_balance(user_id)
        
        if balance < item['price']:
            await callback.answer(f"❌ Недостаточно монет! Нужно: {item['price']}", show_alert=True)
            return
        
        await callback.message.edit_text(
            text=f"✅ Выбран бонус x{item['multiplier']}\n"
            f"💰 Цена: {item['price']} монет за 1 час\n"
            f"⏱ Длительность: 1 час\n\n"
            f"Нажми 'Купить' для подтверждения или измени время:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Купить", callback_data=f"shop_confirm_{item_name}_1")],
                    [InlineKeyboardButton(text="⏱ Изменить время", callback_data="shop_time")],
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="shop")]
                ],
                row_width=1
            )
        )
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("shop_confirm_"))
    async def shop_confirm(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        data = callback.data.split('_')
        item_name = data[2]
        hours = int(data[3])
        
        if item_name not in SHOP_ITEMS:
            await callback.answer("❌ Неверный выбор!")
            return
        
        await state.clear()
        
        item = SHOP_ITEMS[item_name]
        total_price = item['price'] * hours
        balance = await Database.get_balance(user_id)
        
        if balance < total_price:
            await callback.answer(f"❌ Недостаточно монет! Нужно: {total_price}", show_alert=True)
            return
        
        await Database.update_balance(user_id, -total_price)
        await Database.set_boost(user_id, item['multiplier'], hours)
        balance = await Database.get_balance(user_id)
        
        await callback.message.edit_text(
            text=f"✅ Куплен бонус x{item['multiplier']} на {hours} час(ов)!\n\n"
            f"💰 Баланс: {balance} монет\n"
            f"🔥 Теперь выигрыши увеличены в {item['multiplier']}x!",
            reply_markup=shop_keyboard()
        )
        await callback.answer()
    
    @dp.callback_query(F.data == "shop_time")
    async def shop_time_input(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        await state.set_state(GameStates.waiting_for_hours)
        await callback.message.edit_text(
            text="⏱ Отправь сообщением количество часов (1-24):\n\n"
            "💡 Стоимость: цена бонуса × количество часов\n"
            "Пример: для бонуса x1.3 (25💰) на 3 часа = 75💰",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="shop")]],
                row_width=1
            )
        )
        await callback.answer()
    
    @dp.message(GameStates.waiting_for_hours)
    async def process_hours_input(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        
        try:
            hours = int(message.text.strip())
            if 1 <= hours <= 24:
                await state.update_data(hours=hours)
                
                data = await state.get_data()
                if 'item' in data:
                    item_name = data['item']
                    item = SHOP_ITEMS[item_name]
                    total_price = item['price'] * hours
                    
                    await message.delete()
                    
                    await state.set_state(GameStates.waiting_for_shop_confirm)
                    
                    await message.answer(
                        text=f"✅ Выбрано {hours} час(ов) для бонуса x{item['multiplier']}\n"
                        f"💰 Цена: {total_price} монет\n\n"
                        f"Нажми 'Купить' для подтверждения:",
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(text="✅ Купить", callback_data=f"shop_confirm_{item_name}_{hours}")],
                                [InlineKeyboardButton(text="🔙 Назад", callback_data="shop")]
                            ],
                            row_width=1
                        )
                    )
                else:
                    await message.answer(
                        text="⚠️ Сначала выбери бонус в магазине!",
                        reply_markup=shop_keyboard()
                    )
                return
            else:
                await message.answer("❌ Введи число от 1 до 24!")
        except:
            await message.answer("❌ Введи число!")
    
    @dp.message(GameStates.waiting_for_bet)
    async def process_bet_input(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        
        try:
            bet = int(message.text.strip())
            if MIN_BET <= bet <= MAX_BET:
                if user_id not in user_sessions:
                    await message.answer("❌ Напиши /start чтобы начать!")
                    await state.clear()
                    return
                
                data = await state.get_data()
                game = data.get('game', 'dice')
                
                await state.clear()
                await message.delete()
                await process_game(message, game, bet, message.bot)
                return
            else:
                await message.answer(f"❌ Ставка должна быть от {MIN_BET} до {MAX_BET}!")
        except:
            await message.answer("❌ Введи число!")
    
    async def process_game(message: types.Message, game: str, bet: int, bot: Bot):
        user_id = message.from_user.id
        balance = await Database.get_balance(user_id)
        
        if balance < bet:
            await message.answer("❌ Недостаточно монет!")
            return
        
        boost, _ = await Database.get_boost(user_id)
        
        if game == 'dice':
            # ========== КОСТИ ==========
            start_msg = await message.answer("🎲 НАЧИНАЕМ ИГРУ В КОСТИ!")
            await save_message(user_id, start_msg)
            
            # Бот кидает кубик
            await asyncio.sleep(0.5)
            bot_dice = await bot.send_dice(chat_id=message.chat.id, emoji="🎲")
            await save_message(user_id, bot_dice)
            
            # Ждём анимацию
            await asyncio.sleep(2.5)
            bot_roll = bot_dice.dice.value
            
            # Игрок кидает кубик
            await asyncio.sleep(0.5)
            player_dice = await bot.send_dice(chat_id=message.chat.id, emoji="🎲")
            await save_message(user_id, player_dice)
            
            await asyncio.sleep(2.5)
            player_roll = player_dice.dice.value
            
            # Результат
            await asyncio.sleep(0.5)
            result_text = (
                f"🤖 Бросок бота: {bot_roll}\n"
                f"🎯 Твой бросок: {player_roll}\n\n"
            )
            
            if player_roll > bot_roll:
                win_amount = bet * 1.7 * boost
                await Database.update_balance(user_id, win_amount)
                await Database.update_stats(user_id, True)
                await Database.add_game_history(user_id, game, bet, win_amount, 'win')
                balance = await Database.get_balance(user_id)
                result_msg = await message.answer(
                    text=f"🏆 ТЫ ПОБЕДИЛ!\n{result_text}"
                    f"💰 +{win_amount:.1f} монет! (x{1.7 * boost:.1f})\n\n"
                    f"💳 Баланс: {balance:.1f} монет",
                    reply_markup=games_keyboard()
                )
            elif player_roll < bot_roll:
                win_amount = -bet  # ОТРИЦАТЕЛЬНОЕ ЗНАЧЕНИЕ!
                await Database.update_balance(user_id, win_amount)  # СПИСЫВАЕМ!
                await Database.update_stats(user_id, False)
                await Database.add_game_history(user_id, game, bet, win_amount, 'loss')
                balance = await Database.get_balance(user_id)
                result_msg = await message.answer(
                    text=f"😢 БОТ ПОБЕДИЛ!\n{result_text}"
                    f"💸 -{bet} монет!\n\n"
                    f"💳 Баланс: {balance:.1f} монет",
                    reply_markup=games_keyboard()
                )
            else:
                await Database.add_game_history(user_id, game, bet, 0, 'draw')
                balance = await Database.get_balance(user_id)
                result_msg = await message.answer(
                    text=f"🤝 НИЧЬЯ!\n{result_text}"
                    f"💳 Баланс: {balance:.1f} монет",
                    reply_markup=games_keyboard()
                )
            await save_message(user_id, result_msg)
        
        elif game == 'slot':
            # ========== СЛОТЫ ==========
            start_msg = await message.answer("🎰 КРУТИМ БАРАБАНЫ...")
            await save_message(user_id, start_msg)
            
            # Отправляем слот
            await asyncio.sleep(0.5)
            slot_msg = await bot.send_dice(chat_id=message.chat.id, emoji="🎰")
            await save_message(user_id, slot_msg)
            
            # Ждём анимацию
            await asyncio.sleep(3.0)
            slot_value = slot_msg.dice.value
            
            # Правильные эмодзи для слотов
            slot_combinations = {
                1: ['🍒', '🍒', '🍒'],
                2: ['🍋', '🍋', '🍋'],
                3: ['🍊', '🍊', '🍊'],
                4: ['🍇', '🍇', '🍇'],
                5: ['🔔', '🔔', '🔔'],
                6: ['💎', '💎', '💎'],
            }
            
            if slot_value in slot_combinations:
                slot1, slot2, slot3 = slot_combinations[slot_value]
            else:
                # Резерв - но такого не должно быть
                symbols = ['🍒', '🍋', '🍊', '🍇', '🔔', '💎', '7️⃣']
                slot1 = random.choice(symbols)
                slot2 = random.choice(symbols)
                slot3 = random.choice(symbols)
            
            await asyncio.sleep(0.5)
            
            # Результат
            if slot1 == slot2 == slot3:
                if slot1 == '💎':
                    win = bet * 20 * boost
                    await Database.update_balance(user_id, win)
                    await Database.update_stats(user_id, True)
                    await Database.add_game_history(user_id, game, bet, win, 'win')
                    balance = await Database.get_balance(user_id)
                    result_msg = await message.answer(
                        text=f"🎰 {slot1} {slot2} {slot3} 💎 ДЖЕКПОТ!\n"
                        f"💰 +{win:.1f} монет! (x{20 * boost:.1f})\n\n"
                        f"💳 Баланс: {balance:.1f} монет",
                        reply_markup=games_keyboard()
                    )
                elif slot1 == '7️⃣':
                    win = bet * 15 * boost
                    await Database.update_balance(user_id, win)
                    await Database.update_stats(user_id, True)
                    await Database.add_game_history(user_id, game, bet, win, 'win')
                    balance = await Database.get_balance(user_id)
                    result_msg = await message.answer(
                        text=f"🎰 {slot1} {slot2} {slot3} 🎰 СЕМЁРКИ!\n"
                        f"💰 +{win:.1f} монет! (x{15 * boost:.1f})\n\n"
                        f"💳 Баланс: {balance:.1f} монет",
                        reply_markup=games_keyboard()
                    )
                else:
                    win = bet * 10 * boost
                    await Database.update_balance(user_id, win)
                    await Database.update_stats(user_id, True)
                    await Database.add_game_history(user_id, game, bet, win, 'win')
                    balance = await Database.get_balance(user_id)
                    result_msg = await message.answer(
                        text=f"🎰 {slot1} {slot2} {slot3} 🎰 ТРИ В РЯД!\n"
                        f"💰 +{win:.1f} монет! (x{10 * boost:.1f})\n\n"
                        f"💳 Баланс: {balance:.1f} монет",
                        reply_markup=games_keyboard()
                    )
            elif slot1 == slot2 or slot2 == slot3:
                await Database.add_game_history(user_id, game, bet, bet, 'draw')
                balance = await Database.get_balance(user_id)
                result_msg = await message.answer(
                    text=f"🎰 {slot1} {slot2} {slot3} 🔄 ДВА В РЯД!\n"
                    f"💳 Баланс: {balance:.1f} монет",
                    reply_markup=games_keyboard()
                )
            else:
                win = -bet  # ОТРИЦАТЕЛЬНОЕ ЗНАЧЕНИЕ!
                await Database.update_balance(user_id, win)  # СПИСЫВАЕМ!
                await Database.update_stats(user_id, False)
                await Database.add_game_history(user_id, game, bet, win, 'loss')
                balance = await Database.get_balance(user_id)
                result_msg = await message.answer(
                    text=f"🎰 {slot1} {slot2} {slot3} ❌ Ничего не совпало!\n"
                    f"💸 -{bet} монет!\n\n"
                    f"💳 Баланс: {balance:.1f} монет",
                    reply_markup=games_keyboard()
                )
            await save_message(user_id, result_msg)
    
    @dp.callback_query(F.data.startswith("game_"))
    async def game_handler(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        game = callback.data.replace('game_', '')
        balance = await Database.get_balance(user_id)
        
        if balance < MIN_BET:
            await callback.answer(f"❌ Недостаточно монет! Минимальная ставка: {MIN_BET}")
            return
        
        await callback.message.edit_text(
            text=f"🎮 {game.upper()}\n💰 Баланс: {balance:.1f} монет\n\nВыбери ставку:",
            reply_markup=bet_keyboard(game)
        )
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("bet_"))
    async def play_game(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        data = callback.data.split('_')
        game = data[1]
        bet = int(data[2])
        
        balance = await Database.get_balance(user_id)
        if balance < bet:
            await callback.answer("❌ Недостаточно монет!")
            return
        
        await state.clear()
        
        # Удаляем сообщение со ставкой
        await callback.message.delete()
        
        await process_game(callback.message, game, bet, callback.bot)
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("custom_bet_"))
    async def custom_bet(callback: types.CallbackQuery, state: FSMContext):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        game = callback.data.replace('custom_bet_', '')
        
        await state.set_state(GameStates.waiting_for_bet)
        await state.update_data(game=game)
        
        await callback.message.edit_text(
            text=f"✏️ Отправь сообщением сумму ставки от {MIN_BET} до {MAX_BET}:\n\n"
            f"Игра: {game.upper()}\n"
            f"💰 Баланс: {await Database.get_balance(user_id)} монет",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="games")]],
                row_width=1
            )
        )
        await callback.answer()
