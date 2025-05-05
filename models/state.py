from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    """User registration and interaction states"""
    waiting_for_subscription = State()
    waiting_for_name = State()
    waiting_for_phone = State()
    main_menu = State()
    waiting_for_promocode = State()

class AdminForm(StatesGroup):
    """Admin panel states"""
    waiting_for_login = State()
    waiting_for_password = State()
    admin_menu = State()
    waiting_for_promocode_count = State()
    waiting_for_winner_count = State()