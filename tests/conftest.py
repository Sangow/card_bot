import asyncio
import itertools
import json

import pytest
from aiogram import Bot, Dispatcher, types
from cryptography.fernet import Fernet
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import bot.handlers.hiding as hiding
import bot.sql.sq as sq
from bot import prepare_all


class Chat:
    """Sends updates from one user and records what the bot answers."""

    def __init__(self, harness, user_id: int, language_code: str):
        self.harness = harness
        self.user = {'id': user_id, 'is_bot': False, 'first_name': 'u',
                     'language_code': language_code}

    def send(self, text: str) -> list:
        self.last_message_id = next(self.harness.ids)

        return self.harness.process({'message': {
            'message_id': self.last_message_id,
            'date': 0,
            'chat': {'id': self.user['id'], 'type': 'private'},
            'from': self.user,
            'text': text,
        }})

    def press(self, data: str) -> list:
        return self.harness.process({'callback_query': {
            'id': str(next(self.harness.ids)),
            'from': self.user,
            'chat_instance': 'test',
            'data': data,
            'message': {
                'message_id': 1,
                'date': 0,
                'chat': {'id': self.user['id'], 'type': 'private'},
                'from': {'id': 1, 'is_bot': True, 'first_name': 'bot'},
                'text': 'previous',
            },
        }})

    def state(self) -> str | None:
        return self.harness.loop.run_until_complete(
            self.harness.dp.current_state(chat=self.user['id'],
                                          user=self.user['id']).get_state()
        )


class Reply:
    """One Bot API call made by the bot."""

    def __init__(self, method: str, data: dict):
        self.method = method
        self.text = data.get('text', '')
        self.data = data
        # Id of the message this call sent, or of the one it edited
        self.message_id = data.get('message_id') or data.get('sent_id')

        markup = data.get('reply_markup')
        if isinstance(markup, str):
            markup = json.loads(markup)
        self.markup = markup or {}

    @property
    def buttons(self) -> list:
        """Inline buttons as (text, callback_data) pairs, row by row."""
        return [[(b['text'], b['callback_data']) for b in row]
                for row in self.markup.get('inline_keyboard', [])]

    @property
    def callbacks(self) -> list:
        return [data for row in self.buttons for _, data in row]


class Harness:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.ids = itertools.count(100)
        self.calls = []

        self.bot = Bot(token='123456:TEST')
        self.dp = Dispatcher(self.bot, storage=MemoryStorage())
        Bot.set_current(self.bot)
        Dispatcher.set_current(self.dp)

    def process(self, update: dict) -> list:
        update['update_id'] = next(self.ids)
        start = len(self.calls)
        # run_until_complete runs each update in its own task, like polling
        # does, so aiogram's per-update context does not leak between them
        self.loop.run_until_complete(
            self.dp.process_update(types.Update(**update)))

        return [Reply(method, data) for method, data in self.calls[start:]]

    def wait(self, seconds: float) -> list:
        """Lets timers run for a while and returns what the bot did."""
        start = len(self.calls)
        self.loop.run_until_complete(asyncio.sleep(seconds))

        return [Reply(method, data) for method, data in self.calls[start:]]

    def chat(self, user_id: int = 42, language_code: str = 'en') -> Chat:
        return Chat(self, user_id, language_code)

    def rows(self) -> list:
        """Cards as (user_id, decrypted number, nickname)."""
        return [(user_id, sq.decrypt(card_number), card_nickname)
                for user_id, card_number, card_nickname in self.raw_rows()]

    def raw_rows(self) -> list:
        """Cards exactly as they are stored in the database."""
        return sq.cur.execute(
            'SELECT user_id, card_number, card_nickname FROM cards ORDER BY id'
        ).fetchall()


@pytest.fixture
def harness(tmp_path, monkeypatch):
    monkeypatch.setattr(sq, 'DB_PATH', str(tmp_path / 'db.db'))
    monkeypatch.setattr(sq, 'CARD_KEY', Fernet.generate_key().decode())

    h = Harness()

    async def fake_request(self, method, data=None, *args, **kwargs):
        data = dict(data or {})
        h.calls.append((method, data))
        if method in ('sendMessage', 'editMessageText'):
            sent_id = data.get('message_id') or next(h.ids)
            if method == 'sendMessage':
                data['sent_id'] = sent_id
            return {'message_id': sent_id, 'date': 0,
                    'chat': {'id': data.get('chat_id', 1),
                             'type': 'private'},
                    'text': data.get('text', '')}
        return True

    monkeypatch.setattr(Bot, 'request', fake_request)

    h.loop.run_until_complete(prepare_all(h.dp))
    h.calls.clear()

    yield h

    for task, _ in hiding.pending.values():
        task.cancel()
    hiding.pending.clear()
    sq.db.close()
    h.loop.close()


@pytest.fixture
def chat(harness):
    return harness.chat()


def add_card(chat: Chat, card_number: str, card_nickname: str) -> list:
    chat.send('/add')
    chat.send(card_nickname)
    return chat.send(card_number)
