from sqlite3 import connect


async def start() -> None:
    global db, cur

    db = connect(database='db.db')
    cur = db.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS cards (user_id TEXT, card_number TEXT, card_nickname TEXT,'
                'CONSTRAINT user_id_card_nick UNIQUE (user_id, card_nickname))')
    db.commit()


async def get_cards_nicknames(user_id: str) -> list:
    return cur.execute('SELECT card_nickname FROM cards WHERE user_id=(?)', (user_id,)).fetchall()


async def get_card_number(user_id: str, card_nickname: str) -> str:
    return cur.execute('SELECT card_number FROM cards WHERE user_id=(?) AND card_nickname=(?)',
                       (user_id, card_nickname)).fetchone()[0]


async def add_card(user_id: str, card_number: str, card_nickname: str) -> None:
    cur.execute('INSERT INTO cards VALUES (?, ?, ?)', (user_id, card_number, card_nickname))
    db.commit()


async def delete_card(user_id: str, card_number: str) -> None:
    cur.execute('DELETE FROM cards WHERE user_id=(?) and card_number=(?)', (user_id, card_number))
    db.commit()


async def edit_card(user_id: str, card_number: str, new_card_number: str) -> None:
    pass
