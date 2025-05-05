from aiogram import Dispatcher, Bot, F
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from models import AdminForm
from config_admin import ADMIN_USERNAME, ADMIN_PASSWORD
from db import get_total_confirmed_promocodes, get_all_registered_users
from db import add_multiple_promocodes, get_random_winners
from utils.promocode_generator import generate_promocodes
from utils.excel_export import export_users_to_excel, export_promocodes_to_excel, export_winners_to_excel

# Admin menu keyboard
def get_admin_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📈 Tasdiqlangan kodlar soni")],
            [KeyboardButton(text="📊 Ro'yxatdan o'tganlar soni (Excel)")],
            [KeyboardButton(text="🎁 Promo kodlar yaratish")],
            [KeyboardButton(text="🏆 G'olibni aniqlash")],
            [KeyboardButton(text="🔙 Chiqish")]
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

import logging


async def cmd_admin(message: Message, state: FSMContext):
    """Handle /admin command"""
    await state.clear()
    await message.answer("Admin login kiriting:")
    await state.set_state(AdminForm.waiting_for_login)

    

async def process_login(message: Message, state: FSMContext):
    """Process admin login"""
    if message.text == ADMIN_USERNAME:
        await message.answer("Parolni kiriting:")
        await state.set_state(AdminForm.waiting_for_password)
    else:
        await message.answer("Noto'g'ri login. Qayta urinib ko'ring:")

async def process_password(message: Message, state: FSMContext):
    """Process admin password"""
    if message.text == ADMIN_PASSWORD:
        await message.answer(
            "Admin panelga xush kelibsiz!",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.set_state(AdminForm.admin_menu)
    else:
        await message.answer("Noto'g'ri parol. Qayta urinib ko'ring:")

async def admin_menu_handler(message: Message, state: FSMContext, bot: Bot):
    """Handle admin menu options"""
    if message.text == "📈 Tasdiqlangan kodlar soni":
        count = await get_total_confirmed_promocodes()
        await message.answer(f"Tasdiqlangan kodlar soni: {count}")
    
    elif message.text == "📊 Ro'yxatdan o'tganlar soni (Excel)":
        users = await get_all_registered_users()
        
        if users:
            # Generate Excel file
            excel_file = await export_users_to_excel(users)
            
            # Save to temporary file and send
            with open("users.xlsx", "wb") as f:
                f.write(excel_file.getvalue())
            
            # Send file to admin
            doc = FSInputFile("users.xlsx")
            await bot.send_document(
                message.chat.id,
                document=doc,
                caption=f"Ro'yxatdan o'tgan foydalanuvchilar soni: {len(users)}"
            )
        else:
            await message.answer("Hali foydalanuvchilar ro'yxatdan o'tishmagan.")
    
    elif message.text == "🎁 Promo kodlar yaratish":
        await message.answer(
            "Nechta promokod yaratmoqchisiz? (1 dan 10000 gacha son kiriting)",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(AdminForm.waiting_for_promocode_count)
    
    elif message.text == "🏆 G'olibni aniqlash":
        await message.answer(
            "Nechta g'olibni aniqlash kerak? (son kiriting)",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(AdminForm.waiting_for_winner_count)
    
    elif message.text == "🔙 Chiqish":
        await message.answer(
            "Admin paneldan chiqildi.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="/start")]],
                resize_keyboard=True
            )
        )
        await state.clear()

async def process_promocode_count(message: Message, state: FSMContext, bot: Bot):
    """Process promocode generation count"""
    if message.text == "🔙 Orqaga qaytish":
        await message.answer(
            "Admin panel:",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.set_state(AdminForm.admin_menu)
        return
    
    try:
        count = int(message.text)
        if count <= 0 or count > 10000:
            await message.answer(
                "Iltimos 1 dan 10000 gacha bo'lgan son kiriting.",
                reply_markup=get_back_keyboard()
            )
            return
        
        # Generate promocodes
        promocodes = generate_promocodes(count)
        
        # Add promocodes to database
        success = await add_multiple_promocodes(promocodes)
        
        if success:
            # Generate Excel file
            excel_file = await export_promocodes_to_excel(promocodes)
            
            # Save to temporary file and send
            with open("promocodes.xlsx", "wb") as f:
                f.write(excel_file.getvalue())
            
            # Send file to admin
            doc = FSInputFile("promocodes.xlsx")
            await bot.send_document(
                message.chat.id,
                document=doc,
                caption=f"{count} ta promokod muvaffaqiyatli yaratildi."
            )
            
            await message.answer(
                "Admin panel",
                reply_markup=get_admin_menu_keyboard()
            )
            await state.set_state(AdminForm.admin_menu)
        else:
            await message.answer(
                "Promokodlarni yaratishda xatolik yuz berdi. Iltimos qayta urinib ko'ring.",
                reply_markup=get_admin_menu_keyboard()
            )
            await state.set_state(AdminForm.admin_menu)
    
    except ValueError:
        await message.answer(
            "Iltimos faqat son kiriting.",
            reply_markup=get_back_keyboard()
        )

async def process_winner_count(message: Message, state: FSMContext, bot: Bot):
    """Process winner selection count"""
    if message.text == "🔙 Orqaga qaytish":
        await message.answer(
            "Admin panel:",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.set_state(AdminForm.admin_menu)
        return
    
    try:
        count = int(message.text)
        if count <= 0:
            await message.answer(
                "Iltimos 1 dan katta son kiriting.",
                reply_markup=get_back_keyboard()
            )
            return
        
        # Select random winners
        winners = await get_random_winners(count)
        
        if winners and len(winners) > 0:
            # Format winners list for message
            winners_text = "\n".join([
                f"{i+1}. {winner['full_name']} - {winner['phone_number']} "
                f"({winner['promocode_count']} ta promokod)"
                for i, winner in enumerate(winners)
            ])
            
            await message.answer(
                f"G'oliblar ro'yxati:\n\n{winners_text}"
            )
            
            # Generate Excel file
            excel_file = await export_winners_to_excel(winners)
            
            # Save to temporary file and send
            with open("winners.xlsx", "wb") as f:
                f.write(excel_file.getvalue())
            
            # Send file to admin
            doc = FSInputFile("winners.xlsx")
            await bot.send_document(
                message.chat.id,
                document=doc,
                caption=f"{len(winners)} ta g'olib aniqlandi."
            )
        else:
            await message.answer(
                "G'oliblarni aniqlashda xatolik yuz berdi yoki promokodi tasdiqlangan "
                "foydalanuvchilar yo'q."
            )
        
        await message.answer(
            "Admin panel:",
            reply_markup=get_admin_menu_keyboard()
        )
        await state.set_state(AdminForm.admin_menu)
    
    except ValueError:
        await message.answer(
            "Iltimos faqat son kiriting.",
            reply_markup=get_back_keyboard()
        )



def register_admin_handlers(dp: Dispatcher):
    """Register all admin handlers"""
    dp.message.register(cmd_admin, Command("admin"))  # Ensure this is present
    dp.message.register(process_login, AdminForm.waiting_for_login)
    dp.message.register(process_password, AdminForm.waiting_for_password)
    dp.message.register(admin_menu_handler, AdminForm.admin_menu)
    dp.message.register(process_promocode_count, AdminForm.waiting_for_promocode_count)
    dp.message.register(process_winner_count, AdminForm.waiting_for_winner_count)
