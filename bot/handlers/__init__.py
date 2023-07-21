from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import CommandStart, Text

from bot.states import AddCard, ShowCard
from .user_handlers import cmd_start, cmd_cancel, \
    add_card_1, add_card_2, add_card_3, add_card_4, \
    show_cards_nicknames, show_card_number, \
    callback_delete, callback_edit


async def register_handlers(dp: Dispatcher) -> None:
    dp.register_message_handler(cmd_start, CommandStart())
    dp.register_message_handler(cmd_cancel, Text(equals='cancel', ignore_case=True), state='*')

    dp.register_message_handler(add_card_1, Text(equals='add card', ignore_case=True))
    dp.register_message_handler(add_card_2, state=AddCard.card_number)
    dp.register_message_handler(add_card_3, state=AddCard.card_nickname)
    dp.register_message_handler(add_card_4, Text(equals='confirm', ignore_case=True), state=AddCard.confirm)

    dp.register_message_handler(show_cards_nicknames, Text(equals='show cards', ignore_case=True))
    dp.register_message_handler(show_card_number, state=ShowCard.show_card_number)

    dp.register_callback_query_handler(callback_delete, lambda callback: callback.data == 'delete_callback')
    dp.register_callback_query_handler(callback_edit, lambda callback: callback.data == 'edit_callback')
