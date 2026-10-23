from aiogram.types import InlineQuery, InlineQueryResultArticle, \
    InputTextMessageContent

from bot.sql import get_cards
from bot.texts import t, get_lang
from .service import card_label, format_card_number


async def inline_cards_handler(query: InlineQuery) -> None:
    lang = get_lang(query.from_user)
    wanted = query.query.strip().casefold()

    results = [
        InlineQueryResultArticle(
            id=str(card_id),
            # The title is seen only by the user; the chat gets the number
            title=card_label(card_nickname, card_number),
            input_message_content=InputTextMessageContent(
                message_text=f'💳 <code>{format_card_number(card_number)}'
                             f'</code>',
                parse_mode='html'
            )
        )
        for card_id, card_nickname, card_number
        in await get_cards(user_id=query.from_user.id)
        if wanted in card_nickname.casefold()
    ]

    # Results are someone's card numbers: Telegram must neither cache them
    # nor show them to anyone else typing the same query
    await query.answer(
        results=results,
        cache_time=0,
        is_personal=True,
        switch_pm_text=None if results else t(lang, 'inline_add_card'),
        switch_pm_parameter=None if results else 'add'
    )
