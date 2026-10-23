from aiogram.types import InlineQuery, InlineQueryResultArticle, \
    InputTextMessageContent

from bot.config import CARD_ICONS_URL
from bot.sql import get_cards
from bot.texts import t, get_lang
from .service import card_label, card_icon, format_card_number

ICON_SIZE = 192


def card_result(card_id: int, card_nickname: str,
                card_number: str) -> InlineQueryResultArticle:
    icon = f'{CARD_ICONS_URL}/{card_icon(card_number)}.png'
    result = InlineQueryResultArticle(
        id=str(card_id),
        # The title is seen only by the user; the chat gets the number
        title=card_label(card_nickname, card_number),
        input_message_content=InputTextMessageContent(
            message_text=f'💳 <code>{format_card_number(card_number)}</code>',
            parse_mode='html'
        ),
        thumb_url=icon,
        thumb_width=ICON_SIZE,
        thumb_height=ICON_SIZE
    )
    # aiogram 2 knows only the names Bot API 6.6 renamed; send the new ones
    # too, so the icon shows whichever Telegram reads
    result.values.update(thumbnail_url=icon, thumbnail_width=ICON_SIZE,
                         thumbnail_height=ICON_SIZE)

    return result


async def inline_cards_handler(query: InlineQuery) -> None:
    lang = get_lang(query.from_user)
    wanted = query.query.strip().casefold()

    cards = await get_cards(user_id=query.from_user.id)

    # Nicknames are unique per user, so an exact match means that one card:
    # the Share button relies on it to offer just the card it was pressed on
    exact = [card for card in cards if card[1].casefold() == wanted]
    if wanted and exact:
        cards = exact

    results = [
        card_result(card_id, card_nickname, card_number)
        for card_id, card_nickname, card_number in cards
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
