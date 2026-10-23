from aiogram import Bot
from aiogram.utils.exceptions import MessageToEditNotFound

import bot.handlers.hiding as hiding
from conftest import add_card


def bot_messages(replies) -> list:
    """Bot calls that show something, leaving out deleted user inputs."""
    return [r for r in replies if r.method != 'deleteMessage']


def test_adding_from_button_edits_one_message(chat):
    replies = chat.press('nav:add')
    replies += chat.send('two words')
    replies += chat.send('mono')
    replies += chat.send('1234')
    replies += chat.send('4242 4242 4242 4242')

    shown = [r for r in bot_messages(replies)
             if r.method != 'answerCallbackQuery']

    assert [r.method for r in shown] == ['editMessageText'] * 5
    # The menu button sits on message 1, so the whole flow stays there
    assert {r.message_id for r in shown} == {1}
    assert shown[-1].text == 'Card added.'


def test_adding_from_command_edits_the_prompt(chat):
    deleted_command, prompt = chat.send('/add')
    replies = chat.send('mono')
    replies += chat.send('4242424242424242')

    assert prompt.method == 'sendMessage'
    assert [(r.method, r.message_id) for r in bot_messages(replies)] == [
        ('editMessageText', prompt.message_id),
        ('editMessageText', prompt.message_id),
    ]


def test_changing_number_edits_the_card_message(chat):
    add_card(chat, '4242424242424242', 'mono')

    chat.press('card:edit:1')
    replies = chat.send('1111')
    replies += chat.send('5555555555554444')

    assert [(r.method, r.message_id) for r in bot_messages(replies)] == [
        ('editMessageText', 1),
        ('editMessageText', 1),
    ]
    assert replies[-1].text == 'Information saved.'


def test_renaming_shows_the_card_in_the_same_message(chat):
    add_card(chat, '4242424242424242', 'mono')

    chat.press('card:rename:1')
    replies = chat.send('black')

    shown, = bot_messages(replies)
    assert (shown.method, shown.message_id) == ('editMessageText', 1)
    assert 'black' in shown.text
    # The number shown after renaming is hidden later like any other
    assert (42, 1) in hiding.pending


def test_deleted_prompt_is_replaced_by_a_new_message(chat, monkeypatch):
    chat.press('nav:add')

    original = Bot.edit_message_text

    async def prompt_gone(self, *args, **kwargs):
        if kwargs.get('message_id') == 1:
            raise MessageToEditNotFound('Message to edit not found')
        return await original(self, *args, **kwargs)

    monkeypatch.setattr(Bot, 'edit_message_text', prompt_gone)

    first = bot_messages(chat.send('mono'))
    second = bot_messages(chat.send('4242424242424242'))

    new_prompt, = first
    assert new_prompt.method == 'sendMessage'
    assert new_prompt.text == 'Enter card number:'
    assert [(r.method, r.message_id) for r in second] == [
        ('editMessageText', new_prompt.message_id)]
    assert second[0].text == 'Card added.'
