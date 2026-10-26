import pytest

import bot.handlers.throttling as throttling
from bot.handlers.throttling import RATE_LIMIT, RATE_PERIOD, MESSAGE_LIMIT
from conftest import add_card
from test_favorite import inline_titles

WARNING = 'Too many actions. Please wait a few seconds.'


@pytest.fixture
def clock(harness, monkeypatch):
    """Turns the limit back on, with time that only moves when told to."""
    now = [1000.0]
    monkeypatch.setattr(throttling, 'RATE_LIMIT', RATE_LIMIT)
    monkeypatch.setattr(throttling, 'MESSAGE_LIMIT', MESSAGE_LIMIT)
    monkeypatch.setattr(throttling, 'monotonic', lambda: now[0])

    return now


def middleware(harness) -> throttling.ThrottlingMiddleware:
    app, = [app for app in harness.dp.middleware.applications
            if isinstance(app, throttling.ThrottlingMiddleware)]
    return app


def use_up_limit(chat) -> None:
    for _ in range(RATE_LIMIT):
        chat.press('nav:about')


def test_presses_up_to_the_limit_are_handled(chat, clock):
    for _ in range(RATE_LIMIT - 1):
        chat.press('nav:about')

    replies = chat.press('nav:about')

    assert [r.method for r in replies] == ['editMessageText',
                                           'answerCallbackQuery']


def test_presses_over_the_limit_are_ignored_with_one_warning(chat, clock):
    use_up_limit(chat)

    first = chat.press('nav:about')
    second = chat.press('nav:about')

    assert [r.method for r in first] == ['answerCallbackQuery']
    assert first[0].text == WARNING
    assert first[0].data['show_alert'] is True
    # Later presses are only answered, so the button stops spinning
    assert [r.method for r in second] == ['answerCallbackQuery']
    assert not second[0].text


def test_limit_is_lifted_after_the_period(chat, clock):
    use_up_limit(chat)
    chat.press('nav:about')

    clock[0] += RATE_PERIOD

    replies = chat.press('nav:about')
    assert replies[0].method == 'editMessageText'


def test_warning_comes_again_in_the_next_burst(chat, clock):
    use_up_limit(chat)
    chat.press('nav:about')

    clock[0] += RATE_PERIOD
    use_up_limit(chat)

    assert chat.press('nav:about')[0].text == WARNING


def test_ignored_message_gets_one_warning(chat, clock):
    use_up_limit(chat)

    first = chat.send('/cards')
    second = chat.send('/cards')

    assert [(r.method, r.text) for r in first] == [('sendMessage', WARNING)]
    assert second == []


def test_ignored_card_number_is_still_deleted(chat, harness, clock):
    chat.send('/add')
    chat.send('mono')
    for _ in range(RATE_LIMIT - 2):
        chat.press('nav:about')

    replies = chat.send('4242 4242 4242 4242')

    assert [r.method for r in replies] == ['deleteMessage', 'sendMessage']
    assert replies[1].text == WARNING
    assert harness.rows() == []


def test_ignored_card_number_with_text_is_still_deleted(chat, clock):
    use_up_limit(chat)

    replies = chat.send('mono 4242 4242 4242 4242')

    assert [r.method for r in replies] == ['deleteMessage', 'sendMessage']
    assert replies[1].text == WARNING


def test_ignored_text_is_not_deleted(chat, clock):
    use_up_limit(chat)

    replies = chat.send('hello')

    assert 'deleteMessage' not in [r.method for r in replies]


def test_ukrainian_warning(harness, clock):
    chat = harness.chat(language_code='uk')
    use_up_limit(chat)

    replies = chat.press('nav:about')

    assert replies[0].text == 'Забагато дій. Зачекайте кілька секунд.'


def test_limit_is_per_user(harness, clock):
    busy = harness.chat(user_id=1)
    other = harness.chat(user_id=2)
    use_up_limit(busy)

    assert busy.press('nav:about')[0].text == WARNING
    assert other.press('nav:about')[0].method == 'editMessageText'


def test_inline_queries_over_the_limit_are_ignored(harness, chat, clock):
    add_card(chat, '4242424242424242', 'mono')
    for _ in range(RATE_LIMIT - 4):
        chat.press('nav:about')

    assert inline_titles(harness, chat) == ['mono •••• 4242 · Visa']
    with pytest.raises(ValueError):
        # No answer at all, so there is nothing to unpack
        inline_titles(harness, chat)


def test_quiet_users_are_forgotten(harness, clock, monkeypatch):
    monkeypatch.setattr(throttling, 'MAX_TRACKED_USERS', 2)
    for user_id in (1, 2, 3):
        harness.chat(user_id=user_id).press('nav:about')

    clock[0] += RATE_PERIOD
    harness.chat(user_id=4).press('nav:about')

    assert set(middleware(harness).users) == {4}


def use_up_message_limit(chat) -> None:
    for _ in range(MESSAGE_LIMIT):
        chat.send('/help')


def test_messages_up_to_their_limit_are_handled(chat, clock):
    for _ in range(MESSAGE_LIMIT - 1):
        chat.send('/help')

    assert chat.send('/help')[-1].text != WARNING


def test_messages_over_their_limit_are_ignored(chat, clock):
    use_up_message_limit(chat)

    first = chat.send('/help')
    second = chat.send('/help')

    assert [(r.method, r.text) for r in first] == [('sendMessage', WARNING)]
    assert second == []


def test_presses_work_when_messages_are_limited(chat, clock):
    use_up_message_limit(chat)
    chat.send('/help')

    replies = chat.press('nav:about')

    assert replies[0].method == 'editMessageText'


def test_message_limit_is_lifted_after_the_period(chat, clock):
    use_up_message_limit(chat)
    chat.send('/help')

    clock[0] += RATE_PERIOD

    assert chat.send('/help')[-1].text != WARNING


def test_messages_also_count_towards_the_limit_of_all_updates(chat, clock):
    messages = MESSAGE_LIMIT // 2
    for _ in range(RATE_LIMIT - messages):
        chat.press('nav:about')
    for _ in range(messages - 1):
        chat.send('/help')

    assert chat.send('/help')[-1].text != WARNING
    # Fewer messages than their own limit, but all updates reach theirs
    assert chat.send('/help')[-1].text == WARNING
