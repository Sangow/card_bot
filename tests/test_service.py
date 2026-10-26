import pytest

from bot.handlers.service import validate_card_number, \
    validate_card_nickname, card_brand, card_label, format_card_number, \
    normalize_card_number, is_mir_card


@pytest.mark.parametrize('card_number', [
    '4242424242424242',
    '4242 4242 4242 4242',
    '5555555555554444',
    '378282246310005',
    '4222222222222',
    '67596498264384533',    # 17 digits
    '501800000000000009',   # 18 digits
    '6212345678901234569',  # 19 digits
    '6212 3456 7890 1234 569',
    '4242-4242-4242-4242',
    '4242\u00a04242\u00a04242\u00a04242',  # non-breaking spaces
    '4242\u202f4242\u202f4242\u202f4242',  # narrow non-breaking spaces
    ' 4242 4242 4242 4242\n',
])
def test_valid_card_numbers(card_number):
    assert validate_card_number(card_number)


@pytest.mark.parametrize('card_number', [
    '4242424242424241',     # wrong checksum
    '424242424242',         # too short
    '42424242424242424242',  # too long
    '6212345678901234568',  # 19 digits, wrong checksum
    '4242abcd42424242',     # letters
    '4242.4242.4242.4242',  # dots are not separators
    '4242-4242-4242-4241',  # wrong checksum with dashes
    '',
])
def test_invalid_card_numbers(card_number):
    assert not validate_card_number(card_number)


@pytest.mark.parametrize('card_number', [
    '4242424242424242',
    '4242 4242 4242 4242',
    '4242-4242-4242-4242',
    '4242 - 4242 - 4242 - 4242',
    '4242\u00a04242\u202f4242\t4242',
])
def test_normalize_card_number(card_number):
    assert normalize_card_number(card_number) == '4242424242424242'


@pytest.mark.parametrize('card_number', [
    '2200000000000004',
    '2200 0000 0000 0004',
    '2200-0000-0000-0004',
    '2200\u00a00000\u00a00000\u00a00004',
])
def test_mir_card_with_any_separators(card_number):
    assert is_mir_card(card_number)


@pytest.mark.parametrize('card_nickname', ['mono', 'privat&co', 'Моно'])
def test_valid_nicknames(card_nickname):
    assert validate_card_nickname(card_nickname)


@pytest.mark.parametrize('card_nickname',
                         ['two\nlines', '<b>', 'a>b', '', ' '])
def test_invalid_nicknames(card_nickname):
    assert not validate_card_nickname(card_nickname)


@pytest.mark.parametrize('card_number, brand', [
    ('4242424242424242', 'Visa'),
    ('5555555555554444', 'MC'),
    ('2223003122003222', 'MC'),
    ('378282246310005', 'Amex'),
    ('6011111111111117', 'Discover'),
    ('3530111333300000', 'JCB'),
    ('6200000000000005', 'UnionPay'),
    ('5018000000000009', 'Maestro'),
    ('9804000000000000', 'ПРОСТІР'),
    ('1234567812345670', None),
])
def test_card_brand(card_number, brand):
    assert card_brand(card_number) == brand


def test_card_label_with_brand():
    assert card_label('mono', '4242424242424242') == 'mono •••• 4242 · Visa'


def test_card_label_without_brand():
    assert card_label('mono', '1234567812345670') == 'mono •••• 5670'


@pytest.mark.parametrize('card_number, formatted', [
    ('4242424242424242', '4242 4242 4242 4242'),
    ('378282246310005', '3782 822463 10005'),
    ('4222222222222', '4222 2222 2222 2'),
    ('6212345678901234569', '6212 3456 7890 1234 569'),
])
def test_format_card_number(card_number, formatted):
    assert format_card_number(card_number) == formatted


def test_nickname_length_limit():
    from bot.handlers.service import MAX_NICKNAME_LENGTH

    assert validate_card_nickname('x' * MAX_NICKNAME_LENGTH)
    assert not validate_card_nickname('x' * (MAX_NICKNAME_LENGTH + 1))
