import pytest

from comparison_interface.db.connection import db
from comparison_interface.db.models import UserItem
from tests_python.conftest import execute_setup


def test_redirect_to_registration(equal_weight_client):
    """
    GIVEN a flask application configured for testing and equal weights
    WHEN no user is logged in and the item selection page is requested
    THEN the user is redirected to the registration page
    """
    with equal_weight_client:
        response = equal_weight_client.get("/selection/items")
        assert response.status_code == 302
        assert b'href="/register"' in response.data


def test_render_prefer_item_selection(equal_weight_client, user_data):
    """
    GIVEN a flask application configured for testing and equal weights
    WHEN a user is logged in and the item selection page is requested
    THEN the item selection page is shown correctly with the correct title and buttons visible
    """
    with equal_weight_client:
        equal_weight_client.post("/register", data=user_data)
        response = equal_weight_client.get("/selection/items", data=user_data)
        assert response.status_code == 200
        assert b'Comparison Software: Item Preference Selection' in response.data
        assert b'agree-button' in response.data
        assert b'disagree-button' in response.data


def test_no_render_prefer_item_selection_with_custom_weights(custom_weight_client, user_data):
    """
    GIVEN a flask application configured for testing and custom weights
    WHEN a user is logged in and the item selection page is requested
    THEN the user is redirected to the ranking page
    """
    with custom_weight_client:
        custom_weight_client.post("/register", data=user_data)
        response = custom_weight_client.get("/selection/items", data=user_data, follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == "/rank"


def test_no_render_prefer_item_selection_when_asked_not_to_in_config(user_data):
    """
    GIVEN a flask application configured for testing and  equal weights but with the setting for item preferences
        set to false
    WHEN a user is logged in and the item selection page is requested
    THEN the user is redirected to the ranking page
    """
    app = execute_setup("../tests_python/test_configurations/config-equal-item-weights-2.json")
    with app.app_context():
        client = app.test_client()
        client.post("/register", data=user_data)
        response = client.get("/selection/items", data=user_data, follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == "/rank"


def test_register_prefer_item_selection(equal_weight_client, user_data):
    """
    GIVEN a flask application configured for testing and equal weights
    WHEN a user is logged in and an item preference is posted
    THEN the user is redirected back to the item preference page to make another preference decision
    """
    with equal_weight_client:
        equal_weight_client.post("/register", data=user_data)
        preference_data = {'action': 'agree', 'item_id': '1'}
        response = equal_weight_client.post("/selection/items", data=preference_data)
        assert response.status_code == 302
        assert b'href="/selection/items"' in response.data


@pytest.mark.usefixtures('add_basic_data_equal')
def test_redirect_to_rank_page_when_all_preferences_specified(equal_weight_client):
    """
    GIVEN a flask application configured for testing and equal weights
    WHEN a user is logged in and the final item preference  for the users group is posted
    THEN the user is redirected to the rank page
    """
    user_id = 1
    # add two more preferences so we only have one remaining in the group
    item_preferences = [
        {'user_id': user_id, 'item_id': 10, 'known': True},
        {'user_id': user_id, 'item_id': 11, 'known': True},
    ]
    for preference in item_preferences:
        item = UserItem(**preference)
        db.session.add(item)
    db.session.commit()
    with equal_weight_client.session_transaction() as session:
        session['user_id'] = user_id
        session['group_ids'] = [1]
        session['weight_conf'] = 'equal'
        session['previous_comparison_id'] = None
        session['comparison_ids'] = []
    # post the last preference and follow the redirect
    preference_data = {'action': 'agree', 'item_id': '12'}
    response = equal_weight_client.post("/selection/items", data=preference_data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Comparison Software: Items Rank' in response.data
    assert response.request.path == "/rank"
