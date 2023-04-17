from sqlite3 import connect


async def start() -> None:
    global db, cur

    db = connect(database='db.db')
    cur = db.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS cards (user_id TEXT, card_number INTEGER)')
    db.commit()


async def get_cards(user_id: int) -> list:
    return cur.execute('SELECT card_number FROM card WHERE user_id = (?)', (user_id,)).fetchall()


async def add_card(user_id: int, card_number: int) -> None:
    cur.execute('INSERT INTO cards VALUES (?, ?)', (user_id, card_number,))
