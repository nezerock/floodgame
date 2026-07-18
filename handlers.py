from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import Database
from config import EMOJI, DAILY_BONUS, MIN_BET, MAX_BET, CLICK_COOLDOWN, MAX_CLICKS_PER_DAY, CLICK_REWARD, SHOP_ITEMS

# Храним сообщения для удаления
user_messages = {}
user_cooldowns = {}
user_sessions = {}

def save_msg(user_id, msg):
    if user_id not in user_messages:
        user_messages[user_id] = []
    user_messages[user_id].append(msg)

def clear_msgs(user_id):
    if user_id in user_messages:
        for msg in user_messages[user_id]:
            try:
                msg.delete()
            except:
                pass
        user_messages[user_id] = []

# ---------- КЛАВИАТУРЫ ----------
def main_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(f"{EMOJI['coin']} Баланс", callback_data="balance"),
        InlineKeyboardButton(f"{EMOJI['diamond']} Бонус", callback_data="daily"),
        InlineKeyboardButton(f"{EMOJI['games']} Игры", callback_data="games"),
        InlineKeyboardButton(f"{EMOJI['leaderboard']} Лидеры", callback_data="leaderboard"),
        InlineKeyboardButton(f"{EMOJI['click']} Кликер", callback_data="clicker"),
        InlineKeyboardButton(f"{EMOJI['shop']} Магазин", callback_data="shop")
    )
    return keyboard

def games_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🎲 Кости (1.7x)", callback_data="game_dice"),
        InlineKeyboardButton("🎰 Слоты (20x)", callback_data="game_slot"),
        InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
    )
    return keyboard

def bet_keyboard(game: str):
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
        InlineKeyboardButton("✏️ Ввести ставку", callback_data=f"custom_bet_{game}"),
        InlineKeyboardButton("🔙 Назад", callback_data="games")
    )
    return keyboard

def shop_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    for name, item in SHOP_ITEMS.items():
        keyboard.add(InlineKeyboardButton(f"{name}x ({item['price']}💰)", callback_data=f"shop_{name}"))
    keyboard.add(
        InlineKeyboardButton("⏱ Ввести часы", callback_data="shop_time"),
        InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
    )
    return keyboard

async def get_boost(user_id):
    async with aiosqlite.connect("casino.db") as db:
        async with db.execute('SELECT boost_multiplier, boost_expiry FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0] and row[1]:
                expiry = datetime.fromisoformat(row[1])
                if datetime.now() < expiry:
                    return row[0]
    return 1.0

# ---------- ОБРАБОТЧИКИ ----------
def register_handlers(dp: Dispatcher):

    @dp.message_handler(commands=['start', 'help'])
    async def cmd_start(message: types.Message):
        user_id = message.from_user.id
        user_sessions[user_id] = True
        await Database.create_user(user_id, message.from_user.username, message.from_user.first_name)
        balance = await Database.get_balance(user_id)
        boost = await get_boost(user_id)
        boost_text = f"\n🔥 Активный бонус: x{boost}" if boost > 1.0 else ""
        clear_msgs(user_id)
        msg = await message.answer(
            f"🎮 Добро пожаловать в FLOOD GAMES, {message.from_user.first_name}!\n\n💰 Баланс: {balance} монет{boost_text}\n\n🎯 Доступные игры:\n• 🎲 Кости (x1.7)\n• 🎰 Слоты (x20)\n\n👆 Кликер - зарабатывай монеты!\n💎 Ежедневный бонус: {DAILY_BONUS} монет",
            reply_markup=main_keyboard()
        )
        save_msg(user_id, msg)
        save_msg(user_id, message)

    @dp.callback_query_handler(lambda c: c.data == "main_menu")
    async def main_menu(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        clear_msgs(user_id)
        balance = await Database.get_balance(user_id)
        msg = await callback.message.edit_text(
            f"🎮 Главное меню\n\n💰 Баланс: {balance} монет",
            reply_markup=main_keyboard()
        )
        save_msg(user_id, msg)
        await callback.answer()

    @dp.callback_query_handler(lambda c: c.data == "balance")
    async def show_balance(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        balance = await Database.get_balance(user_id)
        boost = await get_boost(user_id)
        boost_text = f"\n🔥 Активный бонус: x{boost}" if boost > 1.0 else ""
        await callback.message.edit_text(
            f"💰 Баланс: {balance} монет{boost_text}",
            reply_markup=main_keyboard()
        )
        await callback.answer()

    @dp.callback_query_handler(lambda c: c.data == "daily")
    async def daily_bonus(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        if await Database.can_claim_daily(user_id):
            await Database.claim_daily(user_id)
            balance = await Database.get_balance(user_id)
            await callback.message.edit_text(
                f"🎉 Бонус {DAILY_BONUS} монет получен!\n\n💰 Баланс: {balance} монет",
                reply_markup=main_keyboard()
            )
        else:
            await callback.message.edit_text(
                "⏳ Бонус уже получен сегодня!\nПриходи завтра.",
                reply_markup=main_keyboard()
            )
        await callback.answer()

    @dp.callback_query_handler(lambda c: c.data == "games")
    async def games_menu(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        await callback.message.edit_text(
            "🎮 Выбери игру:",
            reply_markup=games_keyboard()
        )
        await callback.answer()

    @dp.callback_query_handler(lambda c: c.data == "leaderboard")
    async def leaderboard(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        leaders = await Database.get_leaderboard(10)
        if not leaders:
            await callback.message.edit_text(
                "📊 Таблица лидеров пуста!",
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
        await callback.message.edit_text(text, reply_markup=main_keyboard())
        await callback.answer()

    @dp.callback_query_handler(lambda c: c.data == "clicker")
    async def clicker(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
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
            await callback.answer("❌ Лимит кликов на сегодня исчерпан!", show_alert=True)
            return
        await Database.add_click(user_id)
        user_cooldowns[user_id] = current_time
        balance = await Database.get_balance(user_id)
        clicks_today_new = await Database.get_clicks_today(user_id)
        remaining = MAX_CLICKS_PER_DAY - clicks_today_new
        await callback.answer(f"👆 +{CLICK_REWARD} монет! Баланс: {balance:.1f}", show_alert=False)
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

    @dp.callback_query_handler(lambda c: c.data == "shop")
    async def shop_menu(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        balance = await Database.get_balance(user_id)
        boost = await get_boost(user_id)
        boost_text = f"\n🔥 Активный бонус: x{boost}" if boost > 1.0 else "\n❌ Бонус не активен"
        await callback.message.edit_text(
            f"🏪 МАГАЗИН БОНУСОВ\n\n"
            f"💰 Баланс: {balance} монет{boost_text}\n\n"
            f"Выбери бонус к выигрышу (действует 1 час):",
            reply_markup=shop_keyboard()
        )
        await callback.answer()

    @dp.callback_query_handler(lambda c: c.data.startswith("shop_"))
    async def shop_buy(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        item_name = callback.data.replace('shop_', '')
        if item_name == 'time':
            await callback.message.edit_text(
                "⏱ Отправь сообщением количество часов (1-24):\n\n"
                "💡 Стоимость: цена бонуса × количество часов",
                reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="shop"))
            )
            await callback.answer()
            return
        if item_name not in SHOP_ITEMS:
            await callback.answer("❌ Неверный выбор!")
            return
        item = SHOP_ITEMS[item_name]
        balance = await Database.get_balance(user_id)
        if balance < item['price']:
            await callback.answer(f"❌ Недостаточно монет! Нужно: {item['price']}", show_alert=True)
            return
        # Покупаем на 1 час
        await Database.update_balance(user_id, -item['price'])
        expiry = datetime.now() + timedelta(hours=1)
        async with aiosqlite.connect("casino.db") as db:
            await db.execute('UPDATE users SET boost_multiplier = ?, boost_expiry = ? WHERE user_id = ?', 
                            (item['multiplier'], expiry.isoformat(), user_id))
            await db.commit()
        balance = await Database.get_balance(user_id)
        await callback.message.edit_text(
            f"✅ Куплен бонус x{item['multiplier']} на 1 час!\n\n"
            f"💰 Баланс: {balance} монет\n"
            f"🔥 Теперь выигрыши увеличены в {item['multiplier']}x!",
            reply_markup=shop_keyboard()
        )
        await callback.answer()

    @dp.callback_query_handler(lambda c: c.data == "shop_time")
    async def shop_time_input(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        await callback.message.edit_text(
            "⏱ Отправь сообщением количество часов (1-24):\n\n"
            "💡 Стоимость: цена бонуса × количество часов\n"
            "Пример: для бонуса x1.3 (25💰) на 3 часа = 75💰",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="shop"))
        )
        await callback.answer()

    @dp.message_handler(content_types=['text'])
    async def handle_text(message: types.Message):
        user_id = message.from_user.id
        if user_id not in user_sessions:
            await message.answer("❌ Напиши /start чтобы начать!")
            return
        # Проверка на ввод ставки
        try:
            bet = int(message.text.strip())
            if MIN_BET <= bet <= MAX_BET:
                await message.delete()
                await process_game(message, "dice", bet, message.bot)
                return
        except:
            pass
        # Проверка на ввод часов
        try:
            hours = int(message.text.strip())
            if 1 <= hours <= 24:
                await message.answer(
                    f"⏱ Выбрано {hours} час(ов). Теперь выбери бонус в магазине!\n"
                    f"💡 Цена: бонус × {hours}",
                    reply_markup=shop_keyboard()
                )
                return
        except:
            pass

    async def process_game(message: types.Message, game: str, bet: int, bot):
        user_id = message.from_user.id
        balance = await Database.get_balance(user_id)
        if balance < bet:
            await message.answer("❌ Недостаточно монет!")
            return
        boost = await get_boost(user_id)
        
        if game == 'dice':
            start_msg = await message.answer("🎲 НАЧИНАЕМ ИГРУ!")
            await asyncio.sleep(0.5)
            bot_dice = await bot.send_dice(chat_id=message.chat.id, emoji="🎲")
            await asyncio.sleep(2.5)
            bot_roll = bot_dice.dice.value
            player_dice = await bot.send_dice(chat_id=message.chat.id, emoji="🎲")
            await asyncio.sleep(2.5)
            player_roll = player_dice.dice.value
            result_text = f"🤖 Бот: {bot_roll}\n🎯 Ты: {player_roll}\n\n"
            
            if player_roll > bot_roll:
                win = bet * 1.7 * boost
                await Database.update_balance(user_id, win)
                await Database.add_history(user_id, "dice", bet, win, "win")
                balance = await Database.get_balance(user_id)
                await message.answer(
                    f"🏆 ТЫ ПОБЕДИЛ!\n{result_text}💰 +{win:.1f} монет! (x{1.7 * boost:.1f})\n\n💳 Баланс: {balance:.1f} монет",
                    reply_markup=games_keyboard()
                )
            elif player_roll < bot_roll:
                win = -bet
                await Database.update_balance(user_id, win)
                await Database.add_history(user_id, "dice", bet, win, "loss")
                balance = await Database.get_balance(user_id)
                await message.answer(
                    f"😢 БОТ ПОБЕДИЛ!\n{result_text}💸 -{bet} монет!\n\n💳 Баланс: {balance:.1f} монет",
                    reply_markup=games_keyboard()
                )
            else:
                await Database.add_history(user_id, "dice", bet, 0, "draw")
                balance = await Database.get_balance(user_id)
                await message.answer(
                    f"🤝 НИЧЬЯ!\n{result_text}💳 Баланс: {balance:.1f} монет",
                    reply_markup=games_keyboard()
                )
            try:
                await start_msg.delete()
            except:
                pass
        
        elif game == 'slot':
            start_msg = await message.answer("🎰 КРУТИМ БАРАБАНЫ...")
            await asyncio.sleep(0.5)
            slot_msg = await bot.send_dice(chat_id=message.chat.id, emoji="🎰")
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
            await message.answer(
                f"🎰 {slot1} {slot2} {slot3}\n\n{text}\n\n💳 Баланс: {balance:.1f} монет",
                reply_markup=games_keyboard()
            )
            try:
                await start_msg.delete()
            except:
                pass

    @dp.callback_query_handler(lambda c: c.data.startswith("game_"))
    async def game_handler(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        game = callback.data.replace('game_', '')
        balance = await Database.get_balance(user_id)
        if balance < MIN_BET:
            await callback.answer(f"❌ Минимальная ставка: {MIN_BET}", show_alert=True)
            return
        await callback.message.edit_text(
            f"🎮 {game.upper()}\n💰 Баланс: {balance:.1f} монет\n\nВыбери ставку:",
            reply_markup=bet_keyboard(game)
        )
        await callback.answer()

    @dp.callback_query_handler(lambda c: c.data.startswith("bet_"))
    async def play_game(callback: types.CallbackQuery):
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
        await callback.message.delete()
        await process_game(callback.message, game, bet, callback.bot)
        await callback.answer()

    @dp.callback_query_handler(lambda c: c.data.startswith("custom_bet_"))
    async def custom_bet(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Напишите /start", show_alert=True)
            return
        game = callback.data.replace('custom_bet_', '')
        await callback.message.edit_text(
            f"✏️ Отправь сообщением сумму ставки от {MIN_BET} до {MAX_BET}:\n\n"
            f"Игра: {game.upper()}\n"
            f"💰 Баланс: {await Database.get_balance(user_id)} монет",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Назад", callback_data="games"))
        )
        await callback.answer()
