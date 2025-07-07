from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


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
