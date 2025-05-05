import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config_admin import BOT_TOKEN
from db import create_tables
from handlers.admin_handlers import register_admin_handlers

# Configure logging
logging.basicConfig(level=logging.INFO)

# Command list for bot menu
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/admin", description="Admin panel"),
    ]
    await bot.set_my_commands(commands)

async def main():
    # Initialize bot and dispatcher
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register admin handlers
    register_admin_handlers(dp)
        
    # Create database tables if they don't exist
    await create_tables()
    
    # Set bot commands
    await set_commands(bot)
    
    # Start polling
    try:
        logging.info("Admin bot started and polling...")
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
