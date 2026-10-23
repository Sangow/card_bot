from string import Formatter

import pytest
from aiogram.types import User

from bot.texts import TEXTS, get_lang


def placeholders(text: str) -> set:
    return {name for _, name, _, _ in Formatter().parse(text) if name}


def test_all_languages_have_same_keys():
    keys = TEXTS['en'].keys()

    for lang, texts in TEXTS.items():
        assert texts.keys() == keys, lang


def test_all_languages_have_same_placeholders():
    for key, text in TEXTS['en'].items():
        for lang, texts in TEXTS.items():
            assert placeholders(texts[key]) == placeholders(text), \
                f'{lang}.{key}'


@pytest.mark.parametrize('language_code, lang', [
    ('uk', 'uk'),
    ('ru', 'uk'),
    ('en', 'en'),
    ('pt-br', 'en'),
    ('de', 'en'),
    (None, 'en'),
])
def test_get_lang(language_code, lang):
    user = User(id=1, is_bot=False, first_name='u',
                language_code=language_code)

    assert get_lang(user) == lang
