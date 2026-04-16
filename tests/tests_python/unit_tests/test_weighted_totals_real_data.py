import json
import os
from datetime import datetime, timezone

import pytest
from numpy.random import default_rng
from PIL import Image
from sqlalchemy import MetaData
from sqlalchemy.exc import SQLAlchemyError

from comparison_interface.db.connection import db
from comparison_interface.db.models import ParticipantGroup
from comparison_interface.main.views import rank
from comparison_interface.main.views.register import Request
from tests.tests_python.conftest import execute_setup


@pytest.fixture()
def larger_app():
    """Set up the project for testing with equal weights."""
    # create the images
    config_path = os.path.abspath("../comparison-interface/tests/test_configurations/config-weighted-totals.json")
    with open(config_path, mode="r") as config_file:
        config_dict = json.load(config_file)
    for image_config in config_dict['comparisonConfiguration']['groups'][0]['items']:
        image_name = image_config['imageName']
        new_image = Image.new("RGB", (300, 300))
        new_image.save(f"comparison_interface/static/images/{image_name}", "PNG")
    app = execute_setup("../tests/test_configurations/config-weighted-totals.json")
    yield app

    with app.app_context():
        # delete the created images
        for image_config in config_dict['comparisonConfiguration']['groups'][0]['items']:
            image_name = image_config['imageName']
            image_path = os.path.abspath(f"../comparison_interface/static/images/{image_name}")
            os.remove(image_path)
        db.session.remove()
        db.drop_all()
        os.unlink(os.path.join(os.path.join(app.instance_path), 'test_admin_database.db'))
        os.unlink(os.path.join(os.path.join(app.instance_path), 'test_database.db'))


@pytest.fixture()
def larger_client(larger_app):
    """Return the test client for the equal weight app."""
    with larger_app.app_context():
        yield larger_app.test_client()


@pytest.fixture()
def add_basic_data_larger(larger_client):
    # add data for a participant in the group
    participant_data = {
        'accepted_ethics_agreement': '1'
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
    yield


@pytest.mark.usefixtures('add_basic_data_larger')
def test_random_item_retrieval_on_repeat(mocker, larger_app):
    """
    GIVEN a flask app configured for testing with a configuration file with 70 items with equal weights
    WHEN a user has an active session specifying a group_id and _get_random_items is called multiple times
    THEN in repeated calls the generation of the item ids remains random

    Makes 100 calls to _get_random_items 100 times and checks that the mean uniqueness of pairs over those runs is
    greater than or equal to 97
    """
    request = Request(larger_app, {})
    request._session['participant_id'] = 1
    request._session['group_ids'] = [1]
    request._session['weight_conf'] = 'equal'
    request._session['previous_comparison_id'] = None
    request._session['comparison_ids'] = []
    ranker = rank.Rank(request, request._session)

    larger_app.rng = default_rng()
    ranker._app = larger_app

    mean_uniquenesses = []
    for _ in range(0, 100):
        uniqueness_counts = []
        for _ in range(0, 25):
            suggested_item_ids = []
            for _ in range(0, 20):
                items = ranker._get_random_items()
                suggested_item_ids.append(items)
            assert len(suggested_item_ids) == 20
            unique_items = set(suggested_item_ids)
            uniqueness_counts.append(len(unique_items))
        mean_uniqueness = sum(uniqueness_counts) / len(uniqueness_counts)
        mean_uniquenesses.append(mean_uniqueness)
    print(mean_uniquenesses)
    low_uniqueness = [x for x in mean_uniquenesses if x <= 19]
    assert len(low_uniqueness) == 0
