from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

nav_cb = CallbackData('nav', 'to')
card_cb = CallbackData('card', 'action', 'card_id')

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
