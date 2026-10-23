import pytest

import bot.handlers.error_handlers as error_handlers
import bot.handlers.user_handlers as user_handlers
from conftest import Reply, add_card

ADMIN = 777


@pytest.fixture(autouse=True)
def clean_alerts(monkeypatch):
    monkeypatch.setattr(error_handlers, 'alerts', {})
    monkeypatch.setattr(error_handlers, 'ADMIN_CHAT_ID', ADMIN)


@pytest.fixture
def broken_list(monkeypatch):
    async def broken(**kwargs):
        raise RuntimeError('db is down')

    monkeypatch.setattr(user_handlers, 'get_cards', broken)


def alerts_in(replies) -> list:
    return [r for r in replies
            if r.method == 'sendMessage' and r.data.get('chat_id') == ADMIN]


def test_error_is_reported_to_admin(chat, broken_list):
    replies = chat.press('nav:cards')

    alert, = alerts_in(replies)
    assert 'RuntimeError: db is down' in alert.text
    assert 'натискання кнопки' in alert.text
    # The user still gets their own message
    assert replies[0].method == 'answerCallbackQuery'


def test_alert_has_no_user_data(harness, monkeypatch):
    # An id that cannot turn up in the alert's time by chance
    chat = harness.chat(user_id=918273645)
    add_card(chat, '4242424242424242', 'secretnick')

    async def broken(**kwargs):
        raise RuntimeError('rename failed')

    monkeypatch.setattr(user_handlers, 'rename_card_by_id', broken)
    chat.press('card:rename:1')
    alert, = alerts_in(chat.send('anothersecret'))

    for private in ('4242424242424242', 'secretnick', 'anothersecret',
                    '918273645'):
        assert private not in alert.text


def test_same_error_is_not_repeated_within_interval(chat, broken_list,
                                                    monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(error_handlers, 'monotonic', lambda: now[0])

    assert len(alerts_in(chat.press('nav:cards'))) == 1
    for _ in range(3):
        now[0] += 60
        assert alerts_in(chat.press('nav:cards')) == []

    now[0] += error_handlers.ALERT_INTERVAL
    alert, = alerts_in(chat.press('nav:cards'))
    assert 'Повторилася ще 3 раз(ів)' in alert.text


def test_different_errors_are_each_reported(chat, broken_list, monkeypatch):
    chat.press('nav:cards')

    async def other(**kwargs):
        raise ValueError('another problem')

    monkeypatch.setattr(user_handlers, 'get_cards', other)

    alert, = alerts_in(chat.press('nav:cards'))
    assert 'ValueError: another problem' in alert.text


def test_no_alerts_without_admin_chat(chat, broken_list, monkeypatch):
    monkeypatch.setattr(error_handlers, 'ADMIN_CHAT_ID', None)

    replies = chat.press('nav:cards')

    assert alerts_in(replies) == []
    assert [r.method for r in replies] == ['answerCallbackQuery']


def test_failed_alert_does_not_break_error_handling(chat, broken_list,
                                                    monkeypatch):
    from aiogram import Bot

    original = Bot.send_message

    async def telegram_down(self, chat_id, *args, **kwargs):
        if chat_id == ADMIN:
            raise RuntimeError('cannot reach admin')
        return await original(self, chat_id, *args, **kwargs)

    monkeypatch.setattr(Bot, 'send_message', telegram_down)

    replies = chat.press('nav:cards')

    assert replies[0].text == 'Something went wrong. Please try again.'
    assert chat.send('/start')[-1].text == 'Choose an action:'



def admin_messages(harness) -> list:
    return [Reply(method, data) for method, data in harness.calls
            if method == 'sendMessage' and data.get('chat_id') == ADMIN]


def test_startup_is_reported_to_admin(harness):
    harness.calls.clear()

    harness.restart()

    alert, = admin_messages(harness)
    assert alert.text.startswith('✅ Бот запущено')
    assert alert.buttons == [[('✅ Прочитано', 'nav:dismiss')]]


def test_startup_alert_can_be_turned_off(harness, monkeypatch):
    monkeypatch.setattr(error_handlers, 'STARTUP_ALERT', False)
    harness.calls.clear()

    harness.restart()

    assert admin_messages(harness) == []


def test_bot_starts_when_startup_alert_fails(harness, chat):
    from aiogram import Bot

    original = Bot.send_message

    async def telegram_down(self, chat_id, *args, **kwargs):
        raise RuntimeError('cannot reach admin')

    Bot.send_message = telegram_down
    try:
        harness.restart()
    finally:
        Bot.send_message = original

    assert chat.send('/start')[-1].text == 'Choose an action:'


def test_alert_time_is_in_kyiv_time(chat, broken_list):
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    before = datetime.now(ZoneInfo('Europe/Kyiv'))
    alert, = alerts_in(chat.press('nav:cards'))
    after = datetime.now(ZoneInfo('Europe/Kyiv'))

    assert 'UTC' not in alert.text
    # Either minute, in case the clock ticked over during the test
    assert any(f'Дата/час: {t:%d.%m %H:%M}' in alert.text
               for t in (before, after, after + timedelta(seconds=0)))


def test_admin_alert_has_read_button(chat, broken_list):
    alert, = alerts_in(chat.press('nav:cards'))

    assert alert.buttons == [[('✅ Прочитано', 'nav:dismiss')]]



def test_user_error_message_has_no_read_button(chat, monkeypatch):
    async def broken(**kwargs):
        raise RuntimeError('db is down')

    monkeypatch.setattr(user_handlers, 'nickname_taken', broken)
    chat.send('/add')

    replies = chat.send('mono')

    error, = [r for r in replies if r.text.startswith('Something went wrong')]
    assert error.buttons == []

def test_read_button_deletes_the_message(chat):
    chat.send('/add')

    replies = chat.press('nav:dismiss')

    assert [r.method for r in replies] == ['deleteMessage',
                                           'answerCallbackQuery']
    assert replies[0].data['message_id'] == 1
    # Whatever the user was doing goes on
    assert chat.state() == 'AddCard:card_nickname'
