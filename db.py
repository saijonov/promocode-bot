import asyncio
import asyncpg
from config import DATABASE_URL
from datetime import datetime

# Create connection pool
pool = None

async def get_pool():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_URL)
    return pool

async def create_tables():
    """Create necessary database tables if they don't exist"""
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        # Create promocodes table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS promocodes (
                id SERIAL PRIMARY KEY,
                code VARCHAR(20) UNIQUE NOT NULL,
                status VARCHAR(10) DEFAULT 'unused' CHECK (status IN ('used', 'unused')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create users table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                phone_number VARCHAR(20) NOT NULL,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                wrong_attempts INT DEFAULT 0,
                blocked_until TIMESTAMP
            )
        ''')
        
        # Create user_promocodes table for many-to-many relationship
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_promocodes (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(telegram_id) ON DELETE CASCADE,
                promocode_id INTEGER REFERENCES promocodes(id) ON DELETE CASCADE,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, promocode_id)
            )
        ''')

# User database operations
async def register_user(telegram_id, full_name, phone_number):
    """Register a new user or update existing user"""
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        try:
            await conn.execute('''
                INSERT INTO users (telegram_id, full_name, phone_number)
                VALUES ($1, $2, $3)
                ON CONFLICT (telegram_id) 
                DO UPDATE SET full_name = $2, phone_number = $3
            ''', telegram_id, full_name, phone_number)
            return True
        except Exception as e:
            print(f"Error registering user: {e}")
            return False

async def get_user(telegram_id):
    """Get user by telegram ID"""
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        return await conn.fetchrow('''
            SELECT * FROM users WHERE telegram_id = $1
        ''', telegram_id)

async def update_wrong_attempts(telegram_id, attempts=None, block=False):
    """Update wrong attempts counter and optional block time"""
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        if attempts is not None:
            await conn.execute('''
                UPDATE users SET wrong_attempts = $1 
                WHERE telegram_id = $2
            ''', attempts, telegram_id)
            
        if block:
            blocked_until = datetime.now().timestamp() + 3600  # Block for 1 hour
            await conn.execute('''
                UPDATE users SET blocked_until = to_timestamp($1)
                WHERE telegram_id = $2
            ''', blocked_until, telegram_id)

async def is_user_blocked(telegram_id):
    """Check if user is currently blocked"""
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        result = await conn.fetchval('''
            SELECT blocked_until > CURRENT_TIMESTAMP as is_blocked
            FROM users WHERE telegram_id = $1
        ''', telegram_id)
        return result or False

# Promocode database operations
async def add_promocode(code):
    """Add a new promocode to the database"""
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        try:
            await conn.execute('''
                INSERT INTO promocodes (code, status) VALUES ($1, 'unused')
            ''', code)
            return True
        except asyncpg.exceptions.UniqueViolationError:
            # Code already exists
            return False
        except Exception as e:
            print(f"Error adding promocode: {e}")
            return False

async def add_multiple_promocodes(codes):
    """Add multiple promocodes to the database"""
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        try:
            # Using a transaction to ensure all or nothing
            async with conn.transaction():
                for code in codes:
                    await conn.execute('''
                        INSERT INTO promocodes (code, status) 
                        VALUES ($1, 'unused')
                        ON CONFLICT (code) DO NOTHING
                    ''', code)
            return True
        except Exception as e:
            print(f"Error adding multiple promocodes: {e}")
            return False

async def verify_promocode(code):
    """Verify if promocode exists and is unused"""
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        promocode = await conn.fetchrow('''
            SELECT * FROM promocodes WHERE code = $1
        ''', code)
        
        if not promocode:
            return None  # Code doesn't exist
        elif promocode['status'] == 'used':
            return 'used'  # Code already used
        else:
            return 'valid'  # Code is valid

async def mark_promocode_used(code, telegram_id):
    """Mark promocode as used and associate it with user"""
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        try:
            async with conn.transaction():
                # Get promocode ID
                promocode_id = await conn.fetchval('''
                    SELECT id FROM promocodes WHERE code = $1
                ''', code)
                
                if not promocode_id:
                    return False
                
                # Mark promocode as used
                await conn.execute('''
                    UPDATE promocodes SET status = 'used' WHERE id = $1
                ''', promocode_id)
                
                # Link promocode to user
                await conn.execute('''
                    INSERT INTO user_promocodes (user_id, promocode_id)
                    VALUES ($1, $2)
                ''', telegram_id, promocode_id)
                
                return True
        except Exception as e:
            print(f"Error marking promocode as used: {e}")
            return False

async def get_user_promocodes(telegram_id):
    """Get all promocodes used by a user"""
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        return await conn.fetch('''
            SELECT p.code, up.submitted_at
            FROM user_promocodes up
            JOIN promocodes p ON up.promocode_id = p.id
            WHERE up.user_id = $1
            ORDER BY up.submitted_at DESC
        ''', telegram_id)

# Admin database operations
async def get_total_confirmed_promocodes():
    """Get total count of used promocodes"""
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        return await conn.fetchval('''
            SELECT COUNT(*) FROM promocodes WHERE status = 'used'
        ''')

async def get_all_registered_users():
    """Get all registered users with their promocode count"""
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        return await conn.fetch('''
            SELECT u.telegram_id, u.full_name, u.phone_number, u.registered_at,
                  COUNT(up.id) as promocode_count
            FROM users u
            LEFT JOIN user_promocodes up ON u.telegram_id = up.user_id
            GROUP BY u.telegram_id, u.full_name, u.phone_number, u.registered_at
            ORDER BY u.registered_at DESC
        ''')

async def get_random_winners(count=1):
    """Select random winners from users who have submitted valid promocodes"""
    pool = await get_pool()
    
    async with pool.acquire() as conn:
        return await conn.fetch('''
            SELECT DISTINCT ON (u.telegram_id) 
                u.telegram_id, u.full_name, u.phone_number, 
                COUNT(up.id) OVER (PARTITION BY u.telegram_id) as promocode_count
            FROM users u
            JOIN user_promocodes up ON u.telegram_id = up.user_id
            ORDER BY u.telegram_id, RANDOM()
            LIMIT $1
        ''', count)
    
async def is_user_registered(telegram_id):
    """Check if a user is already registered"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchval('''
            SELECT EXISTS (
                SELECT 1 FROM users WHERE telegram_id = $1
            )
        ''', telegram_id)
    return result