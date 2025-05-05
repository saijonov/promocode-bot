# Telegram Promo Code Bot

This is a Telegram bot for managing promotional campaigns with promo code submission, user registration, and winner selection.

## Features

- User registration with name and phone number collection
- Channel subscription verification
- Promo code submission and validation
- Admin panel with authentication
- Excel reports for user data and promo codes
- Random winner selection
- Rate limiting for incorrect promo code attempts

## Setup and Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a PostgreSQL database
4. Copy `.env.example` to `.env` and fill in your configuration values
5. Run the bot:
   ```
   python main.py
   ```

## Bot Commands

- `/start` - Start the bot and register as a user
- `/admin` - Access the admin panel (requires login)

## Admin Credentials

- Username: sai_jonov
- Password: said10102003..

## Database Structure

The bot uses PostgreSQL with the following tables:

- `promocodes` - Stores generated promo codes and their status
- `users` - Stores registered user information
- `user_promocodes` - Connects users with their submitted promo codes

## Development

To extend this bot, you can modify the following components:

- `handlers/` - Contains user and admin interaction handlers
- `models/` - Contains state definitions
- `utils/` - Utility functions for promo code generation, Excel export, etc.
- `db.py` - Database operations# promocode-bot
