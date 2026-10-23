from aiogram.types import CallbackQuery, ChatType, Message

from bot.texts import t, get_lang


def not_private(update: Message | CallbackQuery) -> bool:
    if isinstance(update, CallbackQuery):
        # Buttons of inline messages have no chat to check
        if update.message is None:
            return False
        chat = update.message.chat
    else:
        chat = update.chat

    return chat.type != ChatType.PRIVATE


async def group_message_handler(message: Message) -> None:
    # Card numbers shown here would be seen by everyone in the chat. Only
    # commands get an answer, so the bot does not flood the group
    if message.is_command():
        await message.answer(text=t(get_lang(message.from_user),
                                    'private_only'))


async def group_callback_handler(call: CallbackQuery) -> None:
    await call.answer(text=t(get_lang(call.from_user), 'private_only'),
                      show_alert=True)
