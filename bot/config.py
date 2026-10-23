from os import getenv

API_TOKEN = getenv('API_TOKEN')
# Fernet key that encrypts card numbers in the database
CARD_KEY = getenv('CARD_KEY')
DB_PATH = getenv('DB_PATH', '/data/db.db')
LOG_LEVEL = getenv('LOG_LEVEL', 'INFO')
MAX_CARDS = int(getenv('MAX_CARDS', '20'))
# Seconds after which a shown card number is hidden again
HIDE_AFTER = int(getenv('HIDE_AFTER', '120'))
