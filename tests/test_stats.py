import pytest

import bot.handlers.admin as admin
from conftest import add_card

ADMIN = 42


@pytest.fixture(autouse=True)
def admin_is_test_user(monkeypatch):
    monkeypatch.setattr(admin, 'ADMIN_CHAT_ID', ADMIN)


def stats_message(replies):
    found = [r for r in replies if r.text.startswith('📊')]
    return found[0] if found else None


def test_admin_sees_stats(harness, chat):
    add_card(chat, '4242424242424242', 'mono')
    add_card(chat, '5555555555554444', 'privat')
    add_card(harness.chat(user_id=7), '4242424242424242', 'other')
    harness.chat(user_id=8).send('/add')

    replies = chat.send('/stats')

    message = stats_message(replies)
    assert 'Користувачів з картками: 2' in message.text
    assert 'Карток: 3' in message.text
    assert 'Найбільше в одного: 2 з 20' in message.text
    assert 'Незавершених діалогів: 1' in message.text
    assert 'Бот працює з: ' in message.text


def test_stats_has_no_user_data(harness, chat):
    add_card(chat, '4242424242424242', 'secretnick')

    message = stats_message(chat.send('/stats'))

    assert '4242' not in message.text
    assert 'secretnick' not in message.text


def test_stats_command_is_deleted_and_has_read_button(chat):
    replies = chat.send('/stats')

    assert replies[0].method == 'deleteMessage'
    assert replies[0].data['message_id'] == chat.last_message_id
    assert stats_message(replies).buttons == [[('✅ Прочитано',
                                                'nav:dismiss')]]


def test_other_users_get_not_understood(harness):
    stranger = harness.chat(user_id=9)

    replies = stranger.send('/stats')

    assert stats_message(replies) is None
    assert replies[-1].text == 'I did not understand that. Use the buttons:'


def test_no_stats_without_admin_chat(chat, monkeypatch):
    monkeypatch.setattr(admin, 'ADMIN_CHAT_ID', None)

    assert stats_message(chat.send('/stats')) is None


def test_stats_keep_current_dialog(chat):
    chat.send('/add')

    chat.send('/stats')

    assert chat.state() == 'AddCard:card_nickname'


def test_start_time_is_set_on_start(harness, chat, monkeypatch):
    monkeypatch.setattr(admin, 'started_at', None)

    harness.restart()

    started = admin.started_at.strftime('%d.%m %H:%M')
    assert stats_message(chat.send('/stats')).text.endswith(
        f'Бот працює з: {started}')
