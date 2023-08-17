from aiogram.dispatcher import FSMContext
from aiogram.types import Message

from bot.keyboards import start_kb, cancel_kb, confirm_kb, nickname_kb, \
    leave_previous_kb, edit_delete_kb
from bot.sql import get_cards_nicknames, add_card, get_card_number, \
    delete_card, edit_card
from bot.states import AddCard, ShowCard


async def cmd_start(message: Message, state: FSMContext) -> None:
    if await state.get_state():
        await state.finish()

    await message.answer(
        text='Choose button:',
        reply_markup=start_kb
    )


async def cmd_cancel(message: Message, state: FSMContext) -> None:
    if await state.get_state():
        await state.finish()

    await message.answer(text='Cancelled.', reply_markup=start_kb)


async def add_card_1(message: Message) -> None:
    await message.answer(text='Enter card number:', reply_markup=cancel_kb)
    await AddCard.card_number.set()


async def add_card_2_fail(message: Message) -> None:
    await message.answer(text='Credit card is invalid.')


async def add_card_2(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['card_number'] = message.text

    await message.answer(text='Enter card nickname (without spaces):')

    await AddCard.next()


async def add_card_3_fail(message: Message) -> None:
    await message.answer(text='Choose another nickname (without spaces):')


async def add_card_3(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['card_nickname'] = message.text

    await message.answer(text='Do you confirm?',
                         reply_markup=confirm_kb)

    await AddCard.next()


async def add_card_4(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        try:
            await add_card(user_id=message.from_user.id,
                           card_number=data['card_number'],
                           card_nickname=data['card_nickname'])
        except:
            await message.answer(
                text='Nickname of your card should be unique.\n'
                     'Choose another nickname (without spaces):',
                reply_markup=cancel_kb
            )
            await AddCard.card_nickname.set()
            return

    await message.answer(text='Confirmed.',
                         reply_markup=start_kb)
    await state.finish()


async def show_nickname_list(message: Message) -> None:
    nicks = await get_cards_nicknames(user_id=message.from_user.id)

    if not nicks:
        await message.answer(text='There is no card.')
        return

    await message.answer(text='Choose your card:',
                         reply_markup=nickname_kb(nicks))

    await ShowCard.show_card_number.set()


async def show_card_number(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    card_nickname = message.text
    card_number = await get_card_number(user_id=user_id,
                                        card_nickname=card_nickname)

    async with state.proxy() as data:
        data['card_nickname'] = card_nickname
        data['card_number'] = card_number

    await message.answer(
        text=f'<b>Nickname:</b> {card_nickname}\n\n'
             f'⬇️<b>Tap to copy</b>⬇️\n\n'
             f'<code>{card_number}</code>\n\n'
             f'⬆️<b>Tap to copy</b>⬆️',
        parse_mode='html',
        reply_markup=edit_delete_kb
    )

    await ShowCard.edit_delete_card.set()


async def edit_card_handler(message: Message) -> None:
    await message.answer(text='Enter new card number:',
                         reply_markup=leave_previous_kb)

    await ShowCard.edit_card_number.set()


async def edit_card_number_previous_handler(message: Message) -> None:
    await message.answer(text='Do you confirm?',
                         reply_markup=confirm_kb)

    await ShowCard.confirm.set()


async def edit_card_number_fail_handler(message: Message) -> None:
    await message.answer(text='Credit card is invalid.')


async def edit_card_number_handler(
        message: Message,
        state: FSMContext) -> None:
    async with state.proxy() as data:
        data['card_number'] = message.text

    await message.answer(text='Do you confirm?',
                         reply_markup=confirm_kb)

    await ShowCard.confirm.set()


# async def edit_card_nickname_previous_handler(message: Message) -> None:
#     await message.answer(text='Do you confirm?',
#                          reply_markup=confirm_kb)
#
#     await ShowCard.confirm.set()
#
#
# async def edit_card_nickname_fail_handler(message: Message) -> None:
#     await message.answer(text='Choose another nickname (without spaces):')
#
#
# async def edit_card_nickname_handler(
#         message: Message,
#         state: FSMContext) -> None:
#     new_card_nickname = message.text
#
#     async with state.proxy() as data:
#         data['card_nickname'] = new_card_nickname
#
#     await message.answer(text='Do you confirm?',
#                          reply_markup=confirm_kb)
#
#     await ShowCard.confirm.set()


async def confirm_edited_card_handler(
        message: Message,
        state: FSMContext) -> None:
    async with state.proxy() as data:
        await edit_card(user_id=message.from_user.id,
                        card_nickname=data['card_nickname'],
                        new_card_number=data['card_number'])

    await message.answer(text='Confirmed.',
                         reply_markup=start_kb)
    await state.finish()


async def delete_card_handler(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        await delete_card(
            user_id=message.from_user.id,
            card_nickname=data['card_nickname']
        )
    await message.answer(text='Card deleted.',
                         reply_markup=start_kb)

    await state.finish()
