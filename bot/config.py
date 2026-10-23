from os import getenv

API_TOKEN = getenv('API_TOKEN')
# Fernet key that encrypts card numbers in the database
CARD_KEY = getenv('CARD_KEY')
DB_PATH = getenv('DB_PATH', '/data/db.db')
LOG_LEVEL = getenv('LOG_LEVEL', 'INFO')
MAX_CARDS = int(getenv('MAX_CARDS', '20'))
# Telegram chat that gets a message when the bot hits an error; no alerts
# when unset
ADMIN_CHAT_ID = int(getenv('ADMIN_CHAT_ID')) if getenv('ADMIN_CHAT_ID') \
    else None
# Tell ADMIN_CHAT_ID when the bot starts, which also reveals unplanned
# restarts; STARTUP_ALERT=0 turns it off and keeps the error alerts
STARTUP_ALERT = getenv('STARTUP_ALERT', '1') != '0'
# Time zone of the times in alerts
ALERT_TIMEZONE = getenv('ALERT_TIMEZONE', 'Europe/Kyiv')
# Seconds after which a shown card number is hidden again
HIDE_AFTER = int(getenv('HIDE_AFTER', '120'))
# Where Telegram fetches the card icons shown in inline mode: the repo's
# assets/card-icons on the branch that is deployed
CARD_ICONS_URL = getenv(
    'CARD_ICONS_URL',
    'https://raw.githubusercontent.com/Sangow/card_bot/master/assets/card-icons'
)
