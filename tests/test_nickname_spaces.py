import json

import pytest

from bot.handlers.service import validate_card_nickname, \
    normalize_card_nickname, MAX_NICKNAME_LENGTH
from conftest import add_card

CONTAINS_NUMBER = ('A nickname must not contain a card number. '
                   'Choose another nickname:')


@pytest.mark.parametrize('card_nickname', [
    'Моно чорна', 'privat salary card', '  mono  black  ',
])
def test_nicknames_with_spaces_are_valid(card_nickname):
    assert validate_card_nickname(card_nickname)


@pytest.mark.parametrize('card_nickname, normalized', [
    ('Моно чорна', 'Моно чорна'),
    ('  Моно   чорна  ', 'Моно чорна'),
    ('mono', 'mono'),
])
def test_spaces_are_trimmed_and_squeezed(card_nickname, normalized):
    assert normalize_card_nickname(card_nickname) == normalized


@pytest.mark.parametrize('card_nickname', [
    'mono\tblack',
    'mono\nblack',
    '4242 4242 4242 4242',
    '4242424242424242',
    '4242-4242-4242-4242',
])
def test_multiline_and_number_like_nicknames_are_invalid(card_nickname):
    assert not validate_card_nickname(card_nickname)


def test_length_limit_counts_squeezed_spaces():
    assert validate_card_nickname('a' + ' ' * 40 + 'b')
    assert not validate_card_nickname('a ' * MAX_NICKNAME_LENGTH)


def card_rows(harness) -> list:
    return [nickname for _, _, nickname in harness.rows()]


def test_card_with_spaces_in_nickname_is_added(chat, harness):
    replies = add_card(chat, '4242424242424242', '  Моно   чорна ')

    assert replies[-1].text == 'Card added.'
    assert card_rows(harness) == ['Моно чорна']


def test_nickname_with_spaces_is_shown_in_the_list(chat):
    add_card(chat, '4242424242424242', 'Моно чорна')

    reply = chat.press('nav:cards')[0]

    assert reply.buttons[0] == [('Моно чорна •••• 4242 · Visa',
                                 'card:show:1')]


def test_nickname_differing_in_spaces_or_case_is_taken(chat, harness):
    add_card(chat, '4242424242424242', 'Моно чорна')

    chat.send('/add')
    replies = chat.send('моно   ЧОРНА')

    assert replies[-1].text.startswith('Nickname of your card should be')
    assert chat.state() == 'AddCard:card_nickname'
    assert card_rows(harness) == ['Моно чорна']


def test_card_is_renamed_to_nickname_with_spaces(chat, harness):
    add_card(chat, '4242424242424242', 'mono')

    chat.press('card:rename:1')
    replies = chat.send('Моно  чорна')

    assert 'Моно чорна' in replies[-1].text
    assert card_rows(harness) == ['Моно чорна']


def test_number_like_nickname_is_rejected(chat, harness):
    chat.send('/add')

    replies = chat.send('4242 4242 4242 4242')

    assert replies[0].method == 'deleteMessage'
    assert replies[-1].text == CONTAINS_NUMBER
    assert chat.state() == 'AddCard:card_nickname'


def test_card_cannot_be_renamed_to_number_like_nickname(chat, harness):
    add_card(chat, '4242424242424242', 'mono')

    chat.press('card:rename:1')
    replies = chat.send('4242 4242 4242 4242')

    assert replies[-1].text == CONTAINS_NUMBER
    assert card_rows(harness) == ['mono']


def test_number_like_nickname_in_ukrainian(harness):
    chat = harness.chat(language_code='uk')
    chat.send('/add')

    replies = chat.send('4242424242424242')

    assert replies[-1].text == ('Назва не має містити номер картки. '
                                'Оберіть іншу назву:')


def inline_titles(harness, chat, query: str) -> list:
    replies = harness.process({'inline_query': {
        'id': str(next(harness.ids)), 'from': chat.user,
        'query': query, 'offset': '',
    }})
    answer, = [r for r in replies if r.method == 'answerInlineQuery']
    results = answer.data['results']
    if isinstance(results, str):
        results = json.loads(results)

    return [r['title'] for r in results]


def test_share_offers_just_the_card_with_spaces(harness, chat):
    add_card(chat, '4242424242424242', 'моно')
    add_card(chat, '5555555555554444', 'моно чорна')

    # What the Share button types in for each card
    assert inline_titles(harness, chat, 'моно чорна') == [
        'моно чорна •••• 4444 · MC']
    assert inline_titles(harness, chat, 'моно') == ['моно •••• 4242 · Visa']
