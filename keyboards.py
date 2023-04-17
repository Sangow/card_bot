from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

start_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='SHOW CARDS'), KeyboardButton(text='ADD CARD')]],
                               resize_keyboard=True)
