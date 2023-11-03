from aiogram.types import InlineQuery, InlineQueryResultArticle, \
    InputTextMessageContent
from uuid import uuid4

from bot.sql import get_card_number_and_nick


async def inline_echo(query: InlineQuery) -> None:
    card_nicks_numbers: list = await get_card_number_and_nick(query.from_user.id)

    if not card_nicks_numbers:
        return await query.answer(results=[InlineQueryResultArticle(
            id=str(uuid4()),
            title='Oooops!',
            input_message_content=InputTextMessageContent(message_text='err'),
            description='You need to add a card!'
        )])

    items = []

    for c_n_n in card_nicks_numbers:
        items.append(InlineQueryResultArticle(
            id=str(uuid4()),
            title=c_n_n[0],
            input_message_content=InputTextMessageContent(
                message_text=f'⬇️<b>Tap to copy</b>⬇️\n\n'
                             f'<code>{c_n_n[1]}</code>\n\n'
                             f'⬆️<b>Tap to copy</b>⬆️',
                parse_mode='html')
        ))

    await query.answer(results=items,
                       cache_time=1)
