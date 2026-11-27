import pytest

from comparison_interface.configuration.website import Settings as WS
from comparison_interface.db.connection import db
from comparison_interface.db.models import Comparison, Participant, TotalItemPair
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
    WHEN a logged in participant with no item preferences is specified accesses the rank page
    THEN an error message is shown because no selections have been made
    """
    with equal_weight_client.session_transaction() as session:
        session['participant_id'] = 2
        session['group_ids'] = [1]
        session['weight_conf'] = 'equal'
        session['previous_comparison_id'] = None
        session['comparison_ids'] = []
        session['study_id'] = 1
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
    app = execute_setup("../tests/test_configurations/config-equal-item-weights-2.json")
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
        # register 2 participants so we can use participant 2 for the test
        equal_weight_client.post("/register", data=participant_data)
        equal_weight_client.post("/register", data=participant_data)
        participant_id = 2
        with equal_weight_client.session_transaction() as session:
            session['participant_id'] = participant_id
            session['group_ids'] = [1]
            session['weight_conf'] = 'equal'
            session['previous_comparison_id'] = None
            session['comparison_ids'] = []
            session['study_id'] = 1
            session['item_ids'] = [1, 2]
        response = equal_weight_client.post(
            "/rank",
            data={
                'action': 'confirmed',
                'item_1_id': 1,
                'item_2_id': 2,
                'selected_item_id': '1',
            },
        )
        assert response.status_code == 302
        assert b'href="/rank"' in response.data

        with equal_weight_client.session_transaction() as session:
            assert session['participant_id'] == participant_id
            session_previous_comparison_id = session['previous_comparison_id']
            session_participant_id = session['participant_id']

        with equal_weight_app.app_context():
            query = db.select(Comparison).where(Comparison.participant_id == participant_id)
            comparisons = db.session.scalars(query).all()
            assert len(comparisons) == 1
            comp = comparisons[0]
            assert comp.comparison_id == session_previous_comparison_id
            assert comp.participant_id == session_participant_id
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
        participant_id = 1
        with equal_weight_client.session_transaction() as session:
            session['participant_id'] = participant_id
            session['group_ids'] = [1]
            session['weight_conf'] = 'equal'
            session['previous_comparison_id'] = None
            session['comparison_ids'] = []
            session['study_id'] = 1
            session['item_ids'] = [1, 2]
        response = equal_weight_client.post(
            "/rank",
            data={
                'action': 'skipped',
                'item_1_id': '1',
                'item_2_id': '2',
                'selected_item_id': '',
            },
        )
        assert response.status_code == 302
        assert b'href="/rank"' in response.data

        with equal_weight_client.session_transaction() as session:
            session_previous_comparison_id = session['previous_comparison_id']
            session_participant_id = session['participant_id']

        with equal_weight_app.app_context():
            query = db.select(Comparison).where(Comparison.participant_id == participant_id)
            comparisons = db.session.scalars(query).all()
            assert len(comparisons) == 1
            comp = comparisons[0]
            assert comp.comparison_id == session_previous_comparison_id
            assert comp.participant_id == session_participant_id
            assert comp.selected_item_id is None
            assert comp.state == 'skipped'
            assert comp.item_1_id == 1
            assert comp.item_2_id == 2


@pytest.mark.usefixtures('add_basic_data_totals')
def test_register_selected_rank_comparison_weighted_totals(custom_totals_client, custom_totals_app, participant_data):
    """
    GIVEN a flask app configured for testing and custom totals
    WHEN a 'selected' ranking decision is posted to the rank url
    THEN the data is stored in the database, the pair is marked as judged and the participant redirected to another
      rank page
    """
    with custom_totals_client:
        custom_totals_client.post("/register", data=participant_data)
        participant_id = 1
        with custom_totals_client.session_transaction() as session:
            session['participant_id'] = participant_id
            session['group_ids'] = [1]
            session['weight_conf'] = 'weighted-total'
            session['previous_comparison_id'] = None
            session['comparison_ids'] = []
            session['study_id'] = 1
            session['item_ids'] = [1, 2]
        data = {
            'action': 'confirmed',
            'item_1_id': '1',
            'item_2_id': '2',
            'selected_item_id': '1',
            'weighted_pair_id': 1,
        }
        # check the pair is set to false
        with custom_totals_app.app_context():
            query = db.select(TotalItemPair).where(TotalItemPair.custom_item_pair_id == data['weighted_pair_id'])
            pair = db.session.scalars(query).all()
            assert pair[0].custom_item_pair_id == data['weighted_pair_id']
            assert pair[0].judged is False

        response = custom_totals_client.post("/rank", data=data)
        assert response.status_code == 302
        assert b'href="/rank"' in response.data

        with custom_totals_client.session_transaction() as session:
            session_previous_comparison_id = session['previous_comparison_id']
            session_participant_id = session['participant_id']

        with custom_totals_app.app_context():
            query = db.select(Comparison).where(Comparison.participant_id == participant_id)
            comparisons = db.session.scalars(query).all()
            assert len(comparisons) == 1
            comp = comparisons[0]
            assert comp.comparison_id == session_previous_comparison_id
            assert comp.participant_id == session_participant_id
            assert comp.selected_item_id == 1
            assert comp.state == 'selected'
            assert comp.item_1_id == 1
            assert comp.item_2_id == 2
            # now check we set it to true
            query = db.select(TotalItemPair).where(TotalItemPair.custom_item_pair_id == data['weighted_pair_id'])
            pair = db.session.scalars(query).all()
            assert pair[0].custom_item_pair_id == data['weighted_pair_id']
            assert pair[0].judged is True


@pytest.mark.usefixtures('add_basic_data_totals')
def test_register_skipped_rank_comparison_weighted_total(custom_totals_client, custom_totals_app, participant_data):
    """
    GIVEN a flask app configured for testing and custom totals
    WHEN a 'skipped' ranking decision is posted to the rank url
    THEN the data is stored in the database and the participant redirected to another rank page but the pair is marked
        as judged
    """
    with custom_totals_client:
        custom_totals_client.post("/register", data=participant_data)
        participant_id = 1
        with custom_totals_client.session_transaction() as session:
            session['participant_id'] = participant_id
            session['group_ids'] = [1]
            session['weight_conf'] = 'weighted-total'
            session['previous_comparison_id'] = None
            session['comparison_ids'] = []
            session['study_id'] = 1
            session['item_ids'] = [1, 2]
        data = {
            'action': 'skipped',
            'item_1_id': '1',
            'item_2_id': '2',
            'weighted_pair_id': 1,
            'selected_item_id': '',
        }

        # check the pair is set to false
        with custom_totals_app.app_context():
            query = db.select(TotalItemPair).where(TotalItemPair.custom_item_pair_id == data['weighted_pair_id'])
            pair = db.session.scalars(query).all()
            assert pair[0].custom_item_pair_id == data['weighted_pair_id']
            assert pair[0].judged is False

        response = custom_totals_client.post("/rank", data=data)
        assert response.status_code == 302
        assert b'href="/rank"' in response.data

        with custom_totals_client.session_transaction() as session:
            session_previous_comparison_id = session['previous_comparison_id']
            session_participant_id = session['participant_id']

        with custom_totals_app.app_context():
            query = db.select(Comparison).where(Comparison.participant_id == participant_id)
            comparisons = db.session.scalars(query).all()
            assert len(comparisons) == 1
            comp = comparisons[0]
            assert comp.comparison_id == session_previous_comparison_id
            assert comp.participant_id == session_participant_id
            assert comp.selected_item_id is None
            assert comp.state == 'skipped'
            assert comp.item_1_id == 1
            assert comp.item_2_id == 2
            # now check it is still to false
            query = db.select(TotalItemPair).where(TotalItemPair.custom_item_pair_id == data['weighted_pair_id'])
            pair = db.session.scalars(query).all()
            assert pair[0].custom_item_pair_id == data['weighted_pair_id']
            assert pair[0].judged is False


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
                'action': 'confirmed',
                'item_1_id': '1',
                'item_2_id': '2',
                'selected_item_id': '1',
            },
        )


@pytest.mark.usefixtures('add_basic_data_equal')
def test_requesting_a_previous_comparison_get(equal_weight_app, equal_weight_client):
    """
    GIVEN a flask app configured for testing and equal weights with basic data added
    WHEN a logged in participant has been redirected from the post request to rejudge a comparison
    THEN they see the requested comparison
    """
    selected_item_id = 1
    with equal_weight_client.session_transaction() as session:
        session['participant_id'] = 1
        session['group_ids'] = [1]
        session['item_ids'] = [1, 2]
        session['weight_conf'] = 'equal'
        session['previous_comparison_id'] = None
        session['comparison_ids'] = []
        session['study_id'] = 1
    # first add a comparison to retrieve later
    response = equal_weight_client.post(
        "/rank",
        data={
            'action': 'confirmed',
            'item_1_id': '1',
            'item_2_id': '2',
            'selected_item_id': selected_item_id,
        },
    )
    assert response.status_code == 302
    assert b'href="/rank"' in response.data
    # check the comparison has been added
    with equal_weight_app.app_context():
        query = db.select(Comparison).where(Comparison.participant_id == session['participant_id'])
        comparisons = db.session.scalars(query).all()
        assert len(comparisons) == 1
    # check the previous item is loaded
    response = equal_weight_client.post('/rank/previous')
    assert response.status_code == 200
    test_string_1 = 'data-initial-state="selected"'.encode('utf-8')
    test_string_2 = f'data-initial-selected-item-id="{selected_item_id}"'.encode('utf-8')
    assert test_string_1 in response.data
    assert test_string_2 in response.data
    # check the session has recorded the id correctly
    with equal_weight_client.session_transaction() as session:
        assert session['current_comparison'] == selected_item_id


@pytest.mark.usefixtures('add_basic_data_equal')
def test_requesting_a_previous_comparison_post(equal_weight_app, equal_weight_client):
    """
    GIVEN a flask app configured for testing and equal weights
    WHEN a logged in participant requests to rejudge a comparison and posts a changed decision
    THEN that decision is correctly saved to the database
    """
    selected_item_id = 1
    with equal_weight_client.session_transaction() as session:
        session['participant_id'] = 1
        session['group_ids'] = [1]
        session['weight_conf'] = 'equal'
        session['previous_comparison_id'] = None
        session['comparison_ids'] = []
        session['study_id'] = 1
        session['item_ids'] = [1, 2]
    # first add a comparison
    response = equal_weight_client.post(
        "/rank",
        data={
            'action': 'confirmed',
            'item_1_id': '1',
            'item_2_id': '2',
            'selected_item_id': selected_item_id,
        },
    )
    assert response.status_code == 302
    assert b'href="/rank"' in response.data
    # get the id added
    with equal_weight_app.app_context():
        query = db.select(Comparison).where(Comparison.participant_id == session['participant_id'])
        comparisons = db.session.scalars(query).all()
        assert len(comparisons) == 1
        assert comparisons[0].selected_item_id == selected_item_id
        comparison_id = comparisons[0].comparison_id
    # set up the session so that it looks like we are rejudging
    with equal_weight_client.session_transaction() as session:
        session['current_comparison'] = comparison_id

    new_selected_item_id = 2
    # check the post saved to the current comparison
    response = equal_weight_client.post("/rank", data={'action': 'confirmed', 'selected_item_id': new_selected_item_id})
    with equal_weight_app.app_context():
        query = db.select(Comparison).where(Comparison.participant_id == session['participant_id'])
        comparisons = db.session.scalars(query).all()
        assert len(comparisons) == 1
        assert comparisons[0].selected_item_id == new_selected_item_id
        assert comparisons[0].comparison_id == comparison_id


@pytest.mark.usefixtures('add_basic_data_equal')
def test_get_to_previous_url_is_redirected(equal_weight_app, equal_weight_client):
    """
    GIVEN a flask app configured for testing and equal weights
    WHEN a logged in participant reloads a page using /rank/previous (a GET)
    THEN then they are redirected to the /rank url and a new comparison
    """
    selected_item_id = 1
    with equal_weight_client.session_transaction() as session:
        session['participant_id'] = 1
        session['group_ids'] = [1]
        session['weight_conf'] = 'equal'
        session['previous_comparison_id'] = None
        session['comparison_ids'] = []
        session['study_id'] = 1
        session['item_ids'] = [1, 2]
    # first add a comparison
    equal_weight_client.post(
        "/rank",
        data={
            'action': 'confirmed',
            'item_1_id': '1',
            'item_2_id': '2',
            'selected_item_id': selected_item_id,
        },
    )
    # get the id added
    with equal_weight_app.app_context():
        query = db.select(Comparison).where(Comparison.participant_id == session['participant_id'])
        comparisons = db.session.scalars(query).all()
        assert len(comparisons) == 1
        assert comparisons[0].selected_item_id == selected_item_id
        comparison_id = comparisons[0].comparison_id
    # set up the session so that it looks like we are rejudging
    with equal_weight_client.session_transaction() as session:
        session['current_comparison'] = comparison_id
    # load the page with the post as expected
    response = equal_weight_client.post('/rank/previous')
    assert response.status_code == 200
    test_string_1 = 'data-initial-state="selected"'.encode('utf-8')
    test_string_2 = f'data-initial-selected-item-id="{selected_item_id}"'.encode('utf-8')
    assert test_string_1 in response.data
    assert test_string_2 in response.data
    # now mimic reload with a get
    response = equal_weight_client.get('/rank/previous')
    assert response.status_code == 302
    assert '<a href="/rank">'.encode('utf-8') in response.data


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
        session['study_id'] = 1
        session['item_ids'] = [1, 2]
    # TODO: unhardocde study_id
    max_cycles = WS.get_study_conf(WS.BEHAVIOUR_MAX_CYCLES, 1, equal_weight_app)
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
        session['study_id'] = 1
        session['item_ids'] = [1, 2]
    # TODO: unhardcode study id
    max_cycles = WS.get_study_conf(WS.BEHAVIOUR_MAX_CYCLES, 1, equal_weight_app)
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
        session['study_id'] = 1
    # TODO: unhardcode study id
    cycle_length = WS.get_study_conf(WS.BEHAVIOUR_CYCLE_LENGTH, 1, equal_weight_app)
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
        session['study_id'] = 1
    # TODO: unhardcode study id
    max_cycles = WS.get_study_conf(WS.BEHAVIOUR_MAX_CYCLES, 1, equal_weight_app)
    cycle_length = WS.get_study_conf(WS.BEHAVIOUR_CYCLE_LENGTH, 1, equal_weight_app)
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
    app = execute_setup("../tests/test_configurations/config-equal-item-weights-2.json")
    client = app.test_client()
    client.post("/register", data=participant_data)
    with client.session_transaction() as session:
        session['participant_id'] = 1
        session['group_ids'] = [1]
        session['weight_conf'] = 'equal'
        session['previous_comparison_id'] = None
        session['comparison_ids'] = []
        session['study_id'] = 1
    cycle_length = WS.get_study_conf(WS.BEHAVIOUR_CYCLE_LENGTH, 1, app)
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
        session['study_id'] = 1
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
    app = execute_setup("../tests/test_configurations/config-equal-item-weights-2.json")
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
        session['study_id'] = 1
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
    app = execute_setup("../tests/test_configurations/config-equal-item-weights-2.json")
    client = app.test_client()
    client.post("/register", data=participant_data)
    with client.session_transaction() as session:
        session['participant_id'] = 1
        session['group_ids'] = [1]
        session['weight_conf'] = 'equal'
        session['previous_comparison_id'] = 2
        session['comparison_ids'] = [1, 2]
        session['study_id'] = 1
    response = client.get("/rank", follow_redirects=True)
    assert response.status_code == 200
    assert b'Comparison Software: Items Rank' in response.data
    assert b'<button id="previous-button"' not in response.data
