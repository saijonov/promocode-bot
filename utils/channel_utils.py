from aiogram import Bot
from config import CHANNEL_USERNAME

async def check_subscription(bot: Bot, user_id: int):
    """Check if user is subscribed to the channel"""
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        # Return True if user is a member, administrator or creator
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False