import json

from conftest import add_card


def inline(harness, chat, text: str = '') -> tuple:
    """Sends an inline query; returns the answer and its results."""
    replies = harness.process({'inline_query': {
        'id': str(next(harness.ids)), 'from': chat.user,
        'query': text, 'offset': '',
    }})
    answer, = [r for r in replies if r.method == 'answerInlineQuery']
    results = answer.data['results']
    if isinstance(results, str):
        results = json.loads(results)

    return answer.data, results


def titles(results) -> list:
    return [r['title'] for r in results]


def test_lists_own_cards_and_sends_only_the_number(harness, chat):
    add_card(chat, '4242424242424242', 'mono')
    add_card(chat, '378282246310005', 'privat')

    _, results = inline(harness, chat)

    assert titles(results) == ['mono •••• 4242 · Visa',
                               'privat •••• 0005 · Amex']
    messages = [r['input_message_content'] for r in results]
    assert [m['message_text'] for m in messages] == [
        '💳 <code>4242 4242 4242 4242</code>',
        '💳 <code>3782 822463 10005</code>',
    ]
    assert all(m['parse_mode'] == 'html' for m in messages)


def test_message_has_no_nickname(harness, chat):
    add_card(chat, '4242424242424242', 'зарплатна')

    _, results = inline(harness, chat)

    assert 'зарплатна' not in results[0]['input_message_content'][
        'message_text']


def test_results_are_personal_and_not_cached(harness, chat):
    add_card(chat, '4242424242424242', 'mono')

    answer, _ = inline(harness, chat)

    assert answer['cache_time'] == 0
    assert answer['is_personal'] is True


def test_other_users_cards_are_not_listed(harness):
    me = harness.chat(user_id=1)
    other = harness.chat(user_id=2)
    add_card(me, '4242424242424242', 'mono')
    add_card(other, '5555555555554444', 'friend')

    _, results = inline(harness, me)

    assert titles(results) == ['mono •••• 4242 · Visa']


def test_query_filters_by_nickname_ignoring_case(harness, chat):
    add_card(chat, '4242424242424242', 'mono')
    add_card(chat, '5555555555554444', 'privat')

    _, results = inline(harness, chat, 'MO')

    assert titles(results) == ['mono •••• 4242 · Visa']


def test_no_cards_offers_to_open_the_bot(harness):
    chat = harness.chat(language_code='uk')

    answer, results = inline(harness, chat)

    assert results == []
    assert answer['switch_pm_text'] == 'Додати картку в боті'
    assert answer['switch_pm_parameter'] == 'add'


def test_works_in_the_middle_of_a_dialog(harness, chat):
    add_card(chat, '4242424242424242', 'mono')
    chat.send('/add')

    _, results = inline(harness, chat)

    assert len(results) == 1
    assert chat.state() == 'AddCard:card_nickname'


def test_exact_nickname_lists_only_that_card(harness, chat):
    add_card(chat, '4242424242424242', 'mono')
    add_card(chat, '5555555555554444', 'mono_black')

    _, results = inline(harness, chat, 'Mono')

    assert titles(results) == ['mono •••• 4242 · Visa']


def test_part_of_nickname_still_lists_all_matches(harness, chat):
    add_card(chat, '4242424242424242', 'mono')
    add_card(chat, '5555555555554444', 'mono_black')

    _, results = inline(harness, chat, 'mon')

    assert titles(results) == ['mono •••• 4242 · Visa',
                               'mono_black •••• 4444 · MC']


def test_card_view_has_share_button_first(chat):
    add_card(chat, '4242424242424242', 'mono')

    view = chat.press('card:show:1')[0]

    assert view.buttons[0] == [('📤 Share', 'inline:mono')]


def test_share_button_follows_rename(chat):
    add_card(chat, '4242424242424242', 'mono')
    chat.press('card:rename:1')

    view = chat.send('black')[-1]

    assert view.buttons[0] == [('📤 Share', 'inline:black')]


def test_share_button_in_ukrainian(harness):
    chat = harness.chat(language_code='uk')
    add_card(chat, '4242424242424242', 'mono')

    view = chat.press('card:show:1')[0]

    assert view.buttons[0] == [('📤 Поділитися', 'inline:mono')]


def test_share_button_offers_just_that_card(harness, chat):
    add_card(chat, '4242424242424242', 'mono')
    add_card(chat, '5555555555554444', 'mono_black')
    share_query = chat.press('card:show:1')[0].buttons[0][0][1]

    _, results = inline(harness, chat, share_query.removeprefix('inline:'))

    assert titles(results) == ['mono •••• 4242 · Visa']
