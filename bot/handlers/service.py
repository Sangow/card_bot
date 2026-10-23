def validate_card_number(card_number: str) -> bool:
    cn_no_spaces = card_number.replace(' ', '')

    if len(cn_no_spaces) < 13 or len(cn_no_spaces) > 16 or \
            not cn_no_spaces.isdigit():
        return False

    r = [int(ch) for ch in str(cn_no_spaces)][::-1]

    return (sum(r[0::2]) + sum(
        sum(divmod(d * 2, 10)) for d in r[1::2])) % 10 == 0


# Longer nicknames make the card view exceed Telegram's message size
MAX_NICKNAME_LENGTH = 32


def nickname_too_long(card_nickname: str) -> bool:
    return len(card_nickname.strip()) > MAX_NICKNAME_LENGTH


def validate_card_nickname(card_nickname: str) -> bool:
    if nickname_too_long(card_nickname):
        return False

    nick = card_nickname.split()

    if len(nick) != 1:
        return False

    c_n = nick[0]

    return isinstance(c_n, str) and c_n.count('<') == 0 and c_n.count('>') == 0


# Checked in order, so narrower prefixes go before wider ones
CARD_BRANDS = (
    ('ПРОСТІР', ('9804',)),
    ('Amex', ('34', '37')),
    ('JCB', tuple(str(p) for p in range(3528, 3590))),
    ('Maestro', ('50', '56', '57', '58', '6304', '6759', '676')),
    ('Discover', ('6011', '65')),
    ('UnionPay', ('62',)),
    ('Visa', ('4',)),
    ('MC', ('51', '52', '53', '54', '55')
     + tuple(str(p) for p in range(2221, 2721))),
)


def card_brand(card_number: str) -> str | None:
    for brand, prefixes in CARD_BRANDS:
        if card_number.startswith(prefixes):
            return brand

    return None


def card_label(card_nickname: str, card_number: str) -> str:
    label = f'{card_nickname} •••• {card_number[-4:]}'
    brand = card_brand(card_number)

    return f'{label} · {brand}' if brand else label


def format_card_number(card_number: str) -> str:
    # Amex is printed as 4-6-5, everything else in groups of four
    if card_brand(card_number) == 'Amex':
        return ' '.join((card_number[:4], card_number[4:10],
                         card_number[10:]))

    return ' '.join(card_number[i:i + 4]
                    for i in range(0, len(card_number), 4))


# Russian Mir payment system
MIR_PREFIXES = ('2200', '2201', '2202', '2203', '2204')


def is_mir_card(card_number: str) -> bool:
    return card_number.replace(' ', '').startswith(MIR_PREFIXES)
