from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

start_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='SHOW CARDS'), KeyboardButton(text='ADD CARD')]],
                               resize_keyboard=True)

cancel_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='CANCEL')]],
                                resize_keyboard=True)

confirm_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='CONFIRM'),KeyboardButton(text='CANCEL')]],
                                 resize_keyboard=True)
