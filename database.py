import aiosqlite
from datetime import datetime, timedelta
from config import START_BALANCE, DAILY_BONUS, CLICK_REWARD, MAX_CLICKS_PER_DAY

DB_PATH = "casino.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                balance REAL DEFAULT 50,
                total_wins INTEGER DEFAULT 0,
                total_losses INTEGER DEFAULT 0,
                last_daily_bonus TEXT,
                games_played INTEGER DEFAULT 0,
                created_at TEXT,
                clicks_today INTEGER DEFAULT 0,
                last_click_time TEXT,
                boost_multiplier REAL DEFAULT 1.0,
                boost_expiry TEXT
            )
        ''')
        
        await db.execute('''
            CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                game_type TEXT,
                bet INTEGER,
                win INTEGER,
                result TEXT,
                created_at TEXT
            )
        ''')
        
        await db.commit()

class Database:
    @staticmethod
    async def get_user(user_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                'SELECT * FROM users WHERE user_id = ?', (user_id,)
            ) as cursor:
                return await cursor.fetchone()
    
    @staticmethod
    async def create_user(user_id: int, username: str = None, first_name: str = None):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                INSERT OR IGNORE INTO users 
                (user_id, username, first_name, balance, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, START_BALANCE, datetime.now().isoformat()))
            await db.commit()
    
    @staticmethod
    async def update_balance(user_id: int, amount: float):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                UPDATE users 
                SET balance = balance + ? 
                WHERE user_id = ?
            ''', (amount, user_id))
            await db.commit()
    
    @staticmethod
    async def get_balance(user_id: int) -> float:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                'SELECT balance FROM users WHERE user_id = ?', (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else START_BALANCE
    
    @staticmethod
    async def can_claim_daily(user_id: int) -> bool:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                'SELECT last_daily_bonus FROM users WHERE user_id = ?', (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row or not row[0]:
                    return True
                last_claim = datetime.fromisoformat(row[0])
                return datetime.now() - last_claim >= timedelta(days=1)
    
    @staticmethod
    async def claim_daily(user_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                UPDATE users 
                SET balance = balance + ?, 
                    last_daily_bonus = ?
                WHERE user_id = ?
            ''', (DAILY_BONUS, datetime.now().isoformat(), user_id))
            await db.commit()
    
    @staticmethod
    async def update_stats(user_id: int, win: bool):
        async with aiosqlite.connect(DB_PATH) as db:
            if win:
                await db.execute('''
                    UPDATE users 
                    SET total_wins = total_wins + 1,
                        games_played = games_played + 1
                    WHERE user_id = ?
                ''', (user_id,))
            else:
                await db.execute('''
                    UPDATE users 
                    SET total_losses = total_losses + 1,
                        games_played = games_played + 1
                    WHERE user_id = ?
                ''', (user_id,))
            await db.commit()
    
    @staticmethod
    async def add_game_history(user_id: int, game_type: str, bet: int, win: float, result: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                INSERT INTO game_history 
                (user_id, game_type, bet, win, result, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, game_type, bet, win, result, datetime.now().isoformat()))
            await db.commit()
    
    @staticmethod
    async def get_leaderboard(limit: int = 10):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute('''
                SELECT user_id, username, first_name, balance, total_wins, games_played
                FROM users 
                ORDER BY balance DESC 
                LIMIT ?
            ''', (limit,)) as cursor:
                return await cursor.fetchall()
    
    @staticmethod
    async def get_clicks_today(user_id: int) -> int:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                'SELECT clicks_today, last_click_time FROM users WHERE user_id = ?', (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return 0
                clicks, last_time = row
                if last_time:
                    last_date = datetime.fromisoformat(last_time).date()
                    today = datetime.now().date()
                    if last_date != today:
                        return 0
                return clicks or 0
    
    @staticmethod
    async def add_click(user_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            today = datetime.now().isoformat()
            await db.execute('''
                UPDATE users 
                SET clicks_today = clicks_today + 1,
                    balance = balance + ?,
                    last_click_time = ?
                WHERE user_id = ?
            ''', (CLICK_REWARD, today, user_id))
            await db.commit()
    
    @staticmethod
    async def get_boost(user_id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                'SELECT boost_multiplier, boost_expiry FROM users WHERE user_id = ?', (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return 1.0, None
                multiplier, expiry = row
                if expiry:
                    expiry_time = datetime.fromisoformat(expiry)
                    if datetime.now() > expiry_time:
                        return 1.0, None
                return multiplier or 1.0, expiry
    
    @staticmethod
    async def set_boost(user_id: int, multiplier: float, hours: int):
        async with aiosqlite.connect(DB_PATH) as db:
            expiry = datetime.now() + timedelta(hours=hours)
            await db.execute('''
                UPDATE users 
                SET boost_multiplier = ?,
                    boost_expiry = ?
                WHERE user_id = ?
            ''', (multiplier, expiry.isoformat(), user_id))
            await db.commit()
