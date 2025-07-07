from comparison_interface.main.db.connection import db
from comparison_interface.main.db.models import User
from comparison_interface.main.views import register


def test_page_links_all_true(equal_weight_client):
    """
    GIVEN a flask app configured for testing and equal weights and all of the options for header links set to true
    WHEN the registration page is displayed
    THEN the correct page links appear in the header (this is really testing the base request)
    """
    with equal_weight_client:
        response = equal_weight_client.get("/register")
        assert b'href="/introduction"' in response.data
        assert b'href="/ethics-agreement"' in response.data
        assert b'href="/policies"' in response.data
        assert b'href="/logout"' in response.data


def test_page_links_all_false(mocker, equal_weight_client):
    """
    GIVEN a flask app configured for testing and equal weights and all of the options for header links set to false
    WHEN the registration page is displayed
    THEN the correct page links appear in the header (this is really testing the base request)
    """
    should_render = mocker.patch.object(register.WS, 'should_render')
    # 1 for the ethics button on the form (same setting as header)
    # 3 for the request items for the header
    # 1 for the cookie banner
    should_render.side_effect = [False, False, False, False, True]
    with equal_weight_client:
        response = equal_weight_client.get("/register")
        assert b'href="/introduction"' not in response.data
        assert b'href="/ethics-agreement"' not in response.data
        assert b'href="/policies"' not in response.data
        assert b'href="/logout"' in response.data


def test_register_user_with_escape_route_on(equal_weight_client, user_data):
    """
    GIVEN a flask app configured for testing and equal weights and with the escape route on
    WHEN a new user registers on the site
    THEN the user is stored in the database with cycle count set at 0 and is redirected to the item selection page
    """
    with equal_weight_client:
        response = equal_weight_client.post("/register", data=user_data)

        # Check that there was a redirect to the next page.
        assert response.status_code == 302
        assert b'href="/selection/items"' in response.data

        # Verify the user was inserted into the database with the cycle count set as 0 and added to the session
        with equal_weight_client.session_transaction() as session:
            user = db.session.scalars(db.select(User).order_by(User.user_id.desc())).first()
            assert user.completed_cycles == 0
            assert isinstance(user.user_id, int)
            assert user.user_id == session['user_id']


def test_register_user_with_escape_route_off(mocker, equal_weight_client, user_data):
    """
    GIVEN a flask app configured for testing and equal weights and with the escape route off
    WHEN a new user registers on the site
    THEN the user is stored in the database with cycle count set to None and is redirected to the item selection page
    """
    with equal_weight_client:
        escape_route_setting = mocker.patch.object(register.WS, 'get_behaviour_conf')
        escape_route_setting.side_effect = [False]
        response = equal_weight_client.post("/register", data=user_data)

        # Check that there was a redirect to the next page.
        assert response.status_code == 302
        assert b'href="/selection/items"' in response.data

        # Verify the user was inserted into the database with the cycle count set as 0 and added to the session
        with equal_weight_client.session_transaction() as session:
            user = db.session.scalars(db.select(User).order_by(User.user_id.desc())).first()
            assert user.completed_cycles is None
            assert isinstance(user.user_id, int)
            assert user.user_id == session['user_id']
