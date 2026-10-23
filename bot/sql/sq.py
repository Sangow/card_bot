from sqlite3 import connect


async def start_db() -> None:
    global db, cur

    db = connect(database='/data/db.db')
    cur = db.cursor()

    cur.execute(
        'CREATE TABLE IF NOT EXISTS cards '
        '(user_id TEXT, '
        'card_number TEXT, '
        'card_nickname TEXT, '
        'CONSTRAINT user_id_card_nick UNIQUE (user_id, card_nickname))'
    )
    db.commit()


async def add_card(user_id: str, card_number: str, card_nickname: str) -> None:
    cur.execute(
        'INSERT INTO cards VALUES (?, ?, ?)',
        (user_id, card_number, card_nickname)
    )
    db.commit()


async def get_cards(user_id: str) -> list:
    return cur.execute(
        'SELECT rowid, card_nickname '
        'FROM cards '
        'WHERE user_id=(?)',
        (user_id,)
    ).fetchall()


async def get_card(user_id: str, card_id: int) -> tuple | None:
    return cur.execute(
        'SELECT card_nickname, card_number '
        'FROM cards '
        'WHERE user_id=(?) AND rowid=(?)',
        (user_id, card_id)
    ).fetchone()


async def delete_card_by_id(user_id: str, card_id: int) -> None:
    cur.execute(
        'DELETE FROM cards '
        'WHERE user_id=(?) AND rowid=(?)',
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
        'WHERE user_id=(?) AND rowid=(?)',
        (new_card_number, user_id, card_id)
    )
    db.commit()
