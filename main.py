import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, Message

from config import BOT_TOKEN
from db import create_tables
from handlers.user_handlers import register_user_handlers
from handlers.admin_handlers import register_admin_handlers

# Configure logging
logging.basicConfig(level=logging.INFO)

# Command list for bot menu
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Botni ishga tushirish"),
        BotCommand(command="/admin", description="Admin panel"), 
    ]
    await bot.set_my_commands(commands)

async def main():
    # Initialize bot and dispatcher
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register all handlers
    register_user_handlers(dp)
    register_admin_handlers(dp)
        
    # Create database tables if they don't exist
    await create_tables()
    
    # Set bot commands
    await set_commands(bot)
    
    # Start polling
    try:
        logging.info("Bot started and polling...")
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())