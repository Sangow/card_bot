from aiogram.types import InlineQuery, InlineQueryResultArticle, \
    InputTextMessageContent
import hashlib


async def inline_echo(query: InlineQuery) -> None:
    print('inline')
    text = query.query or 'echo'
    input_content = InputTextMessageContent(text)
    result_id = hashlib.md5(text.encode()).hexdigest()

    item = InlineQueryResultArticle(
        id=result_id,
        title=text,
        input_message_content=input_content
    )

    await query.answer(results=[item],
                       cache_time=1)
