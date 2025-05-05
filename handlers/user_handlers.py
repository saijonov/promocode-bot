from aiogram import Dispatcher, Bot, F
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.types import Contact, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext


from models import Form
from config_user import CHANNEL_USERNAME, MAX_WRONG_ATTEMPTS
from db import register_user, get_user, verify_promocode, mark_promocode_used, is_user_registered
from db import get_user_promocodes, update_wrong_attempts, is_user_blocked
from utils.channel_utils import check_subscription

# Keyboard for requesting contact
def get_contact_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

# Main menu keyboard
def get_main_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Promokod kiritish")],
            [KeyboardButton(text="📋 Mening promokodlarim")]
        ],
        resize_keyboard=True
    )
    return keyboard

# Back button keyboard
def get_back_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Orqaga qaytish")]],
        resize_keyboard=True
    )
    return keyboard

# Subscription keyboard
def get_subscription_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📲 Kanalga o'tish", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data="check_subscription")]
        ]
    )
    return keyboard

async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    """Handle /start command"""
    # Reset state
    await state.clear()

    # Check if the user is already registered
    user_exists = await is_user_registered(message.from_user.id)
    if user_exists:
        await message.answer(
            f"Assalomu alaykum, {message.from_user.first_name}! 👋\n\n"
            f"Siz allaqachon ro'yxatdan o'tgansiz. Asosiy menyuga xush kelibsiz.",
            reply_markup=get_main_menu_keyboard()
        )
        await state.set_state(Form.main_menu)
    else:
        await message.answer(
            f"Assalomu alaykum, {message.from_user.first_name}! 👋\n\n"
            f"Botimizga xush kelibsiz. Iltimos to'liq ismingizni kiriting (Masalan: Aliyev Ali)."
        )
        await state.set_state(Form.waiting_for_name)

async def check_subscription_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    pass

async def process_name(message: Message, state: FSMContext):
    """Process user's name"""
    # Save name to state
    await state.update_data(full_name=message.text)
    
    await message.answer(
        "Rahmat! Endi telefon raqamingizni yuboring.",
        reply_markup=get_contact_keyboard()
    )
    await state.set_state(Form.waiting_for_phone)

async def process_phone(message: Message, state: FSMContext):
    """Process user's phone number"""
    if message.contact and message.contact.phone_number:
        phone_number = message.contact.phone_number
        
        # Get full name from state
        user_data = await state.get_data()
        full_name = user_data.get('full_name')
        
        # Register user in database
        success = await register_user(message.from_user.id, full_name, phone_number)
        
        if success:
            await message.answer(
                "Ro'yxatdan muvaffaqiyatli o'tdingiz! ✅\n\n"
                "Endi siz promokodlarni kiritishingiz mumkin.",
                reply_markup=get_main_menu_keyboard()
            )
            await state.set_state(Form.main_menu)
        else:
            await message.answer(
                "Ro'yxatdan o'tishda xatolik yuz berdi. Iltimos qayta urinib ko'ring.",
                reply_markup=ReplyKeyboardRemove()
            )
            await state.clear()
    else:
        await message.answer(
            "Iltimos telefon raqamingizni yuborish uchun \"📱 Telefon raqamni yuborish\" tugmasini bosing."
        )

async def main_menu_handler(message: Message, state: FSMContext):
    """Handle main menu options"""
    if message.text == "📥 Promokod kiritish":
        await message.answer(
            "Promokodni kiriting:",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(Form.waiting_for_promocode)
    
    elif message.text == "📋 Mening promokodlarim":
        # Get user promocodes from database
        promocodes = await get_user_promocodes(message.from_user.id)
        
        if promocodes:
            promocode_list = "\n".join([
                f"{i+1}. {code['code']} - {code['submitted_at'].strftime('%Y-%m-%d %H:%M')}"
                for i, code in enumerate(promocodes)
            ])
            await message.answer(
                f"Sizning promokodlaringiz ({len(promocodes)}):\n\n{promocode_list}",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await message.answer(
                "Siz hali birorta ham promokod kiritmadingiz.",
                reply_markup=get_main_menu_keyboard()
            )

async def process_promocode(message: Message, state: FSMContext, bot: Bot):
    """Process and verify promocode"""
    if message.text == "🔙 Orqaga qaytish":
        await message.answer(
            "Asosiy menyu:",
            reply_markup=get_main_menu_keyboard()
        )
        await state.set_state(Form.main_menu)
        return
    
    # Check if user is blocked
    is_blocked = await is_user_blocked(message.from_user.id)
    if is_blocked:
        await message.answer(
            "Siz vaqtincha bloklangansiz. Iltimos keyinroq urinib ko'ring.",
            reply_markup=get_back_keyboard()
        )
        return
    
    # Verify promocode
    promocode = message.text.strip().upper()
    verification_result = await verify_promocode(promocode)
    
    if verification_result == 'valid':
        # Mark promocode as used
        success = await mark_promocode_used(promocode, message.from_user.id)
        
        if success:
            # Reset wrong attempts
            await update_wrong_attempts(message.from_user.id, 0)
            
            # Send success message and sticker
            await message.answer(
                "🎉 Kod muvaffaqiyatli qabul qilindi! 🎉",
                reply_markup=get_back_keyboard()
            )
            
            # Send congratulation sticker
            await bot.send_sticker(
                message.chat.id,
                sticker="CAACAgIAAxkBAAELrQJlXFrYJOCCKQJ7AAGC7MtVJ3W8FQgAAvoZAALMWJhL-_6r7l5qmKk0BA"  # Replace with actual sticker ID
            )
        else:
            await message.answer(
                "Promokod kiritishda xatolik yuz berdi. Iltimos qayta urinib ko'ring.",
                reply_markup=get_back_keyboard()
            )
    
    elif verification_result == 'used':
        await message.answer(
            "❌ Bu kod allaqachon ishlatilgan.",
            reply_markup=get_back_keyboard()
        )
    
    else:  # None - code doesn't exist
        # Get current wrong attempts
        user = await get_user(message.from_user.id)
        wrong_attempts = user['wrong_attempts'] + 1 if user else 1
        
        # Update wrong attempts count
        await update_wrong_attempts(message.from_user.id, wrong_attempts)
        
        # Check if user should be blocked
        if wrong_attempts >= MAX_WRONG_ATTEMPTS:
            await update_wrong_attempts(message.from_user.id, 0, block=True)
            await message.answer(
                "⛔ Siz ketma-ket xato kiritishlar soni uchun bloklangansiz. "
                "Bir soatdan so'ng qayta urinib ko'ring.",
                reply_markup=get_back_keyboard()
            )
        elif wrong_attempts >= 3:
            await message.answer(
                f"❌ Xato kod. Agar siz yana {MAX_WRONG_ATTEMPTS - wrong_attempts} marta xato kiritsangiz, "
                f"siz vaqtincha bloklangani bo'lasiz.",
                reply_markup=get_back_keyboard()
            )
        else:
            await message.answer(
                "❌ Xato kod. Iltimos tekshirib qayta kiriting.",
                reply_markup=get_back_keyboard()
            )

def register_user_handlers(dp: Dispatcher):
    """Register all user handlers"""
    dp.message.register(cmd_start, Command("start"))
    dp.callback_query.register(check_subscription_callback, F.data == "check_subscription")
    dp.message.register(process_name, Form.waiting_for_name)
    dp.message.register(process_phone, Form.waiting_for_phone, F.contact)
    dp.message.register(main_menu_handler, Form.main_menu)
    dp.message.register(process_promocode, Form.waiting_for_promocode)