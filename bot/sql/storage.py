import json

from aiogram.dispatcher.storage import BaseStorage

from bot.sql import sq


class SQLiteStorage(BaseStorage):
    """Keeps conversation states in the database, so a conversation goes on
    after the bot restarts."""

    async def close(self) -> None:
        pass

    async def wait_closed(self) -> None:
        pass

    def address(self, chat, user) -> tuple:
        chat, user = self.check_address(chat=chat, user=user)

        return str(chat), str(user)

    def load(self, chat, user) -> tuple:
        row = sq.cur.execute(
            'SELECT state, data FROM fsm WHERE chat=(?) AND user=(?)',
            self.address(chat, user)
        ).fetchone()

        if row is None:
            return None, {}

        state, data = row

        return state, json.loads(sq.decrypt(data)) if data else {}

    def save(self, chat, user, state, data: dict) -> None:
        if state is None and not data:
            sq.cur.execute(
                'DELETE FROM fsm WHERE chat=(?) AND user=(?)',
                self.address(chat, user)
            )
        else:
            sq.cur.execute(
                'INSERT OR REPLACE INTO fsm VALUES (?, ?, ?, ?)',
                (*self.address(chat, user), state,
                 sq.encrypt(json.dumps(data)))
            )
        sq.db.commit()

    async def get_state(self, *, chat=None, user=None, default=None):
        state, _ = self.load(chat, user)

        return state if state is not None else self.resolve_state(default)

    async def get_data(self, *, chat=None, user=None, default=None) -> dict:
        _, data = self.load(chat, user)

        return data

    async def set_state(self, *, chat=None, user=None, state=None) -> None:
        _, data = self.load(chat, user)
        self.save(chat, user, self.resolve_state(state), data)

    async def set_data(self, *, chat=None, user=None, data=None) -> None:
        state, _ = self.load(chat, user)
        self.save(chat, user, state, dict(data or {}))

    async def update_data(self, *, chat=None, user=None, data=None,
                          **kwargs) -> None:
        state, stored = self.load(chat, user)
        stored.update(data or {}, **kwargs)
        self.save(chat, user, state, stored)
