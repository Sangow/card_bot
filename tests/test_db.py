import asyncio
import sqlite3

import pytest
from cryptography.fernet import Fernet

import bot.sql.sq as sq

# The schema the bot used before version 1, as it is in production
OLD_SCHEMA = (
    'CREATE TABLE cards '
    '(user_id TEXT, '
    'card_number TEXT, '
    'card_nickname TEXT, '
    'CONSTRAINT user_id_card_nick UNIQUE (user_id, card_nickname))'
)


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / 'db.db')


@pytest.fixture
def key():
    return Fernet.generate_key().decode()


@pytest.fixture
def start(db_path, monkeypatch):
    def start_db(key: str) -> None:
        monkeypatch.setattr(sq, 'DB_PATH', db_path)
        monkeypatch.setattr(sq, 'CARD_KEY', key)
        asyncio.run(sq.start_db())

    yield start_db

    if hasattr(sq, 'db'):
        sq.db.close()


def run(coro):
    return asyncio.run(coro)


def make_old_db(db_path: str, rows: list) -> None:
    db = sqlite3.connect(db_path)
    db.execute(OLD_SCHEMA)
    db.executemany('INSERT INTO cards VALUES (?, ?, ?)', rows)
    db.commit()
    db.close()


def raw(db_path: str, query: str) -> list:
    db = sqlite3.connect(db_path)
    try:
        return db.execute(query).fetchall()
    finally:
        db.close()


def user_version(db_path: str) -> int:
    return raw(db_path, 'PRAGMA user_version')[0][0]


@pytest.fixture
def old_db(db_path):
    make_old_db(db_path, [
        ('1', '4242424242424242', 'mono'),
        ('1', '5555555555554444', 'gone'),
        ('2', '4000 0566 5566 5556', 'privat'),
    ])
    # A gap in rowids, as left by deleted cards
    db = sqlite3.connect(db_path)
    db.execute("DELETE FROM cards WHERE card_nickname='gone'")
    db.commit()
    db.close()


def test_fresh_database_gets_current_schema(start, db_path, key):
    start(key)

    assert user_version(db_path) == sq.SCHEMA_VERSION
    columns = [row[1] for row in raw(db_path, 'PRAGMA table_info(cards)')]
    assert columns == ['id', 'user_id', 'card_number', 'card_nickname']


def test_migration_keeps_ids_and_cards(start, db_path, key, old_db):
    start(key)

    assert user_version(db_path) == sq.SCHEMA_VERSION
    assert run(sq.get_cards(user_id='1')) == [(1, 'mono', '4242424242424242')]
    # Spaces left by old edits are removed
    assert run(sq.get_cards(user_id='2')) == [
        (3, 'privat', '4000056655665556')]


def test_migration_encrypts_numbers(start, db_path, key, old_db):
    start(key)

    stored = [number for (number,) in raw(db_path,
                                          'SELECT card_number FROM cards')]

    assert len(stored) == 2
    assert all(number.startswith('gAAAAA') for number in stored)
    with open(db_path, 'rb') as f:
        content = f.read()
    assert b'4242424242424242' not in content
    assert b'4000056655665556' not in content


def test_migration_runs_only_once(start, db_path, key, old_db):
    start(key)
    first = raw(db_path, 'SELECT id, card_number FROM cards')
    sq.db.close()

    start(key)

    # Fernet tokens differ on every encryption, so re-encrypting would
    # change them
    assert raw(db_path, 'SELECT id, card_number FROM cards') == first


def test_migrated_database_keeps_unique_nicknames(start, key, old_db):
    start(key)

    with pytest.raises(sqlite3.IntegrityError):
        run(sq.add_card(user_id='1', card_number='4111111111111111',
                        card_nickname='mono'))


def test_new_cards_never_reuse_deleted_ids(start, key, old_db):
    start(key)

    run(sq.add_card(user_id='1', card_number='4111111111111111',
                    card_nickname='new'))
    new_id = run(sq.get_cards(user_id='1'))[-1][0]
    assert new_id == 4

    run(sq.delete_card_by_id(user_id='1', card_id=new_id))
    run(sq.add_card(user_id='1', card_number='4111111111111111',
                    card_nickname='newer'))

    assert run(sq.get_cards(user_id='1'))[-1][0] == 5


def test_failed_migration_leaves_old_table(start, db_path, key, old_db,
                                           monkeypatch):
    def broken(card_number):
        raise RuntimeError('disk is full')

    monkeypatch.setattr(sq, 'encrypt', broken)

    with pytest.raises(RuntimeError):
        start(key)

    assert user_version(db_path) == 0
    assert raw(db_path, 'SELECT rowid, user_id, card_number, card_nickname '
                        'FROM cards ORDER BY rowid') == [
        (1, '1', '4242424242424242', 'mono'),
        (3, '2', '4000 0566 5566 5556', 'privat'),
    ]
    tables = [name for (name,) in raw(
        db_path, "SELECT name FROM sqlite_master WHERE type='table'")]
    assert 'cards_new' not in tables


def test_wrong_key_stops_the_bot(start, key, old_db):
    start(key)
    sq.db.close()

    with pytest.raises(SystemExit, match='does not match'):
        start(Fernet.generate_key().decode())


def test_invalid_key_stops_the_bot(start):
    with pytest.raises(SystemExit, match='not a valid Fernet key'):
        start('not-a-key')


def test_edited_number_is_stored_encrypted(start, db_path, key):
    start(key)
    run(sq.add_card(user_id='1', card_number='4242424242424242',
                    card_nickname='mono'))

    run(sq.edit_card_by_id(user_id='1', card_id=1,
                           new_card_number='5555555555554444'))

    (stored,), = raw(db_path, 'SELECT card_number FROM cards')
    assert stored.startswith('gAAAAA')
    assert run(sq.get_card(user_id='1', card_id=1)) == (
        'mono', '5555555555554444')


def test_version_1_database_gets_states_table(start, db_path, key):
    db = sqlite3.connect(db_path)
    db.execute(sq.CREATE_CARDS.format(table='cards'))
    db.execute('INSERT INTO cards (user_id, card_number, card_nickname) '
               'VALUES (?, ?, ?)',
               ('1', Fernet(key).encrypt(b'4242424242424242').decode(),
                'mono'))
    db.execute('PRAGMA user_version = 1')
    db.commit()
    db.close()

    start(key)

    assert user_version(db_path) == 2
    tables = {name for (name,) in raw(
        db_path, "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {'cards', 'fsm'} <= tables
    assert run(sq.get_cards(user_id='1')) == [(1, 'mono', '4242424242424242')]
