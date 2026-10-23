from os import getenv

API_TOKEN = getenv('API_TOKEN')
DB_PATH = getenv('DB_PATH', '/data/db.db')
LOG_LEVEL = getenv('LOG_LEVEL', 'INFO')
MAX_CARDS = int(getenv('MAX_CARDS', '20'))
