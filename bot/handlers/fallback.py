from aiogram.dispatcher import FSMContext
from aiogram.types import Message

from bot.keyboards import main_ikb, cancel_ikb, edit_ikb, rename_ikb
from bot.states import AddCard, ShowCard
from bot.texts import t, get_lang
from .user_handlers import edit_prompt, delete_user_message

# Input steps that wait for a nickname or a card number as text
NICKNAME_STATES = (AddCard.card_nickname.state,
                   ShowCard.edit_card_nickname.state)
NUMBER_STATES = (AddCard.card_number.state, ShowCard.edit_card_number.state)


async def non_text_in_dialog_handler(message: Message,
                                     state: FSMContext) -> None:
    lang = get_lang(message.from_user)
    current = await state.get_state()

    await delete_user_message(message)

    async with state.proxy() as data:
        card_id = data.get('card_id')

    if current == ShowCard.edit_card_number.state:
        reply_markup = edit_ikb(card_id, lang)
    elif current == ShowCard.edit_card_nickname.state:
        reply_markup = rename_ikb(card_id, lang)
    else:
        reply_markup = cancel_ikb(lang)

    text_key = ('send_nickname_as_text' if current in NICKNAME_STATES
                else 'send_number_as_text')

    await edit_prompt(message, state, text=t(lang, text_key),
                      reply_markup=reply_markup)


async def card_number_outside_dialog_handler(message: Message) -> None:
    lang = get_lang(message.from_user)

    await delete_user_message(message)

    await message.answer(text=t(lang, 'number_outside_dialog'),
                         reply_markup=main_ikb(lang))


async def not_understood_handler(message: Message) -> None:
    lang = get_lang(message.from_user)

    await message.answer(text=t(lang, 'not_understood'),
                         reply_markup=main_ikb(lang))
