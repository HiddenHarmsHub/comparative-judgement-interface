from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()
csrf = CSRFProtect()


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, _):
    """Enable SQLite foreign-key enforcement on every new connection."""
    previous_autocommit = dbapi_connection.autocommit
    dbapi_connection.autocommit = True
    try:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()
    finally:
        dbapi_connection.autocommit = previous_autocommit


def persist(conn, obj):
    """Make an object persistent in the database.

    In order to get the last inserted id, the object needs to be flushed through the
    database connection. This is not the same as committing the transaction.

    Args:
        conn (db): SQLAlchemy connection
        obj (db): Database object to be persisted in the database.

    Returns:
        db: The object after refreshing the persisted values as the primary keys
    """
    conn.session.add(obj)
    conn.session.flush()
    conn.session.refresh(obj)

    return obj
