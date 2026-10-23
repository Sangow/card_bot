import bot.sql.sq as sq
from conftest import add_card


def fsm_rows() -> list:
    return sq.cur.execute('SELECT chat, user, state, data FROM fsm').fetchall()


def test_adding_a_card_goes_on_after_restart(chat, harness):
    chat.press('nav:add')
    chat.send('mono')

    harness.restart()
    replies = chat.send('4242424242424242')

    shown = [r for r in replies if r.method != 'deleteMessage']
    assert [(r.method, r.message_id, r.text) for r in shown] == [
        ('editMessageText', 1, 'Card added.')]
    assert harness.rows() == [('42', '4242424242424242', 'mono')]


def test_changing_a_number_goes_on_after_restart(chat, harness):
    add_card(chat, '4242424242424242', 'mono')
    chat.press('card:edit:1')

    harness.restart()
    replies = chat.send('5555555555554444')

    assert replies[-1].text == 'Information saved.'
    assert replies[-1].message_id == 1
    assert harness.rows() == [('42', '5555555555554444', 'mono')]


def test_renaming_goes_on_after_restart(chat, harness):
    add_card(chat, '4242424242424242', 'mono')
    chat.press('card:rename:1')

    harness.restart()
    replies = chat.send('black')

    assert 'black' in replies[-1].text
    assert harness.rows() == [('42', '4242424242424242', 'black')]


def test_state_data_is_stored_encrypted(chat, harness, tmp_path):
    chat.send('/add')
    chat.send('secretnick')

    (_, _, state, data), = fsm_rows()

    assert state == 'AddCard:card_number'
    assert data.startswith('gAAAAA')
    with open(sq.DB_PATH, 'rb') as f:
        assert b'secretnick' not in f.read()


def test_finished_conversation_leaves_no_state(chat):
    add_card(chat, '4242424242424242', 'mono')
    assert fsm_rows() == []

    chat.send('/add')
    chat.press('nav:main')
    assert fsm_rows() == []

    chat.press('card:edit:1')
    chat.send('/cancel')
    assert fsm_rows() == []


def test_states_are_kept_per_user(harness):
    first = harness.chat(user_id=1)
    second = harness.chat(user_id=2)

    first.send('/add')
    second.send('/add')
    first.send('one')

    harness.restart()

    assert first.state() == 'AddCard:card_number'
    assert second.state() == 'AddCard:card_nickname'
