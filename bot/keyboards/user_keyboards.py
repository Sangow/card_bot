from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

start_kb = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='SHOW CARDS'),
        KeyboardButton(text='ADD CARD')
    ]],
    resize_keyboard=True)

cancel_kb = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='CANCEL')
    ]],
    resize_keyboard=True)

confirm_kb = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='CONFIRM'),
        KeyboardButton(text='CANCEL')
    ]],
    resize_keyboard=True)

edit_delete_kb = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='✏️'),
        KeyboardButton(text='❌')
    ],
    [
        KeyboardButton(text='CANCEL')
    ]],
    resize_keyboard=True)

leave_previous_kb = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='LEAVE PREVIOUS')
    ],
    [
        KeyboardButton(text='CANCEL')
    ]],
    resize_keyboard=True)


def nickname_kb(card_nicknames: list) -> ReplyKeyboardMarkup:
    rkm = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    for c_n in card_nicknames:
        rkm.insert(c_n[0])

    return rkm.add(KeyboardButton(text='CANCEL'))
