def validate_card_number(card_number: str) -> bool:
    if len(card_number) < 13 or len(card_number) > 16 or not card_number.isdigit():
        return False

    r = [int(ch) for ch in str(card_number)][::-1]

    return (sum(r[0::2]) + sum(sum(divmod(d * 2, 10)) for d in r[1::2])) % 10 == 0


def validate_card_nickname(card_nickname: list) -> bool:
    if len(card_nickname) != 1:
        return False

    c_n = card_nickname[0]

    return isinstance(c_n, str) and c_n.count('<') == 0 and c_n.count('>') == 0
