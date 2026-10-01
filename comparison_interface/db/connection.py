from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()
csrf = CSRFProtect()


def enable_sqlite_foreign_keys():
    """Turn on the foreign key checks for all connections to all binds."""

    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, _):
        ac = dbapi_connection.autocommit
        dbapi_connection.autocommit = True
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        dbapi_connection.autocommit = ac

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
