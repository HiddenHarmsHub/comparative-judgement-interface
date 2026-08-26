from sqlalchemy import delete, update

from .connection import db
from .models import Comparison, Participant, ParticipantGroup, ParticipantItem, TotalItemPair


def clear_study_data():
    """Clear the participant and judgement data from the database and reset the TotalItemPair judgement tracker."""
    tables_to_clear = [Comparison, ParticipantGroup, ParticipantItem, Participant]

    db_engine = db.engines['study_db']
    with db_engine.begin() as connection:
        for table in tables_to_clear:
            connection.execute(delete(table))

        connection.execute(update(TotalItemPair).values(judged=False))
