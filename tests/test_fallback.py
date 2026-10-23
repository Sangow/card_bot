import pytest

from conftest import add_card

STICKER = {'file_id': 'x', 'file_unique_id': 'y', 'width': 1, 'height': 1,
           'is_animated': False, 'is_video': False, 'type': 'regular'}


def send_sticker(chat) -> list:
    chat.last_message_id = next(chat.harness.ids)
    return chat.harness.process({'message': {
        'message_id': chat.last_message_id, 'date': 0,
        'chat': {'id': chat.user['id'], 'type': 'private'},
        'from': chat.user, 'sticker': STICKER,
    }})


def deleted(replies) -> list:
    return [r.data['message_id'] for r in replies
            if r.method == 'deleteMessage']


def shown(replies) -> list:
    return [r for r in replies if r.method != 'deleteMessage']


@pytest.mark.parametrize('text', ['hello', 'покажи картки', '/unknown'])
def test_unknown_text_gets_menu(chat, text):
    replies = chat.send(text)

    assert [(r.method, r.text) for r in replies] == [
        ('sendMessage', 'I did not understand that. Use the buttons:')]
    assert replies[0].callbacks == ['nav:cards', 'nav:add']


@pytest.mark.parametrize('text', ['4242 4242 4242 4242',
                                  '4242-4242-4242-4241',
                                  '4242424242424242'])
def test_card_number_outside_dialog_is_deleted(chat, harness, text):
    replies = chat.send(text)

    assert deleted(replies) == [chat.last_message_id]
    hint, = shown(replies)
    assert hint.text.startswith('Your message with a card number was deleted')
    assert hint.callbacks == ['nav:cards', 'nav:add']
    assert harness.rows() == []


def test_short_number_is_not_treated_as_card(chat):
    replies = chat.send('12345')

    assert deleted(replies) == []
    assert replies[0].text == 'I did not understand that. Use the buttons:'


def test_sticker_outside_dialog_gets_menu_and_stays(chat):
    replies = send_sticker(chat)

    assert deleted(replies) == []
    assert replies[0].text == 'I did not understand that. Use the buttons:'


def test_sticker_instead_of_nickname(chat):
    chat.press('nav:add')

    replies = send_sticker(chat)

    assert deleted(replies) == [chat.last_message_id]
    prompt, = shown(replies)
    assert (prompt.method, prompt.message_id) == ('editMessageText', 1)
    assert prompt.text == 'Send the nickname as text:'
    assert chat.state() == 'AddCard:card_nickname'

    chat.send('mono')
    chat.send('4242424242424242')
    assert chat.harness.rows() == [('42', '4242424242424242', 'mono')]


def test_sticker_instead_of_number(chat):
    chat.press('nav:add')
    chat.send('mono')

    prompt, = shown(send_sticker(chat))

    assert prompt.text == 'Send the card number as text:'
    assert prompt.callbacks == ['nav:main']
    assert chat.state() == 'AddCard:card_number'


def test_sticker_while_changing_number_keeps_leave_previous(chat):
    add_card(chat, '4242424242424242', 'mono')
    chat.press('card:edit:1')

    prompt, = shown(send_sticker(chat))

    assert prompt.text == 'Send the card number as text:'
    assert prompt.callbacks == ['card:show:1']
    assert chat.state() == 'ShowCard:edit_card_number'


def test_sticker_while_renaming_keeps_leave_previous(chat):
    add_card(chat, '4242424242424242', 'mono')
    chat.press('card:rename:1')

    prompt, = shown(send_sticker(chat))

    assert prompt.text == 'Send the nickname as text:'
    assert prompt.callbacks == ['card:show:1']


def test_fallback_in_ukrainian(harness):
    chat = harness.chat(language_code='uk')

    assert chat.send('привіт')[0].text == \
        'Не зрозумів. Скористайтеся кнопками:'
    assert shown(chat.send('4242 4242 4242 4242'))[0].text.startswith(
        'Повідомлення з номером картки видалено')


def test_dialogs_still_take_text_first(chat, harness):
    chat.send('/add')
    chat.send('hello')                       # a nickname, not a fallback
    chat.send('4242 4242 4242 4242')         # the number of that card

    assert harness.rows() == [('42', '4242424242424242', 'hello')]
