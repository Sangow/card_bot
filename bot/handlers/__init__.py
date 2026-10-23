from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Command, CommandStart, Text
from aiogram.types import ContentTypes

from bot.keyboards import nav_cb, card_cb, cards_cb
from bot.states import AddCard, ShowCard
from .admin import is_admin, cmd_stats
from .error_handlers import errors_handler
from .inline import inline_cards_handler
from .fallback import non_text_in_dialog_handler, \
    card_number_outside_dialog_handler, not_understood_handler, \
    invalid_card_button, invalid_button_handler, \
    NICKNAME_STATES, NUMBER_STATES
from .private_only import not_private, group_message_handler, \
    group_callback_handler
from .service import validate_card_number, validate_card_nickname, \
    is_mir_card, looks_like_card_number
from .user_handlers import cmd_start, cmd_cancel, cmd_cards, cmd_add, \
    cmd_help, main_menu_handler, about_handler, dismiss_handler, \
    add_card_1, add_card_2, add_card_2_fail, add_card_3, add_card_3_fail, \
    add_card_3_not_supported, edit_card_number_not_supported_handler, \
    show_cards_handler, show_card_handler, edit_card_handler, \
    edit_card_number_fail_handler, edit_card_number_handler, \
    rename_card_handler, rename_card_fail_handler, rename_card_save_handler, \
    confirm_delete_card_handler, delete_card_handler


async def register_handlers(dp: Dispatcher) -> None:
    # Registered first, so nothing else runs outside private chats
    dp.register_message_handler(group_message_handler,
                                not_private,
                                content_types=ContentTypes.ANY,
                                state='*')
    dp.register_callback_query_handler(group_callback_handler,
                                       not_private,
                                       state='*')
    dp.register_callback_query_handler(invalid_button_handler,
                                       invalid_card_button,
                                       state='*')

    dp.register_message_handler(cmd_start,
                                CommandStart(),
                                state='*')
    dp.register_message_handler(cmd_cancel,
                                Text(equals='cancel', ignore_case=True),
                                state='*')
    # Commands go before state handlers so they work in the middle of input
    dp.register_message_handler(cmd_cancel,
                                Command('cancel'),
                                state='*')
    dp.register_message_handler(cmd_cards,
                                Command('cards'),
                                state='*')
    dp.register_message_handler(cmd_add,
                                Command('add'),
                                state='*')
    dp.register_message_handler(cmd_help,
                                Command('help'),
                                state='*')
    # Only for the bot owner; anyone else gets the usual "not understood"
    dp.register_message_handler(cmd_stats,
                                Command('stats'),
                                is_admin,
                                state='*')
    # Buttons of the old reply keyboard
    dp.register_message_handler(cmd_start,
                                Text(equals=['show cards', 'add card'],
                                     ignore_case=True),
                                state='*')

    dp.register_callback_query_handler(main_menu_handler,
                                       nav_cb.filter(to='main'),
                                       state='*')
    dp.register_callback_query_handler(about_handler,
                                       nav_cb.filter(to='about'),
                                       state='*')
    dp.register_callback_query_handler(dismiss_handler,
                                       nav_cb.filter(to='dismiss'),
                                       state='*')

    dp.register_callback_query_handler(add_card_1,
                                       nav_cb.filter(to='add'),
                                       state='*')
    dp.register_message_handler(add_card_2_fail,
                                lambda message:
                                not validate_card_nickname(message.text),
                                state=AddCard.card_nickname)
    dp.register_message_handler(add_card_2,
                                state=AddCard.card_nickname)
    dp.register_message_handler(add_card_3_fail,
                                lambda message:
                                not validate_card_number(message.text),
                                state=AddCard.card_number)
    dp.register_message_handler(add_card_3_not_supported,
                                lambda message: is_mir_card(message.text),
                                state=AddCard.card_number)
    dp.register_message_handler(add_card_3,
                                state=AddCard.card_number)

    dp.register_callback_query_handler(show_cards_handler,
                                       nav_cb.filter(to='cards'),
                                       state='*')
    dp.register_callback_query_handler(show_cards_handler,
                                       cards_cb.filter(),
                                       state='*')
    dp.register_callback_query_handler(show_card_handler,
                                       card_cb.filter(action='show'),
                                       state='*')

    dp.register_callback_query_handler(edit_card_handler,
                                       card_cb.filter(action='edit'),
                                       state='*')
    dp.register_message_handler(edit_card_number_fail_handler,
                                lambda message:
                                not validate_card_number(message.text),
                                state=ShowCard.edit_card_number)
    dp.register_message_handler(edit_card_number_not_supported_handler,
                                lambda message: is_mir_card(message.text),
                                state=ShowCard.edit_card_number)
    dp.register_message_handler(edit_card_number_handler,
                                state=ShowCard.edit_card_number)

    dp.register_callback_query_handler(rename_card_handler,
                                       card_cb.filter(action='rename'),
                                       state='*')
    dp.register_message_handler(rename_card_fail_handler,
                                lambda message:
                                not validate_card_nickname(message.text),
                                state=ShowCard.edit_card_nickname)
    dp.register_message_handler(rename_card_save_handler,
                                state=ShowCard.edit_card_nickname)

    dp.register_callback_query_handler(confirm_delete_card_handler,
                                       card_cb.filter(action='confirm_delete'),
                                       state='*')
    dp.register_callback_query_handler(delete_card_handler,
                                       card_cb.filter(action='delete'),
                                       state='*')

    # Sharing a card from any chat; works in the middle of a dialog too
    dp.register_inline_handler(inline_cards_handler, state='*')

    # Fallbacks: registered last, so they only get what nothing above took
    dp.register_message_handler(non_text_in_dialog_handler,
                                content_types=ContentTypes.ANY,
                                state=NICKNAME_STATES + NUMBER_STATES)
    dp.register_message_handler(card_number_outside_dialog_handler,
                                lambda message:
                                looks_like_card_number(message.text))
    dp.register_message_handler(not_understood_handler,
                                content_types=ContentTypes.ANY)

    dp.register_errors_handler(errors_handler)
