import logging
from contextlib import contextmanager
from sqlite3 import connect

from cryptography.fernet import Fernet, InvalidToken

from bot.config import CARD_KEY, DB_PATH

logger = logging.getLogger(__name__)

# 1: cards have their own id and encrypted card numbers
# 2: conversation states are kept in the database
# 3: a user can mark one card as favorite
SCHEMA_VERSION = 3

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

# Data is stored encrypted, as it holds what the user is in the middle of
# entering
CREATE_FSM = (
    'CREATE TABLE fsm '
    '(chat TEXT NOT NULL, '
    'user TEXT NOT NULL, '
    'state TEXT, '
    'data TEXT, '
    'PRIMARY KEY (chat, user))'
)


def encrypt(card_number: str) -> str:
    return cipher.encrypt(card_number.encode()).decode()


def decrypt(token: str) -> str:
    return cipher.decrypt(token.encode()).decode()


@contextmanager
def transaction():
    """One explicit transaction, so a failed migration leaves the database
    as it was."""
    db.isolation_level = None
    try:
        cur.execute('BEGIN')
        yield
        cur.execute('COMMIT')
    except BaseException:
        cur.execute('ROLLBACK')
        raise
    finally:
        db.isolation_level = ''


def migrate_to_1() -> None:
    has_cards = cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='cards'"
    ).fetchone()

    with transaction():
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

            logger.info('Migrated %d cards to schema version 1', len(rows))
        else:
            cur.execute(CREATE_CARDS.format(table='cards'))

        cur.execute('PRAGMA user_version = 1')

    if has_cards:
        # Pages of the dropped table still hold the plain card numbers until
        # they are overwritten, so rebuild the file without them
        cur.execute('VACUUM')


def migrate_to_2() -> None:
    with transaction():
        cur.execute(CREATE_FSM)
        cur.execute('PRAGMA user_version = 2')


def migrate_to_3() -> None:
    with transaction():
        cur.execute('ALTER TABLE cards '
                    'ADD COLUMN favorite INTEGER NOT NULL DEFAULT 0')
        # The database itself keeps it to one favorite card per user
        cur.execute('CREATE UNIQUE INDEX one_favorite_per_user '
                    'ON cards (user_id) WHERE favorite = 1')
        cur.execute('PRAGMA user_version = 3')


def migrate() -> None:
    version = cur.execute('PRAGMA user_version').fetchone()[0]

    if version < 1:
        migrate_to_1()
    if version < 2:
        migrate_to_2()
    if version < 3:
        migrate_to_3()


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
        'ORDER BY favorite DESC, id',
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
        new_card_number: str) -> bool:
    """Returns False when the user has no such card."""
    cur.execute(
        'UPDATE cards '
        'SET card_number=(?) '
        'WHERE user_id=(?) AND id=(?)',
        (encrypt(new_card_number), user_id, card_id)
    )
    saved = cur.rowcount > 0
    db.commit()

    return saved


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


async def nickname_taken(user_id: str, card_nickname: str,
                         except_card_id: int | None = None) -> bool:
    # Compared in Python: SQLite's lower() only folds ASCII, so "Моно" and
    # "моно" would count as different there
    wanted = card_nickname.casefold()

    return any(
        card_id != except_card_id and nickname.casefold() == wanted
        for card_id, nickname in cur.execute(
            'SELECT id, card_nickname FROM cards WHERE user_id=(?)',
            (user_id,)
        )
    )


async def stats() -> dict:
    users, cards, most = cur.execute(
        'SELECT COUNT(DISTINCT user_id), COUNT(*), '
        '(SELECT COUNT(*) FROM cards GROUP BY user_id '
        'ORDER BY COUNT(*) DESC LIMIT 1) '
        'FROM cards'
    ).fetchone()
    dialogs = cur.execute('SELECT COUNT(*) FROM fsm').fetchone()[0]

    return {'users': users, 'cards': cards, 'most': most or 0,
            'dialogs': dialogs}


async def favorite_card_id(user_id: str) -> int | None:
    row = cur.execute(
        'SELECT id FROM cards WHERE user_id=(?) AND favorite=1',
        (user_id,)
    ).fetchone()

    return row[0] if row else None


async def set_favorite(user_id: str, card_id: int) -> None:
    # One transaction, so the user never ends up with two favorites or a
    # moment without the old one being cleared
    with transaction():
        # A deleted or someone else's card must not take the favorite away
        # from the current one
        if cur.execute('SELECT 1 FROM cards WHERE user_id=(?) AND id=(?)',
                       (user_id, card_id)).fetchone() is None:
            return

        cur.execute('UPDATE cards SET favorite=0 WHERE user_id=(?)',
                    (user_id,))
        cur.execute('UPDATE cards SET favorite=1 '
                    'WHERE user_id=(?) AND id=(?)',
                    (user_id, card_id))


async def unset_favorite(user_id: str, card_id: int) -> None:
    cur.execute(
        'UPDATE cards SET favorite=0 WHERE user_id=(?) AND id=(?)',
        (user_id, card_id)
    )
    db.commit()
