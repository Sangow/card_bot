import pytest

import bot.handlers.hiding as hiding
from bot import shutdown_all
from conftest import Reply, add_card
from test_flows import luhn_number

HIDE_AFTER = 0.2


@pytest.fixture(autouse=True)
def short_timer(monkeypatch):
    monkeypatch.setattr(hiding, 'HIDE_AFTER', HIDE_AFTER)


def edits(replies) -> list:
    return [r for r in replies if r.method == 'editMessageText']


def test_shown_number_is_hidden_after_timeout(chat):
    add_card(chat, '4242424242424242', 'a&b')
    chat.press('card:show:1')

    assert edits(chat.harness.wait(HIDE_AFTER / 2)) == []

    hidden, = edits(chat.harness.wait(HIDE_AFTER))

    assert (hidden.data['chat_id'], hidden.data['message_id']) == (42, 1)
    assert '4242' not in hidden.text
    assert '🔒 Number hidden' in hidden.text
    assert 'a&amp;b' in hidden.text
    assert hidden.buttons == [[('👁 Show number', 'card:show:1'),
                               ('⬅️ Back', 'cards:0')]]


def test_leaving_the_card_cancels_hiding(chat):
    add_card(chat, '4242424242424242', 'mono')
    chat.press('card:show:1')
    chat.press('nav:cards')

    assert edits(chat.harness.wait(HIDE_AFTER * 2)) == []
    assert hiding.pending == {}


def test_showing_again_restarts_the_timer(chat):
    add_card(chat, '4242424242424242', 'mono')
    chat.press('card:show:1')
    chat.harness.wait(HIDE_AFTER * 0.6)

    chat.press('card:show:1')

    assert edits(chat.harness.wait(HIDE_AFTER * 0.6)) == []
    assert len(edits(chat.harness.wait(HIDE_AFTER))) == 1


def test_hidden_view_returns_to_the_cards_page(chat):
    for n in range(6):
        add_card(chat, luhn_number(n), f'card{n}')
    chat.press('card:show:6')

    hidden, = edits(chat.harness.wait(HIDE_AFTER * 2))

    assert ('⬅️ Back', 'cards:1') in hidden.buttons[0]


def test_renamed_card_view_is_hidden_too(chat):
    add_card(chat, '4242424242424242', 'mono')
    chat.press('card:rename:1')
    chat.send('black')

    hidden, = edits(chat.harness.wait(HIDE_AFTER * 2))

    assert 'black' in hidden.text
    assert '4242' not in hidden.text


def test_stopping_the_bot_hides_everything(harness):
    first = harness.chat(user_id=1)
    second = harness.chat(user_id=2)
    add_card(first, '4242424242424242', 'mono')
    add_card(second, '5555555555554444', 'privat')
    first.press('card:show:1')
    second.press('card:show:2')

    start = len(harness.calls)
    harness.loop.run_until_complete(shutdown_all(harness.dp))
    stopped = edits(Reply(method, data)
                    for method, data in harness.calls[start:])

    assert {r.data['chat_id'] for r in stopped} == {1, 2}
    assert all('🔒' in r.text for r in stopped)
    assert hiding.pending == {}
    assert edits(harness.wait(HIDE_AFTER * 2)) == []


def test_entered_numbers_and_nicknames_are_deleted(chat):
    chat.send('/add')

    nickname = chat.send('mono')
    assert nickname[0].method == 'deleteMessage'

    invalid = chat.send('1234 5678')
    assert invalid[0].method == 'deleteMessage'
    assert invalid[0].data['message_id'] == chat.last_message_id

    valid = chat.send('4242 4242 4242 4242')
    assert valid[0].method == 'deleteMessage'
    assert valid[0].data['message_id'] == chat.last_message_id


def test_changed_numbers_are_deleted(chat):
    add_card(chat, '4242424242424242', 'mono')
    chat.press('card:edit:1')

    for number in ('1111', '5555 5555 5555 4444'):
        replies = chat.send(number)

        assert replies[0].method == 'deleteMessage'
        assert replies[0].data['message_id'] == chat.last_message_id
