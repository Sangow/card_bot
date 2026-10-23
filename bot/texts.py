from aiogram.types import User

TEXTS = {
    'en': {
        'welcome': 'Welcome to card bot!',
        'choose_action': 'Choose an action:',
        'cancelled': 'Cancelled.',
        'enter_card_number': 'Enter card number:',
        'card_invalid': 'Credit card is invalid.',
        'enter_nickname': 'Enter card nickname (without spaces):',
        'choose_another_nickname': 'Choose another nickname '
                                   '(without spaces):',
        'nickname_not_unique': 'Nickname of your card should be unique.\n'
                               'Choose another nickname (without spaces):',
        'card_added': 'Card added.',
        'no_cards': 'There is no card.',
        'choose_card': 'Choose your card:',
        'card_not_found': 'Card not found.',
        'card_view': '<b>Nickname:</b> {nickname}\n\n'
                     '⬇️<b>Tap to copy</b>⬇️\n\n'
                     '<code>{number}</code>\n\n'
                     '⬆️<b>Tap to copy</b>⬆️',
        'enter_new_card_number': 'Enter new card number:',
        'info_saved': 'Information saved.',
        'delete_confirm': 'Delete card "{nickname}"?',
        'card_deleted': 'Card deleted.',
        'error': 'Something went wrong. Please try again.',

        'btn_show_cards': '💳 Show cards',
        'btn_add_card': '➕ Add card',
        'btn_cancel': '✖️ Cancel',
        'btn_back': '⬅️ Back',
        'btn_edit': '✏️ Edit',
        'btn_delete': '❌ Delete',
        'btn_leave_previous': '↩️ Leave previous',
        'btn_yes_delete': '✅ Yes, delete',
        'btn_no': '↩️ No',
    },
    'uk': {
        'welcome': 'Вітаю в card bot!',
        'choose_action': 'Оберіть дію:',
        'cancelled': 'Скасовано.',
        'enter_card_number': 'Введіть номер картки:',
        'card_invalid': 'Недійсний номер картки.',
        'enter_nickname': 'Введіть назву картки (без пробілів):',
        'choose_another_nickname': 'Оберіть іншу назву (без пробілів):',
        'nickname_not_unique': 'Назва картки має бути унікальною.\n'
                               'Оберіть іншу назву (без пробілів):',
        'card_added': 'Картку додано.',
        'no_cards': 'Карток немає.',
        'choose_card': 'Оберіть картку:',
        'card_not_found': 'Картку не знайдено.',
        'card_view': '<b>Назва:</b> {nickname}\n\n'
                     '⬇️<b>Натисніть, щоб скопіювати</b>⬇️\n\n'
                     '<code>{number}</code>\n\n'
                     '⬆️<b>Натисніть, щоб скопіювати</b>⬆️',
        'enter_new_card_number': 'Введіть новий номер картки:',
        'info_saved': 'Збережено.',
        'delete_confirm': 'Видалити картку «{nickname}»?',
        'card_deleted': 'Картку видалено.',
        'error': 'Щось пішло не так. Спробуйте ще раз.',

        'btn_show_cards': '💳 Мої картки',
        'btn_add_card': '➕ Додати картку',
        'btn_cancel': '✖️ Скасувати',
        'btn_back': '⬅️ Назад',
        'btn_edit': '✏️ Змінити',
        'btn_delete': '❌ Видалити',
        'btn_leave_previous': '↩️ Залишити попередній',
        'btn_yes_delete': '✅ Так, видалити',
        'btn_no': '↩️ Ні',
    },
}

DEFAULT_LANG = 'en'

# Languages without own texts that should get another language instead
LANG_ALIASES = {
    'ru': 'uk',
}


def get_lang(user: User) -> str:
    code = (user.language_code or '').split('-')[0]
    code = LANG_ALIASES.get(code, code)

    return code if code in TEXTS else DEFAULT_LANG


def t(lang: str, key: str, **kwargs) -> str:
    text = TEXTS[lang][key]

    return text.format(**kwargs) if kwargs else text
