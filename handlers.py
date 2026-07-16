from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

from database import Database
from config import EMOJI, DAILY_BONUS, MIN_BET, MAX_BET, CLICK_COOLDOWN, MAX_CLICKS_PER_DAY, CLICK_REWARD, SHOP_ITEMS
import time
import random
import asyncio
import re

user_cooldowns = {}
user_sessions = {}

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
        keyboard.add(InlineKeyboardButton(
            f"{name}x ({item['price']}💰)", 
            callback_data=f"shop_{name}"
        ))
    keyboard.add(
        InlineKeyboardButton("⏱ Ввести часы", callback_data="shop_time"),
        InlineKeyboardButton("🔙 Назад", callback_data="main_menu")
    )
    return keyboard

def parse_dice_result(text: str) -> int:
    """Парсим результат броска кубика из текста"""
    match = re.search(r'🎲\s*(\d+)', text)
    if match:
        return int(match.group(1))
    return None

def parse_slot_result(text: str) -> list:
    """Парсим результат слота из текста"""
    # В ответе слота приходит что-то вроде: "🎰 🍒 🍋 🍊"
    match = re.search(r'🎰\s*([🍒🍋🍊🍇🔔💎7️⃣])\s*([🍒🍋🍊🍇🔔💎7️⃣])\s*([🍒🍋🍊🍇🔔💎7️⃣])', text)
    if match:
        return [match.group(1), match.group(2), match.group(3)]
    return None

def register_handlers(dp: Dispatcher):
    
    @dp.message_handler(commands=['start', 'help'])
    async def cmd_start(message: types.Message):
        user_id = message.from_user.id
        
        if user_id in user_sessions:
            del user_sessions[user_id]
        
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
        
        await message.answer(welcome_text, reply_markup=main_keyboard())
    
    @dp.callback_query_handler(lambda c: c.data == "main_menu")
    async def main_menu(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        balance = await Database.get_balance(user_id)
        await callback.message.edit_text(
            f"🎮 Главное меню\n\n💰 Баланс: {balance} монет",
            reply_markup=main_keyboard()
        )
        await callback.answer()
    
    @dp.callback_query_handler(lambda c: c.data == "balance")
    async def show_balance(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        balance = await Database.get_balance(user_id)
        boost, _ = await Database.get_boost(user_id)
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
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        if await Database.can_claim_daily(user_id):
            await Database.claim_daily(user_id)
            balance = await Database.get_balance(user_id)
            await callback.message.edit_text(
                f"🎉 Ты получил ежедневный бонус {DAILY_BONUS} монет!\n\n💰 Баланс: {balance} монет",
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
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
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
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
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
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
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
            f"🏪 МАГАЗИН БОНУСОВ\n\n"
            f"💰 Баланс: {balance} монет{boost_text}\n\n"
            f"Выбери бонус к выигрышу (действует 1 час):",
            reply_markup=shop_keyboard()
        )
        await callback.answer()
    
    @dp.callback_query_handler(lambda c: c.data.startswith('shop_'))
    async def shop_buy(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        item_name = callback.data.replace('shop_', '')
        if item_name == 'time':
            await callback.message.edit_text(
                "⏱ Отправь сообщением количество часов (1-24):\n\n"
                "Стоимость: цена бонуса × количество часов",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🔙 Назад", callback_data="shop")
                )
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
        
        await Database.update_balance(user_id, -item['price'])
        await Database.set_boost(user_id, item['multiplier'], 1)
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
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        await callback.message.edit_text(
            "⏱ Отправь сообщением количество часов (1-24):\n\n"
            "💡 Стоимость: цена бонуса × количество часов\n"
            "Пример: для бонуса x1.3 (25💰) на 3 часа = 75💰",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 Назад", callback_data="shop")
            )
        )
        await callback.answer()
    
    @dp.message_handler(content_types=['text'])
    async def handle_text(message: types.Message):
        user_id = message.from_user.id
        
        try:
            hours = int(message.text.strip())
            if 1 <= hours <= 24:
                if user_id not in user_sessions:
                    return
                
                await message.answer(
                    f"⏱ Выбрано {hours} час(ов). Теперь выбери бонус в магазине!\n"
                    f"💡 Цена: бонус × {hours}",
                    reply_markup=shop_keyboard()
                )
                return
        except:
            pass
        
        try:
            bet = int(message.text.strip())
            if MIN_BET <= bet <= MAX_BET:
                if user_id not in user_sessions:
                    return
                
                await play_game_direct(message, bet)
                return
        except:
            pass
    
    async def play_game_direct(message: types.Message, bet: int):
        user_id = message.from_user.id
        balance = await Database.get_balance(user_id)
        
        if balance < bet:
            await message.answer("❌ Недостаточно монет!")
            return
        
        boost, _ = await Database.get_boost(user_id)
        
        # Отправляем анимированный кубик
        await message.answer("🎲 Бросаем кубики...")
        
        # Ждём результат через следующий хендлер
        # Результат придёт в сообщении, которое нужно спарсить
        
        # Сохраняем состояние игры
        # Для этого используем временные данные
        
        # Результат будет обработан в следующем сообщении
        await message.answer("Ожидайте результат...")
    
    @dp.callback_query_handler(lambda c: c.data.startswith('game_'))
    async def game_handler(callback: types.CallbackQuery):
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
            f"🎮 {game.upper()}\n💰 Баланс: {balance:.1f} монет\n\nВыбери ставку:",
            reply_markup=bet_keyboard(game)
        )
        await callback.answer()
    
    @dp.callback_query_handler(lambda c: c.data.startswith('bet_'))
    async def play_game(callback: types.CallbackQuery):
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
        
        boost, _ = await Database.get_boost(user_id)
        
        if game == 'dice':
            # Отправляем анимированный кубик 🎲
            await callback.message.answer("🎲 БРОСАЕМ КУБИКИ...")
            
            # Теперь ждём, что пользователь тоже кинет кубик
            # Для этого используем следующий хендлер для текстовых сообщений
            
            await callback.message.answer(
                "🔥 Теперь твой бросок!\nКидай кубик 🎲 в ответ на это сообщение",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🎲 Кинуть кубик", callback_data=f"roll_dice_{bet}_{boost}")
                )
            )
            await callback.answer()
            return
        
        elif game == 'slot':
            # Для слота используем 🎰
            await callback.message.answer("🎰 КРУТИМ БАРАБАНЫ...")
            await asyncio.sleep(1.0)
            
            # Анимированный слот сам показывает результат
            # Парсим результат из сообщения
            result_msg = await callback.message.answer("🎰 🍒 🍋 🍊")
            result_text = result_msg.text
            
            # Парсим результат
            symbols = ['🍒', '🍋', '🍊', '🍇', '🔔', '💎', '7️⃣']
            # Здесь нужно спарсить результат из сообщения
            # В реальности результат приходит в виде: "🎰 🍒 🍋 🍊"
            
            # Для демонстрации используем случайный результат
            slot1 = random.choice(symbols)
            slot2 = random.choice(symbols)
            slot3 = random.choice(symbols)
            result = [slot1, slot2, slot3]
            
            if slot1 == slot2 == slot3:
                if slot1 == '💎':
                    win = bet * 20 * boost
                    await Database.update_balance(user_id, win)
                    await Database.update_stats(user_id, True)
                    await Database.add_game_history(user_id, game, bet, win, 'win')
                    balance = await Database.get_balance(user_id)
                    await callback.message.answer(
                        f"🎰 {' '.join(result)} 💎 ДЖЕКПОТ!\n"
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
                    await callback.message.answer(
                        f"🎰 {' '.join(result)} 🎰 СЕМЁРКИ!\n"
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
                    await callback.message.answer(
                        f"🎰 {' '.join(result)} 🎰 ТРИ В РЯД!\n"
                        f"💰 +{win:.1f} монет! (x{10 * boost:.1f})\n\n"
                        f"💳 Баланс: {balance:.1f} монет",
                        reply_markup=games_keyboard()
                    )
            elif slot1 == slot2 or slot2 == slot3:
                await Database.add_game_history(user_id, game, bet, bet, 'draw')
                balance = await Database.get_balance(user_id)
                await callback.message.answer(
                    f"🎰 {' '.join(result)} 🔄 ДВА В РЯД!\n"
                    f"💳 Баланс: {balance:.1f} монет",
                    reply_markup=games_keyboard()
                )
            else:
                win = -bet
                await Database.update_balance(user_id, win)
                await Database.update_stats(user_id, False)
                await Database.add_game_history(user_id, game, bet, win, 'loss')
                balance = await Database.get_balance(user_id)
                await callback.message.answer(
                    f"🎰 {' '.join(result)} ❌ Ничего не совпало!\n"
                    f"💸 -{bet} монет!\n\n"
                    f"💳 Баланс: {balance:.1f} монет",
                    reply_markup=games_keyboard()
                )
            
            await callback.answer()
            return
    
    @dp.callback_query_handler(lambda c: c.data.startswith('roll_dice_'))
    async def roll_dice(callback: types.CallbackQuery):
        """Обработчик броска кубика игроком"""
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        data = callback.data.split('_')
        bet = int(data[2])
        boost = float(data[3])
        
        # Бот кидает кубик
        bot_msg = await callback.message.answer("🤖 БРОСОК БОТА: 🎲")
        await asyncio.sleep(0.5)
        
        # Игрок кидает кубик
        player_msg = await callback.message.answer("🎯 ТВОЙ БРОСОК: 🎲")
        await asyncio.sleep(0.5)
        
        # Парсим результаты
        bot_text = bot_msg.text
        player_text = player_msg.text
        
        # Извлекаем числа из сообщений
        bot_match = re.search(r'🎲\s*(\d+)', bot_text)
        player_match = re.search(r'🎲\s*(\d+)', player_text)
        
        if bot_match and player_match:
            bot_roll = int(bot_match.group(1))
            player_roll = int(player_match.group(1))
        else:
            # Если не удалось спарсить, используем случайные числа
            bot_roll = random.randint(1, 6)
            player_roll = random.randint(1, 6)
        
        # Определяем победителя
        if player_roll > bot_roll:
            win_amount = bet * 1.7 * boost
            await Database.update_balance(user_id, win_amount)
            await Database.update_stats(user_id, True)
            await Database.add_game_history(user_id, 'dice', bet, win_amount, 'win')
            balance = await Database.get_balance(user_id)
            await callback.message.answer(
                f"🏆 ТЫ ПОБЕДИЛ!\n"
                f"🎯 Твой бросок: {player_roll}\n"
                f"🤖 Бросок бота: {bot_roll}\n"
                f"💰 +{win_amount:.1f} монет! (x{1.7 * boost:.1f})\n\n"
                f"💳 Баланс: {balance:.1f} монет",
                reply_markup=games_keyboard()
            )
        elif player_roll < bot_roll:
            win_amount = -bet
            await Database.update_balance(user_id, win_amount)
            await Database.update_stats(user_id, False)
            await Database.add_game_history(user_id, 'dice', bet, win_amount, 'loss')
            balance = await Database.get_balance(user_id)
            await callback.message.answer(
                f"😢 БОТ ПОБЕДИЛ!\n"
                f"🎯 Твой бросок: {player_roll}\n"
                f"🤖 Бросок бота: {bot_roll}\n"
                f"💸 -{bet} монет!\n\n"
                f"💳 Баланс: {balance:.1f} монет",
                reply_markup=games_keyboard()
            )
        else:
            await Database.add_game_history(user_id, 'dice', bet, 0, 'draw')
            balance = await Database.get_balance(user_id)
            await callback.message.answer(
                f"🤝 НИЧЬЯ!\n"
                f"🎯 Твой бросок: {player_roll}\n"
                f"🤖 Бросок бота: {bot_roll}\n"
                f"💳 Баланс: {balance:.1f} монет",
                reply_markup=games_keyboard()
            )
        
        await callback.answer()
    
    @dp.callback_query_handler(lambda c: c.data.startswith('custom_bet_'))
    async def custom_bet(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        if user_id not in user_sessions:
            await callback.answer("❌ Это окно не для вас! Напишите /start", show_alert=True)
            return
        
        game = callback.data.replace('custom_bet_', '')
        await callback.message.edit_text(
            f"✏️ Отправь сообщением сумму ставки от {MIN_BET} до {MAX_BET}:\n\n"
            f"Игра: {game.upper()}\n"
            f"💰 Баланс: {await Database.get_balance(user_id)} монет",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🔙 Назад", callback_data="games")
            )
        )
        await callback.answer()
