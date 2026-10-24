import json
import sqlite3

import pytest

import bot.sql.sq as sq
from conftest import add_card


def add_cards(chat, nicknames) -> None:
    for nickname in nicknames:
        add_card(chat, '4242424242424242', nickname)


def list_labels(chat) -> list:
    reply = chat.press('nav:cards')[0]
    return [text for row in reply.buttons for text, data in row
            if data.startswith('card:')]


def inline_titles(harness, chat) -> list:
    replies = harness.process({'inline_query': {
        'id': str(next(harness.ids)), 'from': chat.user,
        'query': '', 'offset': '',
    }})
    answer, = [r for r in replies if r.method == 'answerInlineQuery']
    results = answer.data['results']
    if isinstance(results, str):
        results = json.loads(results)

    return [r['title'] for r in results]


def test_card_view_offers_to_make_favorite(chat):
    add_cards(chat, ['mono'])

    view = chat.press('card:show:1')[0]

    assert view.buttons[1] == [('⭐ Make favorite', 'card:favorite:1')]


def test_favorite_button_switches_to_remove(chat):
    add_cards(chat, ['mono'])

    view = chat.press('card:favorite:1')[0]

    assert view.buttons[1] == [('☆ Remove from favorites',
                                'card:unfavorite:1')]


def test_favorite_card_comes_first_with_a_star(chat):
    add_cards(chat, ['a', 'b', 'c'])

    chat.press('card:favorite:3')

    assert list_labels(chat) == ['⭐ c •••• 4242 · Visa',
                                 'a •••• 4242 · Visa',
                                 'b •••• 4242 · Visa']


def test_only_one_card_is_favorite(chat):
    add_cards(chat, ['a', 'b', 'c'])

    chat.press('card:favorite:3')
    chat.press('card:favorite:2')

    labels = list_labels(chat)
    assert labels[0] == '⭐ b •••• 4242 · Visa'
    assert sum(label.startswith('⭐') for label in labels) == 1


def test_removing_favorite_restores_order(chat):
    add_cards(chat, ['a', 'b', 'c'])
    chat.press('card:favorite:3')

    chat.press('card:unfavorite:3')

    assert list_labels(chat) == ['a •••• 4242 · Visa',
                                 'b •••• 4242 · Visa',
                                 'c •••• 4242 · Visa']


def test_favorite_card_comes_first_in_inline_mode(harness, chat):
    add_cards(chat, ['a', 'b', 'c'])

    chat.press('card:favorite:2')

    assert inline_titles(harness, chat) == ['⭐ b •••• 4242 · Visa',
                                            'a •••• 4242 · Visa',
                                            'c •••• 4242 · Visa']


def test_back_from_favorite_card_goes_to_first_page(chat):
    add_cards(chat, ['a', 'b', 'c', 'd', 'e', 'f', 'g'])
    assert chat.press('card:show:7')[0].buttons[-1] == [('⬅️ Back',
                                                        'cards:1')]

    view = chat.press('card:favorite:7')[0]

    assert view.buttons[-1] == [('⬅️ Back', 'cards:0')]


def test_other_users_card_cannot_be_made_favorite(harness):
    owner = harness.chat(user_id=1)
    stranger = harness.chat(user_id=2)
    add_cards(owner, ['a', 'b'])

    replies = stranger.press('card:favorite:2')

    assert replies[0].text == 'Card not found.'
    assert inline_titles(harness, owner) == ['a •••• 4242 · Visa',
                                             'b •••• 4242 · Visa']


def test_database_allows_only_one_favorite_per_user(chat):
    add_cards(chat, ['a', 'b'])
    chat.press('card:favorite:1')

    with pytest.raises(sqlite3.IntegrityError):
        sq.cur.execute('UPDATE cards SET favorite=1 WHERE id=2')


def test_favorite_buttons_in_ukrainian(harness):
    chat = harness.chat(language_code='uk')
    add_cards(chat, ['mono'])

    assert chat.press('card:show:1')[0].buttons[1][0][0] == \
        '⭐ Зробити улюбленою'
    assert chat.press('card:favorite:1')[0].buttons[1][0][0] == \
        '☆ Прибрати з улюблених'
