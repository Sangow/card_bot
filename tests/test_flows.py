import bot.handlers.user_handlers as user_handlers
from conftest import add_card


def test_start_shows_menu_and_removes_old_keyboard(chat):
    replies = chat.send('/start')

    assert replies[0].markup == {'remove_keyboard': True}
    assert replies[1].callbacks == ['nav:cards', 'nav:add']


def test_add_card(chat, harness):
    chat.press('nav:add')
    assert chat.state() == 'AddCard:card_number'

    chat.send('4242 4242 4242 4242')
    assert chat.state() == 'AddCard:card_nickname'

    replies = chat.send('mono')

    assert replies[0].text == 'Card added.'
    assert chat.state() is None
    assert harness.rows() == [('42', '4242424242424242', 'mono')]


def test_add_card_rejects_invalid_number(chat, harness):
    chat.send('/add')
    replies = chat.send('1234')

    assert replies[0].text == 'Credit card is invalid.'
    assert chat.state() == 'AddCard:card_number'
    assert harness.rows() == []


def test_add_card_rejects_duplicate_nickname(chat, harness):
    add_card(chat, '4242424242424242', 'mono')

    replies = add_card(chat, '5555555555554444', 'mono')

    assert replies[0].text.startswith('Nickname of your card should be unique')
    assert chat.state() == 'AddCard:card_nickname'
    assert len(harness.rows()) == 1


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
    assert chat.send('1111')[0].text == 'Credit card is invalid.'

    replies = chat.send('5555 5555 5555 4444')

    assert replies[0].text == 'Information saved.'
    assert harness.rows() == [('42', '5555555555554444', 'mono')]


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
    assert chat.send('two words')[0].text.startswith('Choose another nickname')
    assert chat.send('privat')[0].text.startswith('Nickname of your card')

    replies = chat.send('black')

    assert 'black' in replies[0].text
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

    assert chat.send('/add')[0].text.startswith('You can keep up to 2 cards')
    assert chat.press('nav:add')[0].text.startswith('You can keep up to 2')
    assert chat.state() is None


def test_cards_limit_is_checked_before_saving(chat, harness, monkeypatch):
    monkeypatch.setattr(user_handlers, 'MAX_CARDS', 1)

    chat.send('/add')
    chat.send('4242424242424242')
    # Another card gets saved while this one is still being added
    harness.loop.run_until_complete(user_handlers.add_card(
        user_id=42, card_number='5555555555554444', card_nickname='other'))

    replies = chat.send('mono')

    assert replies[0].text.startswith('You can keep up to 1 cards')
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

    assert '/cards' in replies[0].text
    assert chat.state() == 'AddCard:card_number'


def test_old_reply_keyboard_buttons_open_menu(chat):
    for text in ('SHOW CARDS', 'ADD CARD', 'CANCEL'):
        replies = chat.send(text)

        assert replies[0].markup == {'remove_keyboard': True}
        assert replies[1].callbacks == ['nav:cards', 'nav:add']


def test_ukrainian_user_gets_ukrainian_texts(harness):
    chat = harness.chat(language_code='uk')

    replies = chat.send('/start')

    assert replies[1].text == 'Оберіть дію:'
    assert replies[1].buttons[0][0][0] == '💳 Мої картки'


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
