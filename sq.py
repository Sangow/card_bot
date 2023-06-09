from sqlite3 import connect


async def start() -> None:
    global db, cur

    db = connect(database='db.db')
    cur = db.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS cards (user_id TEXT, card_number TEXT, card_nickname TEXT)')
    db.commit()


async def get_cards_nicknames(user_id: int) -> list:
    return cur.execute('SELECT card_nickname FROM cards WHERE user_id = (?)', (user_id,)).fetchall()


async def get_card_number(user_id: int, card_nickname: str) -> str:
    return cur.execute('SELECT card_number FROM cards WHERE user_id = (?) AND card_nickname = (?)',
                       (user_id, card_nickname)).fetchone()[0]


async def add_card(user_id: int, card_number: str, card_nickname: str) -> None:
    cur.execute('INSERT INTO cards VALUES (?, ?, ?)', (user_id, card_number, card_nickname))
    db.commit()
