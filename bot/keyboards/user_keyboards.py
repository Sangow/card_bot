from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

start_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='SHOW CARDS'), KeyboardButton(text='ADD CARD')]],
                               resize_keyboard=True)

cancel_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='CANCEL')]],
                                resize_keyboard=True, )

cancel_inline_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='CANCEL',
                                                                               callback_data='cancel_callback')]])

confirm_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='CONFIRM'), KeyboardButton(text='CANCEL')]],
                                 resize_keyboard=True)

delete_edit_inline_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='✏️',
                                                                                    callback_data='edit_callback'),
                                                               InlineKeyboardButton(text='❌',
                                                                                    callback_data='delete_callback')]])


def nickname_kb(card_nicknames: list) -> ReplyKeyboardMarkup:
    rkm = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    for c_n in card_nicknames:
        rkm.insert(c_n[0])

    return rkm.add(KeyboardButton(text='CANCEL'))
