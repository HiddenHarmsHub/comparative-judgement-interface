import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import MetaData
from sqlalchemy.exc import SQLAlchemyError

from app import create_app
from comparison_interface.configuration.validation import Validation as ConfigValidation
from comparison_interface.configuration.website import Settings as WS
from comparison_interface.db.connection import db
from comparison_interface.db.models import ParticipantGroup, ParticipantItem
from comparison_interface.db.setup import Setup as DBSetup


def execute_setup(conf_file):
    """Setup a test system."""
    app = create_app(testing=True)
    # 1. Validate the website configuration
    app.logger.info("Setting website configuration")
    WS.set_configuration_location(app, conf_file)
    ConfigValidation(app).validate()

    # 2. Configure database
    app.logger.info("Resetting website database")
    s = DBSetup(app)
    s.exec()
    return app


@pytest.fixture()
def equal_weight_app():
    """Set up the project for testing with equal weights."""
    app = execute_setup("../tests_python/test_configurations/config-equal-item-weights.json")
    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()
        os.unlink(os.path.join(os.path.join(app.instance_path), 'test_admin_database.db'))
        os.unlink(os.path.join(os.path.join(app.instance_path), 'test_database.db'))


@pytest.fixture()
def equal_weight_client(equal_weight_app):
    """Return the test client for the equal weight app."""
    with equal_weight_app.app_context():
        yield equal_weight_app.test_client()


@pytest.fixture()
def custom_weight_app():
    """Set up the project for testing with custom weights."""
    app = execute_setup("../tests_python/test_configurations/config-custom-item-weights.json")
    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()
        os.unlink(os.path.join(os.path.join(app.instance_path), 'test_admin_database.db'))
        os.unlink(os.path.join(os.path.join(app.instance_path), 'test_database.db'))


@pytest.fixture()
def custom_weight_client(custom_weight_app):
    """Return the test client for the custom weight app."""
    with custom_weight_app.app_context():
        yield custom_weight_app.test_client()


@pytest.fixture(scope='session')
def participant_data():
    """Return some test participant data."""
    participant_data = {
        'name': 'Dummy test',
        'country': 'England',
        'allergies': 'Yes',
        'age': '30',
        'email': 'dummy@test',
        'accepted_ethics_agreement': '1',
        'group_ids': [1],
    }
    return participant_data


@pytest.fixture()
def add_basic_data_custom(custom_weight_client):
    # add a participant
    participant_data = {
        'name': 'Tester One',
        'country': 'England',
        'allergies': 'Yes',
        'age': '30',
        'email': 'dummy@test',
        'accepted_ethics_agreement': '1',
    }
    participant_data['created_date'] = datetime.now(timezone.utc)
    db_engine = db.engines['study_db']
    db_meta = MetaData()
    db_meta.reflect(bind=db_engine)
    table = db_meta.tables["participant"]
    new_participant_sql = table.insert().values(**participant_data)
    try:
        # Insert the participant into the database
        with db_engine.begin() as connection:
            result = connection.execute(new_participant_sql)
        id = result.lastrowid
    except SQLAlchemyError as e:
        raise RuntimeError(str(e))
    db.session.commit
    # insert the group preferences for the east of england group (assumes groups are always added the same way)
    participant_group_data = {
        'participant_id': id,
        'group_id': 2,
        'created_date': datetime.now(timezone.utc),
    }
    participant_group = ParticipantGroup(**participant_group_data)
    db.session.add(participant_group)
    db.session.commit()

    yield


@pytest.fixture()
def add_basic_data_equal(equal_weight_client):
    # add data for a participant with 9 item preferences (for 12 group items)
    participant_data = {
        'name': 'Tester One',
        'country': 'England',
        'allergies': 'Yes',
        'age': '30',
        'email': 'dummy@test',
        'accepted_ethics_agreement': '1',
    }
    participant_data['created_date'] = datetime.now(timezone.utc)
    db_engine = db.engines['study_db']
    db_meta = MetaData()
    db_meta.reflect(bind=db_engine)
    table = db_meta.tables["participant"]
    new_participant_sql = table.insert().values(**participant_data)
    try:
        # Insert the participant into the database
        with db_engine.begin() as connection:
            result = connection.execute(new_participant_sql)
        id = result.lastrowid
    except SQLAlchemyError as e:
        raise RuntimeError(str(e))
    db.session.commit
    # insert the group preferences for the participant (assumes groups are always added the same way)
    participant_group_data = {
        'participant_id': id,
        'group_id': 1,
        'created_date': datetime.now(timezone.utc),
    }
    participant_group = ParticipantGroup(**participant_group_data)
    db.session.add(participant_group)
    db.session.commit()
    item_preferences = [
        {'participant_id': id, 'item_id': 1, 'known': True},
        {'participant_id': id, 'item_id': 2, 'known': True},
        {'participant_id': id, 'item_id': 3, 'known': True},
        {'participant_id': id, 'item_id': 4, 'known': False},
        {'participant_id': id, 'item_id': 5, 'known': False},
        {'participant_id': id, 'item_id': 6, 'known': False},
        {'participant_id': id, 'item_id': 7, 'known': True},
        {'participant_id': id, 'item_id': 8, 'known': True},
        {'participant_id': id, 'item_id': 9, 'known': True},
    ]
    for preference in item_preferences:
        item = ParticipantItem(**preference)
        db.session.add(item)
    db.session.commit()

    # add data for a participant with only one item preference
    participant_data = {
        'name': 'Tester Two',
        'country': 'England',
        'allergies': 'Yes',
        'age': '30',
        'accepted_ethics_agreement': '1',
    }
    participant_data['created_date'] = datetime.now(timezone.utc)
    db_engine = db.engines['study_db']
    db_meta = MetaData()
    db_meta.reflect(bind=db_engine)
    table = db_meta.tables["participant"]
    new_participant_sql = table.insert().values(**participant_data)
    try:
        # Insert the participant into the database
        with db_engine.begin() as connection:
            result = connection.execute(new_participant_sql)
        id = result.lastrowid
    except SQLAlchemyError as e:
        raise RuntimeError(str(e))
    db.session.commit
    # insert the group preferences for the participant (assumes groups are always added the same way)
    participant_group_data = {
        'participant_id': id,
        'group_id': 1,
        'created_date': datetime.now(timezone.utc),
    }
    participant_group = ParticipantGroup(**participant_group_data)
    db.session.add(participant_group)
    db.session.commit()
    item_preferences = [{'participant_id': id, 'item_id': 1, 'known': True}]
    for preference in item_preferences:
        item = ParticipantItem(**preference)
        db.session.add(item)
    db.session.commit()

    yield
