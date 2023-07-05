def luhn_check_card(card_number: str) -> bool:
    if card_number.isdigit():
        r = [int(ch) for ch in str(card_number)][::-1]
        return (sum(r[0::2]) + sum(sum(divmod(d * 2, 10)) for d in r[1::2])) % 10 == 0
    return False
