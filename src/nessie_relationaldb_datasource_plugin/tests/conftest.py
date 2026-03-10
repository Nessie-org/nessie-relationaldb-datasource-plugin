import sqlite3
import pytest


@pytest.fixture(scope="session")
def test_db(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("data") / "test.db"
    conn = sqlite3.connect(str(db_path))

    conn.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            age INTEGER
        );
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            title TEXT,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        INSERT INTO users VALUES (1, 'Ana', 28);
        INSERT INTO users VALUES (2, 'Marko', 35);
        INSERT INTO users VALUES (3, 'Solo', 22);

        INSERT INTO posts VALUES (1, 'Hello World', 1);
        INSERT INTO posts VALUES (2, 'Python je kul', 1);
        INSERT INTO posts VALUES (3, 'GraphDB > RelDB', 2);
    """)

    conn.commit()
    conn.close()
    return str(db_path)
