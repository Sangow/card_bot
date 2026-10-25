import pytest

import bot.handlers.user_handlers as user_handlers
from conftest import add_card


def test_start_shows_menu_and_removes_old_keyboard(chat):
    replies = chat.send('/start')

    # The user's /start is deleted first
    assert replies[0].method == 'deleteMessage'
    assert replies[0].data['message_id'] == chat.last_message_id
    assert replies[1].markup == {'remove_keyboard': True}
    assert replies[2].callbacks == ['nav:cards', 'nav:add', 'nav:about']


def test_add_card(chat, harness):
    chat.press('nav:add')
    assert chat.state() == 'AddCard:card_nickname'

    chat.send('mono')
    assert chat.state() == 'AddCard:card_number'

    replies = chat.send('4242 4242 4242 4242')

    assert replies[-1].text == 'Card added.'
    assert chat.state() is None
    assert harness.rows() == [('42', '4242424242424242', 'mono')]


def test_add_card_with_19_digit_number(chat, harness):
    chat.send('/add')
    chat.send('union')
    replies = chat.send('6212 3456 7890 1234 569')

    assert replies[-1].text == 'Card added.'
    assert harness.rows() == [('42', '6212345678901234569', 'union')]


def test_add_card_rejects_invalid_number(chat, harness):
    chat.send('/add')
    chat.send('mono')
    replies = chat.send('1234')

    assert replies[-1].text == 'Credit card is invalid.'
    assert chat.state() == 'AddCard:card_number'
    assert harness.rows() == []


def test_add_card_rejects_duplicate_nickname(chat, harness):
    add_card(chat, '4242424242424242', 'mono')

    chat.send('/add')
    replies = chat.send('mono')

    # Rejected right away, before the number is asked for
    assert replies[-1].text.startswith('Nickname of your card should be unique')
    assert chat.state() == 'AddCard:card_nickname'
    assert len(harness.rows()) == 1


def test_nickname_taken_while_entering_number(chat, harness):
    chat.send('/add')
    chat.send('mono')
    harness.loop.run_until_complete(user_handlers.add_card(
        user_id=42, card_number='5555555555554444', card_nickname='mono'))

    replies = chat.send('4242424242424242')

    assert replies[-1].text.startswith('Nickname of your card should be unique')
    assert chat.state() == 'AddCard:card_nickname'
    assert harness.rows() == [('42', '5555555555554444', 'mono')]


def test_cancel_button_stops_adding(chat):
    chat.send('/add')
    chat.press('nav:main')

    assert chat.state() is None


def test_cards_list_shows_masked_numbers(chat):
    add_card(chat, '4242424242424242', 'mono')
    add_card(chat, '5555555555554444', 'privat')

    replies = chat.press('nav:cards')

    assert replies[0].buttons == [
        [('mono •••• 4242 · Visa', 'card:show:1')],
        [('privat •••• 4444 · MC', 'card:show:2')],
        [('⬅️ Back', 'nav:main')],
    ]


def test_empty_cards_list(chat):
    replies = chat.press('nav:cards')

    assert replies[0].text == 'There is no card.'


def test_card_view_shows_grouped_number_and_escapes_nickname(chat):
    add_card(chat, '4242424242424242', 'a&b')

    replies = chat.press('card:show:1')

    assert replies[0].data['parse_mode'] == 'html'
    assert '<code>4242 4242 4242 4242</code>' in replies[0].text
    assert 'a&amp;b' in replies[0].text


def test_missing_card_shows_alert(chat):
    replies = chat.press('card:show:999')

    assert replies[0].method == 'answerCallbackQuery'
    assert replies[0].text == 'Card not found.'


def test_other_users_card_is_not_accessible(harness):
    owner = harness.chat(user_id=1)
    stranger = harness.chat(user_id=2)
    add_card(owner, '4242424242424242', 'mono')

    assert stranger.press('card:show:1')[0].text == 'Card not found.'

    stranger.press('card:delete:1')
    stranger.press('card:edit:1')
    stranger.send('5555555555554444')
    stranger.press('card:rename:1')
    stranger.send('stolen')

    assert harness.rows() == [('1', '4242424242424242', 'mono')]


def test_edit_card_number(chat, harness):
    add_card(chat, '4242424242424242', 'mono')

    chat.press('card:edit:1')
    assert chat.send('1111')[-1].text == 'Credit card is invalid.'

    replies = chat.send('5555 5555 5555 4444')

    assert replies[-1].text == 'Information saved.'
    assert harness.rows() == [('42', '5555555555554444', 'mono')]


def test_edit_card_number_to_19_digits(chat, harness):
    add_card(chat, '4242424242424242', 'mono')

    chat.press('card:edit:1')
    replies = chat.send('6212345678901234569')

    assert replies[-1].text == 'Information saved.'
    assert harness.rows() == [('42', '6212345678901234569', 'mono')]


def test_edit_leave_previous_keeps_number(chat, harness):
    add_card(chat, '4242424242424242', 'mono')

    chat.press('card:edit:1')
    chat.press('card:show:1')

    assert chat.state() is None
    assert harness.rows() == [('42', '4242424242424242', 'mono')]


def test_rename_card(chat, harness):
    add_card(chat, '4242424242424242', 'mono')
    add_card(chat, '5555555555554444', 'privat')

    chat.press('card:rename:1')
    assert chat.send('two words')[-1].text.startswith('Choose another')
    assert chat.send('privat')[-1].text.startswith('Nickname of your card')

    replies = chat.send('black')

    assert 'black' in replies[-1].text
    assert chat.state() is None
    assert ('42', '4242424242424242', 'black') in harness.rows()


def test_delete_asks_for_confirmation(chat, harness):
    add_card(chat, '4242424242424242', 'mono')

    replies = chat.press('card:confirm_delete:1')

    assert replies[0].text == 'Delete card "mono"?'
    assert replies[0].callbacks == ['card:delete:1', 'card:show:1']
    assert len(harness.rows()) == 1

    chat.press('card:delete:1')

    assert harness.rows() == []


def test_cards_limit(chat, harness, monkeypatch):
    monkeypatch.setattr(user_handlers, 'MAX_CARDS', 2)
    add_card(chat, '4242424242424242', 'a')
    add_card(chat, '5555555555554444', 'b')

    assert chat.send('/add')[-1].text.startswith('You can keep up to 2 cards')
    assert chat.press('nav:add')[0].text.startswith('You can keep up to 2')
    assert chat.state() is None


def test_cards_limit_is_checked_before_saving(chat, harness, monkeypatch):
    monkeypatch.setattr(user_handlers, 'MAX_CARDS', 1)

    chat.send('/add')
    chat.send('mono')
    # Another card gets saved while this one is still being added
    harness.loop.run_until_complete(user_handlers.add_card(
        user_id=42, card_number='5555555555554444', card_nickname='other'))

    replies = chat.send('4242424242424242')

    assert replies[-1].text.startswith('You can keep up to 1 cards')
    assert len(harness.rows()) == 1


def test_commands_interrupt_input(chat):
    chat.send('/add')
    chat.send('/cards')
    assert chat.state() is None

    chat.send('/add')
    chat.send('/cancel')
    assert chat.state() is None


def test_help_keeps_current_input(chat):
    chat.send('/add')
    replies = chat.send('/help')

    assert '/cards' in replies[-1].text
    assert chat.state() == 'AddCard:card_nickname'


def test_old_reply_keyboard_buttons_open_menu(chat):
    for text in ('SHOW CARDS', 'ADD CARD', 'CANCEL'):
        replies = [r for r in chat.send(text) if r.method != 'deleteMessage']

        assert replies[0].markup == {'remove_keyboard': True}
        assert replies[1].callbacks == ['nav:cards', 'nav:add', 'nav:about']


def test_ukrainian_user_gets_ukrainian_texts(harness):
    chat = harness.chat(language_code='uk')

    replies = chat.send('/start')

    assert replies[2].text == 'Оберіть дію:'
    assert replies[2].buttons[0][0][0] == '💳 Мої картки'


def test_errors_are_reported_to_user(chat, monkeypatch):
    async def broken(**kwargs):
        raise RuntimeError('db is down')

    monkeypatch.setattr(user_handlers, 'get_cards', broken)

    replies = chat.press('nav:cards')

    assert replies[-1].method == 'answerCallbackQuery'
    assert replies[-1].text == 'Something went wrong. Please try again.'


def luhn_number(n: int) -> str:
    """A valid 16-digit Visa number that differs for each n."""
    digits = f'400000{n:09d}'
    total = 0
    for i, d in enumerate(reversed(digits)):
        d = int(d)
        if i % 2 == 0:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d

    return digits + str((10 - total % 10) % 10)


def add_cards(chat, count: int) -> None:
    for n in range(1, count + 1):
        add_card(chat, luhn_number(n), f'card{n}')


def card_buttons(reply) -> list:
    return [data for data in reply.callbacks if data.startswith('card:')]


def test_five_cards_fit_on_one_page(chat):
    add_cards(chat, 5)

    reply = chat.press('nav:cards')[0]

    assert reply.text == 'Choose your card:'
    assert len(card_buttons(reply)) == 5
    assert not any(data.startswith('cards:') for data in reply.callbacks)


def test_cards_are_split_into_pages(chat):
    add_cards(chat, 12)

    first = chat.press('nav:cards')[0]
    assert first.text == 'Choose your card (1/3):'
    assert card_buttons(first) == [f'card:show:{n}' for n in range(1, 6)]
    assert first.buttons[-2] == [('Next ➡️', 'cards:1')]

    middle = chat.press('cards:1')[0]
    assert middle.text == 'Choose your card (2/3):'
    assert card_buttons(middle) == [f'card:show:{n}' for n in range(6, 11)]
    assert middle.buttons[-2] == [('⬅️ Previous', 'cards:0'),
                                  ('Next ➡️', 'cards:2')]

    last = chat.press('cards:2')[0]
    assert last.text == 'Choose your card (3/3):'
    assert card_buttons(last) == ['card:show:11', 'card:show:12']
    assert last.buttons[-2] == [('⬅️ Previous', 'cards:1')]
    assert last.buttons[-1] == [('⬅️ Back', 'nav:main')]


def test_back_from_card_returns_to_its_page(chat):
    add_cards(chat, 12)

    reply = chat.press('card:show:7')[0]

    assert ('⬅️ Back', 'cards:1') in reply.buttons[-1]


def test_page_out_of_range_shows_last_page(chat):
    add_cards(chat, 6)
    chat.press('card:delete:6')

    reply = chat.press('cards:1')[0]

    assert reply.text == 'Choose your card:'
    assert card_buttons(reply) == [f'card:show:{n}' for n in range(1, 6)]


def test_pages_show_only_own_cards(harness):
    owner = harness.chat(user_id=1)
    other = harness.chat(user_id=2)
    add_cards(owner, 6)
    add_card(other, luhn_number(99), 'mine')

    reply = other.press('nav:cards')[0]

    assert reply.text == 'Choose your card:'
    assert card_buttons(reply) == ['card:show:7']


def test_ukrainian_page_buttons(harness):
    chat = harness.chat(language_code='uk')
    add_cards(chat, 6)

    reply = chat.press('nav:cards')[0]

    assert reply.text == 'Оберіть картку (1/2):'
    assert reply.buttons[-2] == [('Далі ➡️', 'cards:1')]


def state_data(chat) -> dict:
    return chat.harness.loop.run_until_complete(
        chat.harness.dp.current_state(chat=chat.user['id'],
                                      user=chat.user['id']).get_data())


def test_card_number_is_never_kept_in_state(chat):
    chat.send('/add')
    chat.send('mono')
    chat.send('4242 4242 4242 4241')     # invalid, asked again
    assert '4242' not in str(state_data(chat))

    chat.send('4242 4242 4242 4242')
    assert state_data(chat) == {}

    chat.press('card:edit:1')
    chat.send('1111')                    # invalid, asked again
    assert set(state_data(chat)) == {'card_id', 'prompt_id'}


MIR_NUMBER = '2200 0000 0000 0004'


def test_mir_number_is_otherwise_valid():
    from bot.handlers.service import validate_card_number

    assert validate_card_number(MIR_NUMBER)


def test_mir_card_cannot_be_added(chat, harness):
    chat.send('/add')
    chat.send('mono')

    replies = chat.send(MIR_NUMBER)

    assert replies[0].method == 'deleteMessage'
    assert replies[-1].text == 'Mir cards are not supported.'
    assert chat.state() == 'AddCard:card_number'
    assert harness.rows() == []

    chat.send('4242424242424242')
    assert harness.rows() == [('42', '4242424242424242', 'mono')]


def test_card_number_cannot_be_changed_to_mir(chat, harness):
    add_card(chat, '4242424242424242', 'mono')
    chat.press('card:edit:1')

    replies = chat.send(MIR_NUMBER)

    assert replies[-1].text == 'Mir cards are not supported.'
    assert chat.state() == 'ShowCard:edit_card_number'
    assert harness.rows() == [('42', '4242424242424242', 'mono')]


def test_mir_rejection_in_ukrainian(harness):
    chat = harness.chat(language_code='uk')
    chat.send('/add')
    chat.send('mono')

    assert chat.send(MIR_NUMBER)[-1].text == 'Картки «Мир» не підтримуються.'


def test_too_long_nickname_is_rejected_when_adding(chat, harness):
    chat.send('/add')

    replies = chat.send('x' * 33)

    assert replies[-1].text == 'Nickname must be at most 32 characters long:'
    assert chat.state() == 'AddCard:card_nickname'

    chat.send('x' * 32)
    chat.send('4242424242424242')
    assert harness.rows() == [('42', '4242424242424242', 'x' * 32)]


def test_too_long_nickname_is_rejected_when_renaming(chat, harness):
    add_card(chat, '4242424242424242', 'mono')
    chat.press('card:rename:1')

    replies = chat.send('x' * 33)

    assert replies[-1].text == 'Nickname must be at most 32 characters long:'
    assert harness.rows() == [('42', '4242424242424242', 'mono')]


def test_longest_nickname_fits_in_card_view(chat):
    add_card(chat, '378282246310005', 'ж' * 32)

    view = chat.press('card:show:1')[0]

    assert len(view.text) < 4096
    assert len(chat.press('card:confirm_delete:1')[0].text) < 4096


def test_too_long_nickname_in_ukrainian(harness):
    chat = harness.chat(language_code='uk')
    chat.send('/add')

    assert chat.send('x' * 33)[-1].text == \
        'Назва має бути не довшою за 32 символи:'


@pytest.mark.parametrize('first, second', [('mono', 'MONO'),
                                           ('Mono', 'mono'),
                                           ('Моно', 'моно')])
def test_nickname_in_other_case_is_taken(chat, harness, first, second):
    add_card(chat, '4242424242424242', first)

    chat.send('/add')
    replies = chat.send(second)

    assert replies[-1].text.startswith('Nickname of your card should be unique')
    assert chat.state() == 'AddCard:card_nickname'
    assert len(harness.rows()) == 1


def test_rename_to_other_card_in_other_case_is_rejected(chat, harness):
    add_card(chat, '4242424242424242', 'mono')
    add_card(chat, '5555555555554444', 'privat')
    chat.press('card:rename:2')

    replies = chat.send('MONO')

    assert replies[-1].text.startswith('Nickname of your card should be unique')
    assert ('42', '5555555555554444', 'privat') in harness.rows()


def test_card_can_be_renamed_to_its_own_nickname_in_other_case(chat,
                                                                harness):
    add_card(chat, '4242424242424242', 'mono')
    chat.press('card:rename:1')

    chat.send('Mono')

    # The case the user typed is kept
    assert harness.rows() == [('42', '4242424242424242', 'Mono')]


def test_other_users_may_use_the_same_nickname_in_any_case(harness):
    first = harness.chat(user_id=1)
    second = harness.chat(user_id=2)
    add_card(first, '4242424242424242', 'mono')

    add_card(second, '5555555555554444', 'MONO')

    assert ('2', '5555555555554444', 'MONO') in harness.rows()


@pytest.mark.parametrize('command', ['/start', '/cards', '/add', '/help',
                                     '/cancel'])
def test_commands_are_deleted(chat, command):
    replies = chat.send(command)

    assert replies[0].method == 'deleteMessage'
    assert replies[0].data['message_id'] == chat.last_message_id
