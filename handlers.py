# В игре dice:
if game == 'dice':
    # Отправляем анимированный кубик 🎲 - он сам покажет анимацию!
    await callback.message.answer("🎲 БРОСАЕМ КУБИКИ...")
    await asyncio.sleep(1)  # Даём время на анимацию
    
    # Результаты
    dice_emojis = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅']
    bot_roll = random.randint(1, 6)
    player_roll = random.randint(1, 6)
    
    # Показываем результат с анимированным эмодзи
    await callback.message.answer(
        f"🤖 БРОСОК БОТА: 🎲 {bot_roll}\n"
        f"🎯 ТВОЙ БРОСОК: 🎲 {player_roll}"
    )
    await asyncio.sleep(0.5)
    
    # Результат
    if player_roll > bot_roll:
        win_amount = bet * 1.7 * boost
        await Database.update_balance(user_id, win_amount)
        await Database.update_stats(user_id, True)
        await Database.add_game_history(user_id, game, bet, win_amount, 'win')
        balance = await Database.get_balance(user_id)
        await callback.message.answer(
            f"🏆 ТЫ ПОБЕДИЛ!\n"
            f"💰 +{win_amount:.1f} монет! (x{1.7 * boost:.1f})\n\n"
            f"💳 Баланс: {balance:.1f} монет",
            reply_markup=games_keyboard()
        )
    elif player_roll < bot_roll:
        win_amount = -bet
        await Database.update_balance(user_id, win_amount)
        await Database.update_stats(user_id, False)
        await Database.add_game_history(user_id, game, bet, win_amount, 'loss')
        balance = await Database.get_balance(user_id)
        await callback.message.answer(
            f"😢 БОТ ПОБЕДИЛ!\n"
            f"💸 -{bet} монет!\n\n"
            f"💳 Баланс: {balance:.1f} монет",
            reply_markup=games_keyboard()
        )
    else:
        await Database.add_game_history(user_id, game, bet, 0, 'draw')
        balance = await Database.get_balance(user_id)
        await callback.message.answer(
            f"🤝 НИЧЬЯ!\n\n"
            f"💳 Баланс: {balance:.1f} монет",
            reply_markup=games_keyboard()
        )
    
    await callback.answer()
    return

# В игре slot:
elif game == 'slot':
    # Анимированный слот 🎰 - он сам покажет анимацию!
    await callback.message.answer("🎰 КРУТИМ БАРАБАНЫ...")
    await asyncio.sleep(1.5)  # Даём время на анимацию
    
    symbols = ['🍒', '🍋', '🍊', '🍇', '🔔', '💎', '7️⃣']
    slot1 = random.choice(symbols)
    slot2 = random.choice(symbols)
    slot3 = random.choice(symbols)
    result = [slot1, slot2, slot3]
    
    # Показываем результат
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
