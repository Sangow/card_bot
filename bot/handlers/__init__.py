from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import CommandStart, Text

from bot.keyboards import nav_cb, card_cb
from bot.states import AddCard, ShowCard
from .service import validate_card_number, validate_card_nickname
from .user_handlers import cmd_start, cmd_cancel, main_menu_handler, \
    add_card_1, add_card_2, add_card_2_fail, add_card_3, add_card_3_fail, \
    show_cards_handler, show_card_handler, edit_card_handler, \
    edit_card_number_fail_handler, edit_card_number_handler, \
    confirm_delete_card_handler, delete_card_handler


async def register_handlers(dp: Dispatcher) -> None:
    dp.register_message_handler(cmd_start,
                                CommandStart(),
                                state='*')
    dp.register_message_handler(cmd_cancel,
                                Text(equals='cancel', ignore_case=True),
                                state='*')
    # Buttons of the old reply keyboard
    dp.register_message_handler(cmd_start,
                                Text(equals=['show cards', 'add card'],
                                     ignore_case=True),
                                state='*')

    dp.register_callback_query_handler(main_menu_handler,
                                       nav_cb.filter(to='main'),
                                       state='*')

    dp.register_callback_query_handler(add_card_1,
                                       nav_cb.filter(to='add'),
                                       state='*')
    dp.register_message_handler(add_card_2_fail,
                                lambda message:
                                not validate_card_number(message.text),
                                state=AddCard.card_number)
    dp.register_message_handler(add_card_2,
                                state=AddCard.card_number)
    dp.register_message_handler(add_card_3_fail,
                                lambda message:
                                not validate_card_nickname(message.text),
                                state=AddCard.card_nickname)
    dp.register_message_handler(add_card_3,
                                state=AddCard.card_nickname)

    dp.register_callback_query_handler(show_cards_handler,
                                       nav_cb.filter(to='cards'),
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
    dp.register_message_handler(edit_card_number_handler,
                                state=ShowCard.edit_card_number)

    dp.register_callback_query_handler(confirm_delete_card_handler,
                                       card_cb.filter(action='confirm_delete'),
                                       state='*')
    dp.register_callback_query_handler(delete_card_handler,
                                       card_cb.filter(action='delete'),
                                       state='*')
