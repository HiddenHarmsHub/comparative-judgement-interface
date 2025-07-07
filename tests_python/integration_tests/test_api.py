import os
from datetime import datetime, timezone

import pytest

from app import create_app
from comparison_interface.configuration.validation import Validation as ConfigValidation
from comparison_interface.configuration.website import Settings as WS
from comparison_interface.db.connection import db
from comparison_interface.db.models import Comparison
from comparison_interface.db.setup import Setup as DBSetup


# custom fixtures for these tests
def execute_setup_with_api(conf_file):
    app = create_app(
        {
            "TESTING": True,
            "API_ACCESS": True,
            "API_KEY_FILE": ".tstkyapi",
            "SQLALCHEMY_DATABASE_URI": 'sqlite:///test_database.db',
        }
    )
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
def equal_weight_app_api():
    """Set up the project for testing with equal weights with the api."""
    app = execute_setup_with_api("../tests_python/test_configurations/config-equal-item-weights.json")
    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()
        os.unlink('instance/test_database.db')


@pytest.fixture()
def equal_weight_client_api(equal_weight_app_api):
    """Return the test client for the equal weight app with the api."""
    with equal_weight_app_api.app_context():
        yield equal_weight_app_api.test_client()


@pytest.fixture()
def key_file(equal_weight_app_api):
    filename = equal_weight_app_api.config['API_KEY_FILE']
    while os.path.exists(filename):
        filename = f'{filename}1'
    with open(filename, mode='w') as key_file:
        key_file.write('test-key')
    yield

    with equal_weight_app_api.app_context():
        os.remove(filename)


def test_api_not_available_when_not_configured(equal_weight_client):
    """
    GIVEN a flask app configured for testing and with equal weights and with API_ACCESS set to False
    WHEN the api urls are requested
    THEN a 404 page is shown
    """
    response = equal_weight_client.get("/api/judgements")
    assert response.status_code == 404
    response = equal_weight_client.get("/api/items")
    assert response.status_code == 404


def test_api_not_available_when_switched_on_but_no_key(equal_weight_client_api):
    """
    GIVEN a flask app configured for testing and with equal weights and with API_ACCESS set to True but no key file
    WHEN the api urls are requested
    THEN a 501 page is shown
    """
    response = equal_weight_client_api.get("/api/judgements")
    assert response.status_code == 501
    response = equal_weight_client_api.get("/api/items")
    assert response.status_code == 501


@pytest.mark.usefixtures('key_file')
def test_api_not_available_when_switched_on_but_no_key_sent(equal_weight_client_api):
    """
    GIVEN a flask app configured for testing, with equal weights, API_ACCESS and a key file
    WHEN the api url is requested but the api key is not provided
    THEN a 401 page is shown
    """
    response = equal_weight_client_api.get("/api/judgements")
    assert response.status_code == 401
    response = equal_weight_client_api.get("/api/items")
    assert response.status_code == 401


@pytest.mark.usefixtures('key_file')
def test_judgements_api_available_when_switched_on_if_key_sent(equal_weight_client_api):
    """
    GIVEN a flask app configured for testing, with equal weights, API_ACCESS and a key file
    WHEN the api judgements url is requested and the api key is provided
    THEN a 200 code is received and the comparison data is returned
    """
    comparison_data_list = [
        {
            'user_id': 1,
            'item_1_id': 1,
            'item_2_id': 2,
            'selected_item_id': 1,
            'state': 'selected',
            'created': datetime.now(timezone.utc),
            'updated': datetime.now(timezone.utc),
        },
        {
            'user_id': 1,
            'item_1_id': 4,
            'item_2_id': 3,
            'selected_item_id': None,
            'state': 'skipped',
            'created': datetime.now(timezone.utc),
            'updated': datetime.now(timezone.utc),
        },
    ]
    for comparison_data in comparison_data_list:
        comparison = Comparison(**comparison_data)
        db.session.add(comparison)
    db.session.commit()
    response = equal_weight_client_api.get("/api/judgements", headers={'x-api-key': 'test-key'})
    assert response.status_code == 200
    assert b'comparison_id,user_id,item_1_id,item_2_id,selected_item_id,state,created,updated' in response.data
    assert b'skipped' in response.data
    assert b'selected' in response.data


@pytest.mark.usefixtures('key_file')
def test_items_api_available_when_switched_on_if_key_sent(equal_weight_client_api):
    """
    GIVEN a flask app configured for testing, with equal weights, API_ACCESS and a key file
    WHEN the api items url is requested and the api key is provided
    THEN a 200 code is received and the item data is returned
    """
    response = equal_weight_client_api.get("/api/items", headers={'x-api-key': 'test-key'})
    assert response.status_code == 200
    assert b'item_id,name,display_name,image_path,created_date' in response.data
    assert b'1,north_east,North East,item_1.png' in response.data


@pytest.mark.usefixtures('key_file')
def test_outcomes_api_available_and_correct_when_switched_on_if_key_sent(equal_weight_client_api):
    """
    GIVEN a flask app configured for testing, with equal weights, API_ACCESS and a key file
    WHEN the api outcomes url is requested and the api key is provided
    THEN a 200 code is received and the correct outcome data is returned
    """
    comparison_data_list = [
        {
            'user_id': 1,
            'item_1_id': 1,
            'item_2_id': 2,
            'selected_item_id': 1,
            'state': 'selected',
            'created': datetime.now(timezone.utc),
            'updated': datetime.now(timezone.utc),
        },
        {
            'user_id': 1,
            'item_1_id': 4,
            'item_2_id': 3,
            'selected_item_id': None,
            'state': 'skipped',
            'created': datetime.now(timezone.utc),
            'updated': datetime.now(timezone.utc),
        },
        {
            'user_id': 1,
            'item_1_id': 3,
            'item_2_id': 4,
            'selected_item_id': 4,
            'state': 'selected',
            'created': datetime.now(timezone.utc),
            'updated': datetime.now(timezone.utc),
        },
        {
            'user_id': 1,
            'item_1_id': 1,
            'item_2_id': 3,
            'selected_item_id': None,
            'state': 'tied',
            'created': datetime.now(timezone.utc),
            'updated': datetime.now(timezone.utc),
        },
    ]
    for comparison_data in comparison_data_list:
        comparison = Comparison(**comparison_data)
        db.session.add(comparison)
    db.session.commit()
    response = equal_weight_client_api.get("/api/outcomes", headers={'x-api-key': 'test-key'})
    assert response.status_code == 200
    assert response.data == b'item_1_id,item_2_id,outcome\r\n1,2,0\r\n3,4,1\r\n1,3,2\r\n'
