# User bot configuration settings

# Bot token for the user bot
BOT_TOKEN = "7665418627:AAGJK238VV78LpcT-nxTZMW8tc2F5mCb0M4"  # Replace with your actual user bot token

# Channel username that users must subscribe to
CHANNEL_USERNAME = "@richbekov"  # Replace with your channel username

# Database configuration
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "promocode_bot"
DB_USER = "said"
DB_PASS = "1010"  # Replace with your database password

# Rate limiting settings
MAX_WRONG_ATTEMPTS = 5
BLOCK_TIME_SECONDS = 3600  # 1 hour

# Postgres connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
