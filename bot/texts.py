from aiogram.types import User

TEXTS = {
    'en': {
        'welcome': 'Welcome to card bot!',
        'choose_action': 'Choose an action:',
        'cancelled': 'Cancelled.',
        'enter_card_number': 'Enter card number:',
        'card_invalid': 'Credit card is invalid.',
        'card_not_supported': 'Mir cards are not supported.',
        'enter_nickname': 'Enter card nickname (without spaces):',
        'choose_another_nickname': 'Choose another nickname '
                                   '(without spaces):',
        'nickname_too_long': 'Nickname must be at most {limit} '
                             'characters long:',
        'nickname_not_unique': 'Nickname of your card should be unique.\n'
                               'Choose another nickname (without spaces):',
        'card_added': 'Card added.',
        'cards_limit': 'You can keep up to {limit} cards.\n'
                       'Delete one to add a new one.',
        'no_cards': 'There is no card.',
        'choose_card': 'Choose your card:',
        'choose_card_page': 'Choose your card ({page}/{pages}):',
        'card_not_found': 'Card not found.',
        'card_view': '<b>Nickname:</b> {nickname}\n\n'
                     '⬇️<b>Tap to copy</b>⬇️\n\n'
                     '<code>{number}</code>\n\n'
                     '⬆️<b>Tap to copy</b>⬆️',
        'card_hidden': '<b>Nickname:</b> {nickname}\n\n'
                       '🔒 Number hidden',
        'enter_new_card_number': 'Enter new card number:',
        'enter_new_nickname': 'Enter new card nickname (without spaces):',
        'info_saved': 'Information saved.',
        'delete_confirm': 'Delete card "{nickname}"?',
        'card_deleted': 'Card deleted.',
        'error': 'Something went wrong. Please try again.',
        'alert': '⚠️ Error in the bot\n{error}\nAction: {action}\n'
                 'Date/time: {time}\nDetails: fly logs -a card-bot',
        'alert_repeats': 'Happened {count} more times since the last alert',
        'startup_alert': '✅ Bot started\nDate/time: {time}',
        'stats': '📊 Statistics\nUsers with cards: {users}\nCards: {cards}\n'
                 'Most per user: {most} of {limit}\n'
                 'Unfinished dialogs: {dialogs}\nRunning since: {started}',
        'alert_action_message': 'message',
        'alert_action_button': 'button press',
        'alert_action_other': 'other update',
        'not_understood': 'I did not understand that. Use the buttons:',
        'number_outside_dialog': 'Your message with a card number was '
                                 'deleted. To save a card, tap '
                                 '"➕ Add card".',
        'send_nickname_as_text': 'Send the nickname as text:',
        'send_number_as_text': 'Send the card number as text:',
        'private_only': 'I only work in private messages. '
                        'Open a chat with me to manage your cards.',
        'help': 'Card bot keeps your card numbers so you can copy them '
                'quickly.\n\n'
                '/cards - your cards: tap one to see and copy the number, '
                'change or delete it\n'
                '/add - add a card\n'
                '/cancel - cancel the current action\n'
                '/help - this help',

        'cmd_cards': 'My cards',
        'cmd_add': 'Add card',
        'cmd_cancel': 'Cancel current action',
        'cmd_help': 'Help',

        'btn_show_cards': '💳 Show cards',
        'btn_add_card': '➕ Add card',
        'btn_cancel': '✖️ Cancel',
        'btn_back': '⬅️ Back',
        'btn_prev_page': '⬅️ Previous',
        'btn_next_page': 'Next ➡️',
        'btn_show_number': '👁 Show number',
        'btn_share': '📤 Share',
        'btn_edit_number': '🔢 Change number',
        'btn_edit_nickname': '🏷 Change nickname',
        'btn_delete': '❌ Delete',
        'btn_leave_previous': '↩️ Leave previous',
        'btn_leave_previous_nickname': '↩️ Leave previous',
        'btn_yes_delete': '✅ Yes, delete',
        'btn_no': '↩️ No',
        'btn_read': '✅ Read',
        'inline_add_card': 'Add a card in the bot',
    },
    'uk': {
        'welcome': 'Вітаю в card bot!',
        'choose_action': 'Оберіть дію:',
        'cancelled': 'Скасовано.',
        'enter_card_number': 'Введіть номер картки:',
        'card_invalid': 'Недійсний номер картки.',
        'card_not_supported': 'Картки «Мир» не підтримуються.',
        'enter_nickname': 'Введіть назву картки (без пробілів):',
        'choose_another_nickname': 'Оберіть іншу назву (без пробілів):',
        'nickname_too_long': 'Назва має бути не довшою за {limit} '
                             'символи:',
        'nickname_not_unique': 'Назва картки має бути унікальною.\n'
                               'Оберіть іншу назву (без пробілів):',
        'card_added': 'Картку додано.',
        'cards_limit': 'Можна зберегти не більше {limit} карток.\n'
                       'Видаліть одну, щоб додати нову.',
        'no_cards': 'Карток немає.',
        'choose_card': 'Оберіть картку:',
        'choose_card_page': 'Оберіть картку ({page}/{pages}):',
        'card_not_found': 'Картку не знайдено.',
        'card_view': '<b>Назва:</b> {nickname}\n\n'
                     '⬇️<b>Натисніть, щоб скопіювати</b>⬇️\n\n'
                     '<code>{number}</code>\n\n'
                     '⬆️<b>Натисніть, щоб скопіювати</b>⬆️',
        'card_hidden': '<b>Назва:</b> {nickname}\n\n'
                       '🔒 Номер приховано',
        'enter_new_card_number': 'Введіть новий номер картки:',
        'enter_new_nickname': 'Введіть нову назву картки (без пробілів):',
        'info_saved': 'Збережено.',
        'delete_confirm': 'Видалити картку «{nickname}»?',
        'card_deleted': 'Картку видалено.',
        'error': 'Щось пішло не так. Спробуйте ще раз.',
        'alert': '⚠️ Помилка в боті\n{error}\nДія: {action}\n'
                 'Дата/час: {time}\nПодробиці: fly logs -a card-bot',
        'alert_repeats': 'Повторилася ще {count} раз(ів) з попереднього '
                         'сповіщення',
        'startup_alert': '✅ Бот запущено\nДата/час: {time}',
        'stats': '📊 Статистика\nКористувачів з картками: {users}\n'
                 'Карток: {cards}\nНайбільше в одного: {most} з {limit}\n'
                 'Незавершених діалогів: {dialogs}\nБот працює з: {started}',
        'alert_action_message': 'повідомлення',
        'alert_action_button': 'натискання кнопки',
        'alert_action_other': 'інше оновлення',
        'not_understood': 'Не зрозумів. Скористайтеся кнопками:',
        'number_outside_dialog': 'Повідомлення з номером картки видалено. '
                                 'Щоб зберегти картку, натисніть '
                                 '«➕ Додати картку».',
        'send_nickname_as_text': 'Надішліть назву текстом:',
        'send_number_as_text': 'Надішліть номер картки текстом:',
        'private_only': 'Я працюю лише в особистих повідомленнях. '
                        'Відкрийте чат зі мною, щоб керувати картками.',
        'help': 'Card bot зберігає номери ваших карток, щоб їх можна було '
                'швидко скопіювати.\n\n'
                '/cards - ваші картки: натисніть на картку, щоб побачити й '
                'скопіювати номер, змінити або видалити її\n'
                '/add - додати картку\n'
                '/cancel - скасувати поточну дію\n'
                '/help - ця довідка',

        'cmd_cards': 'Мої картки',
        'cmd_add': 'Додати картку',
        'cmd_cancel': 'Скасувати дію',
        'cmd_help': 'Довідка',

        'btn_show_cards': '💳 Мої картки',
        'btn_add_card': '➕ Додати картку',
        'btn_cancel': '✖️ Скасувати',
        'btn_back': '⬅️ Назад',
        'btn_prev_page': '⬅️ Попередні',
        'btn_next_page': 'Далі ➡️',
        'btn_show_number': '👁 Показати номер',
        'btn_share': '📤 Поділитися',
        'btn_edit_number': '🔢 Змінити номер',
        'btn_edit_nickname': '🏷 Змінити назву',
        'btn_delete': '❌ Видалити',
        'btn_leave_previous': '↩️ Залишити попередній',
        'btn_leave_previous_nickname': '↩️ Залишити попередню',
        'btn_yes_delete': '✅ Так, видалити',
        'btn_no': '↩️ Ні',
        'btn_read': '✅ Прочитано',
        'inline_add_card': 'Додати картку в боті',
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
