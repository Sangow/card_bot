import re


# Card numbers are 13 to 19 digits long (ISO/IEC 7812); some Maestro,
# UnionPay and Visa cards have more than 16
MIN_CARD_NUMBER_LENGTH = 13
MAX_CARD_NUMBER_LENGTH = 19


def normalize_card_number(card_number: str) -> str:
    # Copied numbers come with dashes or non-breaking spaces as well as
    # plain spaces between the digit groups
    return re.sub(r'[\s-]', '', card_number)


def validate_card_number(card_number: str) -> bool:
    cn_no_spaces = normalize_card_number(card_number)

    if len(cn_no_spaces) < MIN_CARD_NUMBER_LENGTH or \
            len(cn_no_spaces) > MAX_CARD_NUMBER_LENGTH or \
            not cn_no_spaces.isdigit():
        return False

    r = [int(ch) for ch in str(cn_no_spaces)][::-1]

    return (sum(r[0::2]) + sum(
        sum(divmod(d * 2, 10)) for d in r[1::2])) % 10 == 0


# Longer nicknames make the card view exceed Telegram's message size
MAX_NICKNAME_LENGTH = 32


def normalize_card_nickname(card_nickname: str) -> str:
    # Words are kept apart by single spaces, so "mono  black" and
    # "mono black" are one nickname
    return re.sub(r' +', ' ', card_nickname.strip())


def nickname_too_long(card_nickname: str) -> bool:
    return len(normalize_card_nickname(card_nickname)) > MAX_NICKNAME_LENGTH


def nickname_looks_like_card_number(card_nickname: str) -> bool:
    # Nicknames are stored and shown unencrypted, so a card number must not
    # end up in one
    return looks_like_card_number(normalize_card_nickname(card_nickname))


def validate_card_nickname(card_nickname: str) -> bool:
    nick = normalize_card_nickname(card_nickname)

    if not nick or nickname_too_long(nick):
        return False

    # One line: spaces between words, but no line breaks or tabs
    if any(ch.isspace() and ch != ' ' for ch in nick):
        return False

    if '<' in nick or '>' in nick:
        return False

    return not nickname_looks_like_card_number(nick)


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


# Icon file under assets/card-icons for each brand card_brand() returns
BRAND_ICONS = {
    'Visa': 'visa', 'MC': 'mc', 'ПРОСТІР': 'prostir', 'Amex': 'amex',
    'Maestro': 'maestro', 'UnionPay': 'unionpay', 'JCB': 'jcb',
    'Discover': 'discover',
}


def card_icon(card_number: str) -> str:
    return BRAND_ICONS.get(card_brand(card_number), 'unknown')


def card_label(card_nickname: str, card_number: str,
               favorite: bool = False) -> str:
    label = f'{card_nickname} •••• {card_number[-4:]}'
    if favorite:
        label = f'⭐ {label}'
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
    return normalize_card_number(card_number).startswith(MIR_PREFIXES)


def looks_like_card_number(text: str) -> bool:
    # Broader than validate_card_number on purpose: a number with a typo
    # is just as private
    if not re.fullmatch(r'[\d\s-]+', text):
        return False

    return 12 <= sum(ch.isdigit() for ch in text) <= 19
