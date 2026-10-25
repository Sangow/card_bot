from conftest import add_card

TAKEN = 'This number is already saved as «mono».\nEnter another card number:'


def test_number_already_saved_is_not_added_again(chat, harness):
    add_card(chat, '4242424242424242', 'mono')

    replies = add_card(chat, '4242 4242 4242 4242', 'black')

    assert replies[0].method == 'deleteMessage'
    assert replies[-1].text == TAKEN
    assert harness.rows() == [('42', '4242424242424242', 'mono')]


def test_user_can_enter_another_number_after_duplicate(chat, harness):
    add_card(chat, '4242424242424242', 'mono')
    add_card(chat, '4242424242424242', 'black')

    assert chat.state() == 'AddCard:card_number'

    replies = chat.send('5555555555554444')

    assert replies[-1].text == 'Card added.'
    assert harness.rows() == [('42', '4242424242424242', 'mono'),
                              ('42', '5555555555554444', 'black')]


def test_duplicate_number_offers_to_open_the_card_or_cancel(chat):
    add_card(chat, '4242424242424242', 'mono')

    replies = add_card(chat, '4242-4242-4242-4242', 'black')

    assert replies[-1].buttons == [[('💳 Open «mono»', 'card:show:1')],
                                   [('✖️ Cancel', 'nav:main')]]


def test_open_button_shows_the_saved_card(chat):
    add_card(chat, '4242424242424242', 'mono')
    add_card(chat, '4242424242424242', 'black')

    replies = chat.press('card:show:1')

    assert '4242 4242 4242 4242' in replies[0].text
    assert chat.state() is None


def test_other_users_may_save_the_same_number(harness):
    first = harness.chat(user_id=1)
    second = harness.chat(user_id=2)
    add_card(first, '4242424242424242', 'mono')

    replies = add_card(second, '4242424242424242', 'mono')

    assert replies[-1].text == 'Card added.'


def test_number_of_another_card_cannot_be_set_by_editing(chat, harness):
    add_card(chat, '4242424242424242', 'mono')
    add_card(chat, '5555555555554444', 'privat')

    chat.press('card:edit:2')
    replies = chat.send('4242 4242 4242 4242')

    assert replies[0].method == 'deleteMessage'
    assert replies[-1].text == TAKEN
    assert replies[-1].buttons == [
        [('💳 Open «mono»', 'card:show:1')],
        [('↩️ Leave previous', 'card:show:2')],
    ]
    assert chat.state() == 'ShowCard:edit_card_number'
    assert ('42', '5555555555554444', 'privat') in harness.rows()


def test_card_number_can_be_entered_again_when_editing(chat, harness):
    add_card(chat, '4242424242424242', 'mono')

    chat.press('card:edit:1')
    replies = chat.send('4242424242424242')

    assert replies[-1].text == 'Information saved.'
    assert harness.rows() == [('42', '4242424242424242', 'mono')]


def test_deleted_card_number_can_be_added_again(chat, harness):
    add_card(chat, '4242424242424242', 'mono')
    chat.press('card:delete:1')

    replies = add_card(chat, '4242424242424242', 'black')

    assert replies[-1].text == 'Card added.'


def test_duplicate_number_in_ukrainian(harness):
    chat = harness.chat(language_code='uk')
    add_card(chat, '4242424242424242', 'mono')

    replies = add_card(chat, '4242424242424242', 'black')

    assert replies[-1].text == ('Цей номер уже збережено як «mono».\n'
                                'Введіть інший номер картки:')
    assert replies[-1].buttons[0] == [('💳 Відкрити «mono»', 'card:show:1')]
