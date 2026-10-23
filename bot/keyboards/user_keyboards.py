from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from bot.texts import t

nav_cb = CallbackData('nav', 'to')
card_cb = CallbackData('card', 'action', 'card_id')


def main_ikb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton(text=t(lang, 'btn_show_cards'),
                             callback_data=nav_cb.new(to='cards')),
        InlineKeyboardButton(text=t(lang, 'btn_add_card'),
                             callback_data=nav_cb.new(to='add'))
    )


def cancel_ikb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton(text=t(lang, 'btn_cancel'),
                             callback_data=nav_cb.new(to='main'))
    )


def cards_ikb(cards: list, lang: str) -> InlineKeyboardMarkup:
    # One card per row, so masked labels are not cut off on narrow screens
    ikm = InlineKeyboardMarkup(row_width=1)

    for card_id, card_label in cards:
        ikm.insert(InlineKeyboardButton(
            text=card_label,
            callback_data=card_cb.new(action='show', card_id=card_id)
        ))

    return ikm.add(InlineKeyboardButton(text=t(lang, 'btn_back'),
                                        callback_data=nav_cb.new(to='main')))


def card_ikb(card_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton(
            text=t(lang, 'btn_edit_number'),
            callback_data=card_cb.new(action='edit', card_id=card_id)),
        InlineKeyboardButton(
            text=t(lang, 'btn_edit_nickname'),
            callback_data=card_cb.new(action='rename', card_id=card_id))
    ).add(InlineKeyboardButton(
        text=t(lang, 'btn_delete'),
        callback_data=card_cb.new(action='confirm_delete', card_id=card_id)
    )).add(InlineKeyboardButton(text=t(lang, 'btn_back'),
                                callback_data=nav_cb.new(to='cards')))


def edit_ikb(card_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(InlineKeyboardButton(
        text=t(lang, 'btn_leave_previous'),
        callback_data=card_cb.new(action='show', card_id=card_id)
    ))


def rename_ikb(card_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(InlineKeyboardButton(
        text=t(lang, 'btn_leave_previous_nickname'),
        callback_data=card_cb.new(action='show', card_id=card_id)
    ))


def delete_confirm_ikb(card_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton(
            text=t(lang, 'btn_yes_delete'),
            callback_data=card_cb.new(action='delete', card_id=card_id)),
        InlineKeyboardButton(
            text=t(lang, 'btn_no'),
            callback_data=card_cb.new(action='show', card_id=card_id))
    )
