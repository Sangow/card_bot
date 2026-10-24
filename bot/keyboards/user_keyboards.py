from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from bot.texts import t

nav_cb = CallbackData('nav', 'to')
card_cb = CallbackData('card', 'action', 'card_id')
cards_cb = CallbackData('cards', 'page')


def main_ikb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton(text=t(lang, 'btn_show_cards'),
                             callback_data=nav_cb.new(to='cards')),
        InlineKeyboardButton(text=t(lang, 'btn_add_card'),
                             callback_data=nav_cb.new(to='add'))
    ).add(InlineKeyboardButton(text=t(lang, 'btn_about'),
                               callback_data=nav_cb.new(to='about')))


def about_ikb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton(text=t(lang, 'btn_back'),
                             callback_data=nav_cb.new(to='main'))
    )


def cancel_ikb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton(text=t(lang, 'btn_cancel'),
                             callback_data=nav_cb.new(to='main'))
    )


def cards_ikb(cards: list, page: int, pages: int,
              lang: str) -> InlineKeyboardMarkup:
    # One card per row, so masked labels are not cut off on narrow screens
    ikm = InlineKeyboardMarkup(row_width=1)

    for card_id, card_label in cards:
        ikm.insert(InlineKeyboardButton(
            text=card_label,
            callback_data=card_cb.new(action='show', card_id=card_id)
        ))

    page_buttons = []
    if page > 0:
        page_buttons.append(InlineKeyboardButton(
            text=t(lang, 'btn_prev_page'),
            callback_data=cards_cb.new(page=page - 1)))
    if page < pages - 1:
        page_buttons.append(InlineKeyboardButton(
            text=t(lang, 'btn_next_page'),
            callback_data=cards_cb.new(page=page + 1)))
    if page_buttons:
        ikm.row(*page_buttons)

    return ikm.add(InlineKeyboardButton(text=t(lang, 'btn_back'),
                                        callback_data=nav_cb.new(to='main')))


def card_ikb(card_id: int, card_nickname: str, lang: str,
             page: int = 0, favorite: bool = False) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(row_width=2).add(
        # Opens a chat picker with "@bot <nickname>" typed in, which lists
        # just this card to send
        InlineKeyboardButton(text=t(lang, 'btn_share'),
                             switch_inline_query=card_nickname)
    ).add(InlineKeyboardButton(
        text=t(lang, 'btn_unfavorite' if favorite else 'btn_favorite'),
        callback_data=card_cb.new(
            action='unfavorite' if favorite else 'favorite',
            card_id=card_id)
    )).add(
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
                                callback_data=cards_cb.new(page=page)))


def hidden_card_ikb(card_id: int, lang: str,
                    page: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton(
            text=t(lang, 'btn_show_number'),
            callback_data=card_cb.new(action='show', card_id=card_id)),
        InlineKeyboardButton(
            text=t(lang, 'btn_back'),
            callback_data=cards_cb.new(page=page))
    )


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


def read_ikb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton(text=t(lang, 'btn_read'),
                             callback_data=nav_cb.new(to='dismiss'))
    )
