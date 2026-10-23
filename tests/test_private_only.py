import pytest

from conftest import add_card

GROUP = {'id': -100, 'type': 'group', 'title': 'Family'}
SUPERGROUP = {'id': -1001, 'type': 'supergroup', 'title': 'Work'}


def group_message(harness, user, chat, text):
    entities = ([{'type': 'bot_command', 'offset': 0,
                  'length': len(text.split()[0])}]
                if text.startswith('/') else [])
    return harness.process({'message': {
        'message_id': next(harness.ids), 'date': 0, 'chat': chat,
        'from': user, 'text': text, 'entities': entities,
    }})


def group_press(harness, user, chat, data):
    return harness.process({'callback_query': {
        'id': str(next(harness.ids)), 'from': user, 'chat_instance': 'g',
        'data': data,
        'message': {'message_id': 7, 'date': 0, 'chat': chat,
                    'from': {'id': 1, 'is_bot': True, 'first_name': 'bot'},
                    'text': 'menu'},
    }})


@pytest.mark.parametrize('chat', [GROUP, SUPERGROUP])
@pytest.mark.parametrize('command', ['/start', '/cards', '/add', '/help'])
def test_commands_in_groups_get_a_notice(harness, chat, command):
    user = harness.chat().user

    replies = group_message(harness, user, chat, command)

    assert [(r.method, r.text) for r in replies] == [
        ('sendMessage', 'I only work in private messages. '
                        'Open a chat with me to manage your cards.')]


def test_other_group_messages_are_ignored(harness):
    user = harness.chat().user

    assert group_message(harness, user, GROUP, 'hello everyone') == []


def test_card_is_not_shown_in_groups(harness):
    owner = harness.chat()
    add_card(owner, '4242424242424242', 'mono')

    replies = group_press(harness, owner.user, GROUP, 'card:show:1')

    assert [r.method for r in replies] == ['answerCallbackQuery']
    assert replies[0].data['show_alert'] is True
    assert not any('4242' in r.text for r in replies)


def test_adding_a_card_does_not_start_in_groups(harness):
    user = harness.chat()

    group_press(harness, user.user, GROUP, 'nav:add')
    group_message(harness, user.user, GROUP, '/add')

    group_state = harness.loop.run_until_complete(
        harness.dp.current_state(chat=GROUP['id'],
                                 user=user.user['id']).get_state())
    assert group_state is None


def test_ukrainian_notice(harness):
    user = harness.chat(language_code='uk').user

    replies = group_message(harness, user, GROUP, '/cards')

    assert replies[0].text.startswith('Я працюю лише в особистих')


def test_private_chats_still_work(chat):
    add_card(chat, '4242424242424242', 'mono')

    assert '4242 4242 4242 4242' in chat.press('card:show:1')[0].text
