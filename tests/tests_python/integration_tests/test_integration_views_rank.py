import pytest
from flask import session

from comparison_interface.configuration.website import Settings as WS
from comparison_interface.db.connection import db
from comparison_interface.db.models import Comparison, Participant
from comparison_interface.main.views import rank
from tests.tests_python.conftest import execute_setup


def test_redirect_if_not_logged_in(equal_weight_client):
    """
    GIVEN a flask app configured for testing and equal weights
    WHEN the rank page is requested but there is no active participant session
    THEN the participant is redirected to the registration page
    """
    response = equal_weight_client.get("/rank")
    assert response.status_code == 302
    assert b'href="/register"' in response.data


@pytest.mark.usefixtures('add_basic_data_equal')
def test_render_rank_comparison_item_choice(equal_weight_client):
    """
    GIVEN a flask app configured for testing, with equal weights and basic data loaded
    WHEN a logged in participant with no item preferences is specifed accesses the rank page
    THEN an error message is shown because no selections have been made
    """
    with equal_weight_client.session_transaction() as session:
        session['participant_id'] = 2
        session['group_ids'] = [1]
        session['weight_conf'] = 'equal'
        session['previous_comparison_id'] = None
        session['comparison_ids'] = []
    response = equal_weight_client.get("/rank")
    assert response.status_code == 200
    assert b'You must be familiar with at least two of the items to continue with the comparisons.' in response.data


@pytest.mark.usefixtures('add_basic_data_equal')
def test_render_rank_comparison_no_item_choice(participant_data):
    """
    GIVEN a flask application configured for testing and equal weights and basic data loaded but with the setting for
        item preferences set to false
    WHEN a participant logs in in and requests the rank page
    THEN the participant sees ranking page
    """
    app = execute_setup("../tests/tests_python/test_configurations/config-equal-item-weights-2.json")
    client = app.test_client()
    client.post("/register", data=participant_data)
    response = client.get("/rank", follow_redirects=True)
    assert response.status_code == 200
    assert b'Comparison Software: Items Rank' in response.data


def test_register_selected_rank_comparison(equal_weight_client, equal_weight_app, participant_data):
    """
    GIVEN a flask app configured for testing and with equal weights
    WHEN a 'selected' ranking decision is posted to the rank url
    THEN the data is stored in the database and the participant redirected to another rank page
    """
    with equal_weight_client:
        equal_weight_client.post("/register", data=participant_data)
        response = equal_weight_client.post(
            "/rank",
            data={
                'state': 'confirmed',
                'item_1_id': '1',
                'item_2_id': '2',
                'selected_item_id': '1',
            },
        )
        assert response.status_code == 302
        assert b'href="/rank"' in response.data

        with equal_weight_app.app_context():
            query = db.select(Comparison).where(Comparison.participant_id == session['participant_id'])
            comparisons = db.session.scalars(query).all()
            assert len(comparisons) == 1
            comp = comparisons[0]
            assert comp.comparison_id == session['previous_comparison_id']
            assert comp.participant_id == session['participant_id']
            assert comp.selected_item_id == 1
            assert comp.state == 'selected'
            assert comp.item_1_id == 1
            assert comp.item_2_id == 2


def test_register_skipped_rank_comparison(equal_weight_client, equal_weight_app, participant_data):
    """
    GIVEN a flask app configured for testing and with equal weights
    WHEN a 'skipped' ranking decision is posted to the rank url
    THEN the data is stored in the database and the participant redirected to another rank page
    """
    with equal_weight_client:
        equal_weight_client.post("/register", data=participant_data)
        response = equal_weight_client.post(
            "/rank",
            data={
                'state': 'skipped',
                'item_1_id': '1',
                'item_2_id': '2',
            },
        )
        assert response.status_code == 302
        assert b'href="/rank"' in response.data

        with equal_weight_app.app_context():
            query = db.select(Comparison).where(Comparison.participant_id == session['participant_id'])
            comparisons = db.session.scalars(query).all()
            assert len(comparisons) == 1
            comp = comparisons[0]
            assert comp.comparison_id == session['previous_comparison_id']
            assert comp.participant_id == session['participant_id']
            assert comp.selected_item_id is None
            assert comp.state == 'skipped'
            assert comp.item_1_id == 1
            assert comp.item_2_id == 2


def test_rejudging_a_comparison(equal_weight_client, equal_weight_app, participant_data):
    """
    GIVEN a flask app configured for testing and with equal weights
    WHEN a 'skipped' ranking decision is posted to the rank url and is then rejudged
    THEN the data is overwritten in the database and no new decision is added
    """
    with equal_weight_client:
        equal_weight_client.post("/register", data=participant_data)
        response = equal_weight_client.post(
            "/rank",
            data={
                'state': 'skipped',
                'item_1_id': '1',
                'item_2_id': '2',
            },
        )
        assert response.status_code == 302
        assert b'href="/rank"' in response.data

        with equal_weight_app.app_context():
            query = db.select(Comparison).where(Comparison.participant_id == session['participant_id'])
            comparisons = db.session.scalars(query).all()
            assert len(comparisons) == 1
            comp = comparisons[0]
            assert comp.comparison_id == session['previous_comparison_id']
            assert comp.participant_id == session['participant_id']
            assert comp.selected_item_id is None
            assert comp.state == 'skipped'
            assert comp.item_1_id == 1
            assert comp.item_2_id == 2

        response = equal_weight_client.post(
            "/rank",
            data={
                'state': 'confirmed',
                'item_1_id': '1',
                'item_2_id': '2',
                'selected_item_id': '1',
                'comparison_id': '1',
            },
        )
        assert response.status_code == 302
        assert b'href="/rank"' in response.data

        with equal_weight_app.app_context():
            query = db.select(Comparison).where(Comparison.participant_id == session['participant_id'])
            comparisons = db.session.scalars(query).all()
            assert len(comparisons) == 1
            comp = comparisons[0]
            assert comp.comparison_id == session['previous_comparison_id']
            assert comp.comparison_id == 1
            assert comp.participant_id == session['participant_id']
            assert comp.selected_item_id == 1
            assert comp.state == 'selected'
            assert comp.item_1_id == 1
            assert comp.item_2_id == 2


def test_rejudging_request_with_an_invalid_comparison_id_raises_error(equal_weight_client, participant_data):
    """
    GIVEN a flask app configured for testing and with equal weights
    WHEN a rejudging is requested with a comparison_id value that is not in the database
    THEN an exception is raised
    """
    with pytest.raises(Exception):
        equal_weight_client.post("/register", data=participant_data)
        equal_weight_client.post(
            "/rank",
            data={
                'state': 'confirmed',
                'item_1_id': '1',
                'item_2_id': '2',
                'selected_item_id': '1',
                'comparison_id': '100',
            },
        )


def test_requesting_a_previous_comparison_post(equal_weight_app, equal_weight_client):
    """
    GIVEN a flask app configured for testing and equal weights
    WHEN a logged in participant requests to rejudge a comparison by post (trigged by the previous button)
    THEN they are redirected to the page for the requested comparison id
    """
    with equal_weight_client.session_transaction() as session:
        session['participant_id'] = 1
        session['group_ids'] = [1]
        session['weight_conf'] = 'equal'
        session['previous_comparison_id'] = None
        session['comparison_ids'] = []
    # first add a comparison
    response = equal_weight_client.post(
        "/rank",
        data={
            'state': 'confirmed',
            'item_1_id': '1',
            'item_2_id': '2',
            'selected_item_id': '1',
        },
    )
    assert response.status_code == 302
    assert b'href="/rank"' in response.data
    # get the is added
    with equal_weight_app.app_context():
        query = db.select(Comparison).where(Comparison.participant_id == session['participant_id'])
        comparisons = db.session.scalars(query).all()
        assert len(comparisons) == 1
        comparison_id = comparisons[0].comparison_id
    # check the redirect
    response = equal_weight_client.post("/rank", data={'comparison_id': comparison_id, 'state': 'rejudged'})
    assert response.status_code == 302
    test_string = f'href="/rank?comparison_id={comparison_id}"'.encode('utf-8')
    assert test_string in response.data


@pytest.mark.usefixtures('add_basic_data_equal')
def test_requesting_a_previous_comparison_get(equal_weight_app, equal_weight_client):
    """
    GIVEN a flask app configured for testing and equal weights with basic data added
    WHEN a logged in participant has been redirected from the post request to rejudge a comparison
    THEN they see the requested comparison
    """
    with equal_weight_client.session_transaction() as session:
        session['participant_id'] = 1
        session['group_ids'] = [1]
        session['weight_conf'] = 'equal'
        session['previous_comparison_id'] = None
        session['comparison_ids'] = []
    # first add a comparison to retrieve later
    response = equal_weight_client.post(
        "/rank",
        data={
            'state': 'confirmed',
            'item_1_id': '1',
            'item_2_id': '2',
            'selected_item_id': '1',
        },
    )
    assert response.status_code == 302
    assert b'href="/rank"' in response.data
    # check the comparison has been added
    with equal_weight_app.app_context():
        query = db.select(Comparison).where(Comparison.participant_id == session['participant_id'])
        comparisons = db.session.scalars(query).all()
        assert len(comparisons) == 1
        comparison_id = comparisons[0].comparison_id
    # check the redirect - this is the actual test
    response = equal_weight_client.get(f'/rank?comparison_id={comparison_id}')
    assert response.status_code == 200
    test_string = f'<input type="hidden" id="comparison_id" name="comparison_id" value="{comparison_id}">'.encode(
        'utf-8'
    )  # NoQA
    assert test_string in response.data


@pytest.mark.usefixtures('add_basic_data_equal')
def test_no_hard_stop_below_max_cycles(equal_weight_client, equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights and basic data
    WHEN a logged in participant still has cycles remaining
    THEN they are allowed to continue ranking items
    """
    with equal_weight_client.session_transaction() as session:
        session['participant_id'] = 1
        session['group_ids'] = [1]
        session['weight_conf'] = 'equal'
        session['previous_comparison_id'] = None
        session['comparison_ids'] = []
    max_cycles = WS.get_behaviour_conf(WS.BEHAVIOUR_MAX_CYCLES, equal_weight_app)
    participant = db.session.get(Participant, session['participant_id'])
    participant.completed_cycles = max_cycles - 1
    db.session.commit()
    response = equal_weight_client.get("/rank")
    assert response.status_code == 200
    assert b'Comparison Software: Items Rank' in response.data


@pytest.mark.usefixtures('add_basic_data_equal')
def test_hard_stop_at_max_cycles(equal_weight_client, equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights and basic data
    WHEN a logged in participant tries to continue ranking items after the end of the final permitted cycle
    THEN they are sent to the thank you page and the page does not have a continue button
    """
    with equal_weight_client.session_transaction() as session:
        session['participant_id'] = 1
        session['group_ids'] = [1]
        session['weight_conf'] = 'equal'
        session['previous_comparison_id'] = None
        session['comparison_ids'] = []
    max_cycles = WS.get_behaviour_conf(WS.BEHAVIOUR_MAX_CYCLES, equal_weight_app)
    participant = db.session.get(Participant, session['participant_id'])
    participant.completed_cycles = max_cycles
    db.session.commit()
    response = equal_weight_client.get("/rank", follow_redirects=True)
    assert response.status_code == 200
    assert b'Comparison Software: Thank You' in response.data
    assert b'id="continue_button"' not in response.data


@pytest.mark.usefixtures('add_basic_data_equal')
def test_redirect_at_first_cycle_end(mocker, equal_weight_client, equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights and basic data
    WHEN a logged in participant gets to the end of the first cycle
    THEN they are redirected to the thankyou page and the page has a continue button
    """
    with equal_weight_client.session_transaction() as session:
        session['participant_id'] = 1
        session['group_ids'] = [1]
        session['weight_conf'] = 'equal'
        session['previous_comparison_id'] = None
        session['comparison_ids'] = []
    cycle_length = WS.get_behaviour_conf(WS.BEHAVIOUR_CYCLE_LENGTH, equal_weight_app)
    get_stats = mocker.patch.object(rank.Rank, '_get_comparison_stats')
    get_stats.side_effect = [(cycle_length, 0)]
    participant = db.session.get(Participant, session['participant_id'])
    participant.completed_cycles = 0
    db.session.commit()
    response = equal_weight_client.get("/rank", follow_redirects=True)
    assert response.status_code == 200
    assert b'Comparison Software: Thank You' in response.data
    assert b'id="continue_button"' in response.data


@pytest.mark.usefixtures('add_basic_data_equal')
def test_redirect_after_final_cycle_end(mocker, equal_weight_client, equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights and basic data
    WHEN a logged in participant gets to the end of the final permitted cycle
    THEN they are redirected to the thank you page and the page does not have a continue button
    """
    with equal_weight_client.session_transaction() as session:
        session['participant_id'] = 1
        session['group_ids'] = [1]
        session['weight_conf'] = 'equal'
        session['previous_comparison_id'] = None
        session['comparison_ids'] = []
    max_cycles = WS.get_behaviour_conf(WS.BEHAVIOUR_MAX_CYCLES, equal_weight_app)
    cycle_length = WS.get_behaviour_conf(WS.BEHAVIOUR_CYCLE_LENGTH, equal_weight_app)
    get_stats = mocker.patch.object(rank.Rank, '_get_comparison_stats')
    get_stats.side_effect = [(cycle_length * max_cycles, 0)]
    participant = db.session.get(Participant, session['participant_id'])
    participant.completed_cycles = max_cycles - 1
    db.session.commit()
    response = equal_weight_client.get("/rank", follow_redirects=True)
    assert response.status_code == 200
    assert b'Comparison Software: Thank You' in response.data
    assert b'id="continue_button"' not in response.data


def test_no_escape_route_if_setting_off(mocker, participant_data):
    """
    GIVEN a flask app configured for testing and equal weights and basic data
    WHEN a logged in participant gets to the end of a cycle but the escape route setting is off
    THEN they can continue ranking items with no redirect
    """
    app = execute_setup("../tests/tests_python/test_configurations/config-equal-item-weights-2.json")
    client = app.test_client()
    client.post("/register", data=participant_data)
    with client.session_transaction() as session:
        session['participant_id'] = 1
        session['group_ids'] = [1]
        session['weight_conf'] = 'equal'
        session['previous_comparison_id'] = None
        session['comparison_ids'] = []
    cycle_length = WS.get_behaviour_conf(WS.BEHAVIOUR_CYCLE_LENGTH, app)
    get_stats = mocker.patch.object(rank.Rank, '_get_comparison_stats')
    get_stats.side_effect = [(cycle_length, 0)]
    response = client.get("/rank", follow_redirects=True)
    assert response.status_code == 200
    assert b'Comparison Software: Items Rank' in response.data


@pytest.mark.usefixtures('add_basic_data_equal')
def test_skip_button_if_setting_true(equal_weight_client):
    """
    GIVEN a flask application configured for testing and equal weights and basic data loaded and with the setting for
        allow_skip set to true
    WHEN a participant logs in in and requests the rank page
    THEN the participant sees ranking page and there is a skip button
    """
    with equal_weight_client.session_transaction() as session:
        session['participant_id'] = 1
        session['group_ids'] = [1]
        session['weight_conf'] = 'equal'
        session['previous_comparison_id'] = None
        session['comparison_ids'] = []
    response = equal_weight_client.get("/rank", follow_redirects=True)
    assert response.status_code == 200
    assert b'Comparison Software: Items Rank' in response.data
    assert b'<button id="skip-button"' in response.data


@pytest.mark.usefixtures('add_basic_data_equal')
def test_no_skip_button_if_setting_false(participant_data):
    """
    GIVEN a flask application configured for testing and equal weights and basic data loaded and with the setting for
        allow_skip set to false
    WHEN a participant logs in in and requests the rank page
    THEN the participant sees ranking page but there is no skip button
    """
    app = execute_setup("../tests/tests_python/test_configurations/config-equal-item-weights-2.json")
    client = app.test_client()
    client.post("/register", data=participant_data)
    response = client.get("/rank", follow_redirects=True)
    assert response.status_code == 200
    assert b'Comparison Software: Items Rank' in response.data
    assert b'<button id="skip-button"' not in response.data


@pytest.mark.usefixtures('add_basic_data_equal')
def test_previous_button_if_setting_true(equal_weight_client):
    """
    GIVEN a flask application configured for testing and equal weights and basic data loaded and with the setting for
        allow_back set to true
    WHEN a participant logs in in and requests the rank page
    THEN the participant sees ranking page and there is a previous button
    """
    with equal_weight_client.session_transaction() as session:
        session['participant_id'] = 1
        session['group_ids'] = [1]
        session['weight_conf'] = 'equal'
        session['previous_comparison_id'] = 2
        session['comparison_ids'] = [1, 2]
    response = equal_weight_client.get("/rank", follow_redirects=True)
    assert response.status_code == 200
    assert b'Comparison Software: Items Rank' in response.data
    assert b'<button id="previous-button"' in response.data


@pytest.mark.usefixtures('add_basic_data_equal')
def test_no_previous_button_if_setting_false(participant_data):
    """
    GIVEN a flask application configured for testing and equal weights and basic data loaded and with the setting for
        allow_back set to false
    WHEN a participant logs in in and requests the rank page
    THEN the participant sees ranking page but there is no previous button
    """
    app = execute_setup("../tests/tests_python/test_configurations/config-equal-item-weights-2.json")
    client = app.test_client()
    client.post("/register", data=participant_data)
    with client.session_transaction() as session:
        session['participant_id'] = 1
        session['group_ids'] = [1]
        session['weight_conf'] = 'equal'
        session['previous_comparison_id'] = 2
        session['comparison_ids'] = [1, 2]
    response = client.get("/rank", follow_redirects=True)
    assert response.status_code == 200
    assert b'Comparison Software: Items Rank' in response.data
    assert b'<button id="previous-button"' not in response.data
