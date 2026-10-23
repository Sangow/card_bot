from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

nav_cb = CallbackData('nav', 'to')
card_cb = CallbackData('card', 'action', 'card_id')

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
    ]],
    resize_keyboard=True)


def nickname_kb(card_nicknames: list) -> ReplyKeyboardMarkup:
    rkm = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    for c_n in card_nicknames:
        rkm.insert(c_n[0])

    return rkm.add(KeyboardButton(text='CANCEL'))


main_ikb = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton(text='💳 Show cards',
                         callback_data=nav_cb.new(to='cards')),
    InlineKeyboardButton(text='➕ Add card',
                         callback_data=nav_cb.new(to='add'))
)

cancel_ikb = InlineKeyboardMarkup().add(
    InlineKeyboardButton(text='✖️ Cancel',
                         callback_data=nav_cb.new(to='main'))
)


def cards_ikb(cards: list) -> InlineKeyboardMarkup:
    ikm = InlineKeyboardMarkup(row_width=2)

    for card_id, card_nickname in cards:
        ikm.insert(InlineKeyboardButton(
            text=card_nickname,
            callback_data=card_cb.new(action='show', card_id=card_id)
        ))

    return ikm.add(InlineKeyboardButton(text='⬅️ Back',
                                        callback_data=nav_cb.new(to='main')))


def card_ikb(card_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton(
            text='✏️ Edit',
            callback_data=card_cb.new(action='edit', card_id=card_id)),
        InlineKeyboardButton(
            text='❌ Delete',
            callback_data=card_cb.new(action='delete', card_id=card_id))
    ).add(InlineKeyboardButton(text='⬅️ Back',
                               callback_data=nav_cb.new(to='cards')))


def edit_ikb(card_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(InlineKeyboardButton(
        text='↩️ Leave previous',
        callback_data=card_cb.new(action='show', card_id=card_id)
    ))
