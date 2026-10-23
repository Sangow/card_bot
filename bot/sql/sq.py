import logging
from sqlite3 import connect

from cryptography.fernet import Fernet, InvalidToken

from bot.config import CARD_KEY, DB_PATH

logger = logging.getLogger(__name__)

# 1: cards have their own id and encrypted card numbers
SCHEMA_VERSION = 1

# AUTOINCREMENT never reuses the id of a deleted card, so buttons left in
# old messages cannot open a card added later
CREATE_CARDS = (
    'CREATE TABLE {table} '
    '(id INTEGER PRIMARY KEY AUTOINCREMENT, '
    'user_id TEXT NOT NULL, '
    'card_number TEXT NOT NULL, '
    'card_nickname TEXT NOT NULL, '
    'CONSTRAINT user_id_card_nick UNIQUE (user_id, card_nickname))'
)


def encrypt(card_number: str) -> str:
    return cipher.encrypt(card_number.encode()).decode()


def decrypt(token: str) -> str:
    return cipher.decrypt(token.encode()).decode()


def migrate() -> None:
    version = cur.execute('PRAGMA user_version').fetchone()[0]

    if version >= SCHEMA_VERSION:
        return

    has_cards = cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='cards'"
    ).fetchone()

    # One explicit transaction, so a failed migration leaves the old table
    # as it was
    db.isolation_level = None
    try:
        cur.execute('BEGIN')

        if has_cards:
            rows = cur.execute(
                'SELECT rowid, user_id, card_number, card_nickname '
                'FROM cards '
                'ORDER BY rowid'
            ).fetchall()

            cur.execute(CREATE_CARDS.format(table='cards_new'))
            # Ids stay equal to the old rowids, so buttons in old messages
            # still point to the same cards
            cur.executemany(
                'INSERT INTO cards_new '
                '(id, user_id, card_number, card_nickname) '
                'VALUES (?, ?, ?, ?)',
                [(rowid, user_id, encrypt(card_number.replace(' ', '')),
                  card_nickname)
                 for rowid, user_id, card_number, card_nickname in rows]
            )
            cur.execute('DROP TABLE cards')
            cur.execute('ALTER TABLE cards_new RENAME TO cards')

            logger.info('Migrated %d cards to schema version %d',
                        len(rows), SCHEMA_VERSION)
        else:
            cur.execute(CREATE_CARDS.format(table='cards'))

        cur.execute(f'PRAGMA user_version = {SCHEMA_VERSION}')
        cur.execute('COMMIT')
    except BaseException:
        cur.execute('ROLLBACK')
        raise
    finally:
        db.isolation_level = ''


def check_key() -> None:
    row = cur.execute('SELECT card_number FROM cards LIMIT 1').fetchone()

    if row is None:
        return

    # With a wrong key new cards would be encrypted differently from the
    # existing ones, so refuse to start instead
    try:
        decrypt(row[0])
    except InvalidToken:
        raise SystemExit('CARD_KEY does not match the key the cards in the '
                         'database were encrypted with')


async def start_db() -> None:
    global db, cur, cipher

    try:
        cipher = Fernet(CARD_KEY)
    except (TypeError, ValueError):
        raise SystemExit('CARD_KEY is not a valid Fernet key')

    db = connect(database=DB_PATH)
    cur = db.cursor()

    migrate()
    check_key()


async def add_card(user_id: str, card_number: str, card_nickname: str) -> None:
    cur.execute(
        'INSERT INTO cards (user_id, card_number, card_nickname) '
        'VALUES (?, ?, ?)',
        (user_id, encrypt(card_number), card_nickname)
    )
    db.commit()


async def get_cards(user_id: str) -> list:
    rows = cur.execute(
        'SELECT id, card_nickname, card_number '
        'FROM cards '
        'WHERE user_id=(?) '
        'ORDER BY id',
        (user_id,)
    ).fetchall()

    return [(card_id, card_nickname, decrypt(card_number))
            for card_id, card_nickname, card_number in rows]


async def get_card(user_id: str, card_id: int) -> tuple | None:
    row = cur.execute(
        'SELECT card_nickname, card_number '
        'FROM cards '
        'WHERE user_id=(?) AND id=(?)',
        (user_id, card_id)
    ).fetchone()

    if row is None:
        return None

    card_nickname, card_number = row

    return card_nickname, decrypt(card_number)


async def delete_card_by_id(user_id: str, card_id: int) -> None:
    cur.execute(
        'DELETE FROM cards '
        'WHERE user_id=(?) AND id=(?)',
        (user_id, card_id)
    )
    db.commit()


async def edit_card_by_id(
        user_id: str,
        card_id: int,
        new_card_number: str) -> None:
    cur.execute(
        'UPDATE cards '
        'SET card_number=(?) '
        'WHERE user_id=(?) AND id=(?)',
        (encrypt(new_card_number), user_id, card_id)
    )
    db.commit()


async def rename_card_by_id(
        user_id: str,
        card_id: int,
        new_card_nickname: str) -> None:
    cur.execute(
        'UPDATE cards '
        'SET card_nickname=(?) '
        'WHERE user_id=(?) AND id=(?)',
        (new_card_nickname, user_id, card_id)
    )
    db.commit()


async def count_cards(user_id: str) -> int:
    return cur.execute(
        'SELECT COUNT(*) '
        'FROM cards '
        'WHERE user_id=(?)',
        (user_id,)
    ).fetchone()[0]
