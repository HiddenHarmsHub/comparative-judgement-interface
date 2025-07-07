from datetime import datetime, timezone

import pytest
from numpy import random
from sqlalchemy import MetaData, text
from sqlalchemy.exc import SQLAlchemyError

from comparison_interface.main.db.connection import db
from comparison_interface.main.db.models import Comparison, Group, Item, ItemGroup, UserGroup
from comparison_interface.main.views import rank
from comparison_interface.main.views.register import Request


@pytest.mark.usefixtures('equal_weight_app', 'add_basic_data_equal')
def test_equal_data_setup():
    """
    GIVEN a flask app configured for testing and equal weights
    WHEN the add_basic_data_equal fixture is also used
    THEN the fixture data is added correctly
    """

    user_sql = 'SELECT * FROM "user"'
    users = db.session.execute(text(user_sql)).all()
    assert len(users) == 2

    user_group_sql = 'SELECT * FROM "user_group"'
    user_groups = db.session.execute(text(user_group_sql)).all()
    assert len(user_groups) == 2

    user_item_sql = 'SELECT * FROM "user_item"'
    user_items = db.session.execute(text(user_item_sql)).all()
    assert len(user_items) == 10


def test_item_retrieval_function_choice_with_id(mocker, equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights
    WHEN a specific existing decision is requested by id
    THEN the correct function runs
    """
    request = Request(equal_weight_app, {})
    request._session['user_id'] = 1
    request._session['group_ids'] = [1]
    request._session['weight_conf'] = 'equal'
    request._session['previous_comparison_id'] = None
    request._session['comparison_ids'] = []
    ranker = rank.Rank(request, request._session)
    should_render = mocker.patch.object(rank.WS, 'should_render')
    should_render.side_effect = [True]
    comparison_function = mocker.patch.object(rank.Rank, '_get_comparison_items')
    ranker._get_items_to_compare(comparison_id=2)
    comparison_function.assert_called_once_with(2)


def test_item_retrieval_function_choice_with_custom_weights(mocker, custom_weight_app):
    """
    GIVEN a flask app configured for testing and custom weights
    WHEN a comparison pair is requested
    THEN the correct function runs
    """
    request = Request(custom_weight_app, {})
    request._session['user_id'] = 1
    request._session['group_ids'] = [1]
    request._session['weight_conf'] = 'manual'
    request._session['previous_comparison_id'] = None
    request._session['comparison_ids'] = []
    ranker = rank.Rank(request, request._session)
    should_render = mocker.patch.object(rank.WS, 'should_render')
    should_render.side_effect = [True]
    comparison_function = mocker.patch.object(rank.Rank, '_get_custom_items')
    ranker._get_items_to_compare()
    comparison_function.assert_called_once_with()


def test_item_retrieval_function_choice_with_preference(mocker, equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights
    WHEN a comparison pair is requested
    THEN the correct function runs
    """
    request = Request(equal_weight_app, {})
    request._session['user_id'] = 1
    request._session['group_ids'] = [1]
    request._session['weight_conf'] = 'equal'
    request._session['previous_comparison_id'] = None
    request._session['comparison_ids'] = []
    ranker = rank.Rank(request, request._session)
    should_render = mocker.patch.object(rank.WS, 'should_render')
    should_render.side_effect = [True]
    comparison_function = mocker.patch.object(rank.Rank, '_get_preferred_items')
    ranker._get_items_to_compare()
    comparison_function.assert_called_once_with()


def test_item_retrieval_function_choice_without_preference(mocker, equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights
    WHEN a comparison pair is requested
    THEN the correct function runs
    """
    request = Request(equal_weight_app, {})
    request._session['user_id'] = 1
    request._session['group_ids'] = [1]
    request._session['weight_conf'] = 'equal'
    request._session['previous_comparison_id'] = None
    request._session['comparison_ids'] = []
    ranker = rank.Rank(request, request._session)
    should_render = mocker.patch.object(rank.WS, 'should_render')
    should_render.side_effect = [False]
    comparison_function = mocker.patch.object(rank.Rank, '_get_random_items')
    ranker._get_items_to_compare()
    comparison_function.assert_called_once_with()


def test_item_retrieval_function_choice_with_unrecognised_setting(mocker, equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights
    WHEN a comparison pair is requested but the session has an unrecognised weight_conf setting
    THEN two None values are returned
    """
    request = Request(equal_weight_app, {})
    request._session['user_id'] = 1
    request._session['group_ids'] = [1]
    request._session['weight_conf'] = 'wrong_setting'
    request._session['previous_comparison_id'] = None
    request._session['comparison_ids'] = []
    ranker = rank.Rank(request, request._session)
    should_render = mocker.patch.object(rank.WS, 'should_render')
    should_render.side_effect = [False]
    result = ranker._get_items_to_compare()
    assert result == (None, None)


@pytest.mark.usefixtures('add_basic_data_equal')
def test_get_comparison_items_normal_order(equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights
    WHEN the items from a previous decision are requested
    THEN the correct items are returned in the correct order
    """
    # add some decisions to retrieve
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

    request = Request(equal_weight_app, {})
    request._session['user_id'] = 1
    request._session['group_ids'] = [1]
    request._session['weight_conf'] = 'equal'
    request._session['previous_comparison_id'] = 1
    request._session['comparison_ids'] = [1, 2]
    ranker = rank.Rank(request, request._session)
    items = ranker._get_comparison_items(1)
    assert items[0].item_id == 1
    assert items[1].item_id == 2


@pytest.mark.usefixtures('add_basic_data_equal')
def test_get_comparison_items_different_order(equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights
    WHEN the items from a previous decision are requested
    THEN the correct items are returned in the correct order
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

    request = Request(equal_weight_app, {})
    request._session['user_id'] = 1
    request._session['group_ids'] = [1]
    request._session['weight_conf'] = 'equal'
    request._session['previous_comparison_id'] = 1
    request._session['comparison_ids'] = [1, 2]
    ranker = rank.Rank(request, request._session)
    items = ranker._get_comparison_items(2)
    assert items[0].item_id == 4
    assert items[1].item_id == 3


@pytest.mark.usefixtures('add_basic_data_equal')
def test_get_comparison_items_invalid_id(equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights
    WHEN the items from a previous decision are requested but the requested comparison id is not in the database
    THEN an error is raised
    """
    # add some decisions to retrieve
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

    with pytest.raises(Exception):
        request = Request(equal_weight_app, {})
        request._session['user_id'] = 1
        request._session['group_ids'] = [1]
        request._session['weight_conf'] = 'equal'
        request._session['previous_comparison_id'] = 1
        request._session['comparison_ids'] = [1, 2]
        ranker = rank.Rank(request, request._session)
        ranker._get_comparison_items(3)


def test_calculate_comparison_state_tied(equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights
    WHEN a comparison state is requested with the action 'confirmed' and no selected_item_id
    THEN the correct details are returned
    """
    request = Request(equal_weight_app, {})
    request._session['user_id'] = 1
    request._session['group_ids'] = [1]
    request._session['weight_conf'] = 'equal'
    request._session['previous_comparison_id'] = 1
    request._session['comparison_ids'] = [1, 2]
    ranker = rank.Rank(request, request._session)
    response = {}
    result = ranker._calculate_comparison_state('confirmed', response)
    assert result[0] == 'tied'
    assert result[1] is None


def test_calculate_comparison_state_selected(equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights
    WHEN a comparison state is requested with the action 'confirmed' and with a selected_item_id
    THEN the correct details are returned
    """
    request = Request(equal_weight_app, {})
    request._session['user_id'] = 1
    request._session['group_ids'] = [1]
    request._session['weight_conf'] = 'equal'
    request._session['previous_comparison_id'] = 1
    request._session['comparison_ids'] = [1, 2]
    ranker = rank.Rank(request, request._session)
    response = {'selected_item_id': 1}
    result = ranker._calculate_comparison_state('confirmed', response)
    assert result[0] == 'selected'
    assert result[1] == 1


def test_calculate_comparison_state_skipped(equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights
    WHEN a comparison state is requested with the action 'skipped'
    THEN the correct details are returned
    """
    request = Request(equal_weight_app, {})
    request._session['user_id'] = 1
    request._session['group_ids'] = [1]
    request._session['weight_conf'] = 'equal'
    request._session['previous_comparison_id'] = 1
    request._session['comparison_ids'] = [1, 2]
    ranker = rank.Rank(request, request._session)
    response = {}
    result = ranker._calculate_comparison_state('skipped', response)
    assert result[0] == 'skipped'
    assert result[1] is None


@pytest.mark.usefixtures('add_basic_data_equal')
def test_increment_cycle_count(equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights and with basic data added
    WHEN a user is logged in and the _increment_cycle_count function is called
    THEN the cycle count for the logged in user is incremented by 1
    """
    request = Request(equal_weight_app, {})
    request._session['user_id'] = 1
    request._session['group_ids'] = [1]
    request._session['weight_conf'] = 'equal'
    request._session['previous_comparison_id'] = 1
    request._session['comparison_ids'] = [1, 2]
    ranker = rank.Rank(request, request._session)
    starting_cycle = ranker._get_current_cycle()
    ranker._increment_cycle_count()
    new_cycle_count = ranker._get_current_cycle()
    assert new_cycle_count == starting_cycle + 1
    # repeat to check we keep incrementing
    ranker._increment_cycle_count()
    new_cycle_count = ranker._get_current_cycle()
    assert new_cycle_count == starting_cycle + 2


@pytest.mark.usefixtures('add_basic_data_equal')
def test_comparison_stats_retrieval(equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights and with some comparisons made
    WHEN the comparison stats are requested
    THEN the correct figures are returned
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
            'item_1_id': 1,
            'item_2_id': 2,
            'selected_item_id': 1,
            'state': 'selected',
            'created': datetime.now(timezone.utc),
            'updated': datetime.now(timezone.utc),
        },
        {
            'user_id': 1,
            'item_1_id': 1,
            'item_2_id': 3,
            'selected_item_id': 3,
            'state': 'selected',
            'created': datetime.now(timezone.utc),
            'updated': datetime.now(timezone.utc),
        },
        {
            'user_id': 1,
            'item_1_id': 2,
            'item_2_id': 4,
            'selected_item_id': 2,
            'state': 'selected',
            'created': datetime.now(timezone.utc),
            'updated': datetime.now(timezone.utc),
        },
        {
            'user_id': 1,
            'item_1_id': 4,
            'item_2_id': 3,
            'selected_item_id': None,
            'state': 'tied',
            'created': datetime.now(timezone.utc),
            'updated': datetime.now(timezone.utc),
        },
        {
            'user_id': 1,
            'item_1_id': 4,
            'item_2_id': 3,
            'selected_item_id': None,
            'state': 'tied',
            'created': datetime.now(timezone.utc),
            'updated': datetime.now(timezone.utc),
        },
        {
            'user_id': 1,
            'item_1_id': 2,
            'item_2_id': 7,
            'selected_item_id': 2,
            'state': 'selected',
            'created': datetime.now(timezone.utc),
            'updated': datetime.now(timezone.utc),
        },
        {
            'user_id': 1,
            'item_1_id': 4,
            'item_2_id': 3,
            'selected_item_id': 3,
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
            'item_1_id': 4,
            'item_2_id': 6,
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

    request = Request(equal_weight_app, {})
    request._session['user_id'] = 1
    request._session['group_ids'] = [1]
    request._session['weight_conf'] = 'equal'
    request._session['previous_comparison_id'] = 1
    request._session['comparison_ids'] = [1, 2]
    ranker = rank.Rank(request, request._session)
    counts = ranker._get_comparison_stats()
    assert counts[0] == 8
    assert counts[1] == 3


@pytest.mark.usefixtures('add_basic_data_equal')
def test_comparison_stats_retrieval_no_data(equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights and no comparisons have been made
    WHEN the comparison stats are requested
    THEN the correct figures are returned
    """
    request = Request(equal_weight_app, {})
    request._session['user_id'] = 1
    request._session['group_ids'] = [1]
    request._session['weight_conf'] = 'equal'
    request._session['previous_comparison_id'] = 1
    request._session['comparison_ids'] = [1, 2]
    ranker = rank.Rank(request, request._session)
    counts = ranker._get_comparison_stats()
    assert counts[0] == 0
    assert counts[1] == 0


@pytest.mark.usefixtures('add_basic_data_custom')
def test_custom_item_retrieval(mocker, custom_weight_app):
    """
    GIVEN a flask app configured for testing and custom weights and with basic data added for user and group preference
    WHEN a user has an active session specifying a group_id and _get_custom_items is called
    THEN the correct group ids and weightings are supplied to the random generator function and two items are returned
    """
    request = Request(custom_weight_app, {})
    request._session['user_id'] = 1
    request._session['group_ids'] = [2]
    request._session['weight_conf'] = 'equal'
    request._session['previous_comparison_id'] = None
    request._session['comparison_ids'] = []
    ranker = rank.Rank(request, request._session)
    mock_rng = mocker.Mock(spec=random.Generator)
    custom_weight_app.rng = mock_rng
    ranker._app = custom_weight_app
    mock_rng.choice.return_value = [4, 8]
    ranker._get_custom_items()
    # check that we feed the correct data to the random item generator
    mock_rng.choice.assert_called_once_with([4, 5, 6, 7, 8, 9], 1, p=[0.1, 0.2, 0.2, 0.3, 0.1, 0.1], replace=False)


@pytest.mark.usefixtures('add_basic_data_equal')
def test_preferred_item_retrieval(mocker, equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights and with basic data added including item preferences
    WHEN a user has an active session specifying a group_id and _get_preferred_items is called
    THEN only items that are known are selected for comparison
    """
    request = Request(equal_weight_app, {})
    request._session['user_id'] = 1
    request._session['group_ids'] = [1]
    request._session['weight_conf'] = 'equal'
    request._session['previous_comparison_id'] = None
    request._session['comparison_ids'] = []
    ranker = rank.Rank(request, request._session)
    mock_rng = mocker.Mock(spec=random.Generator)
    equal_weight_app.rng = mock_rng
    ranker._app = equal_weight_app
    mock_rng.choice.return_value = [1, 8]
    ranker._get_preferred_items()
    # check that we feed the correct data to the random item generator
    mock_rng.choice.assert_called_once_with([1, 2, 3, 7, 8, 9], 2, replace=False)


@pytest.mark.usefixtures('add_basic_data_equal')
def test_preferred_item_retrieval_not_enough_items(equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights with basic data added including a single item preference
    WHEN a user has an active session specifying a group_id and _get_preferred_items is called
    THEN no items are returned for comparison because there is only one to choose from
    """
    request = Request(equal_weight_app, {})
    request._session['user_id'] = 2
    request._session['group_ids'] = [1]
    request._session['weight_conf'] = 'equal'
    request._session['previous_comparison_id'] = None
    request._session['comparison_ids'] = []
    ranker = rank.Rank(request, request._session)
    items = ranker._get_preferred_items()
    # check that we get two items returned from the range
    assert len(items) == 2
    assert items[0] is None
    assert items[1] is None


@pytest.mark.usefixtures('add_basic_data_equal')
def test_random_item_retrieval(mocker, equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights and with basic data added including item preferences
    WHEN a user has an active session specifying a group_id and _get_random_items is called
    THEN only items in the chosen group are selected for comparison

    In reality this function would never be called with the settings of this setup but the
    function can still be unit tested with these settings.
    """
    request = Request(equal_weight_app, {})
    request._session['user_id'] = 1
    request._session['group_ids'] = [1]
    request._session['weight_conf'] = 'equal'
    request._session['previous_comparison_id'] = None
    request._session['comparison_ids'] = []
    ranker = rank.Rank(request, request._session)
    mock_rng = mocker.Mock(spec=random.Generator)
    equal_weight_app.rng = mock_rng
    ranker._app = equal_weight_app
    mock_rng.choice.return_value = [1, 8]
    ranker._get_random_items()
    # check that we feed the correct data to the random item generator
    mock_rng.choice.assert_called_once_with([1, 2, 3, 4, 5, 6, 7, 8, 9], 2, replace=False)


@pytest.mark.usefixtures('add_basic_data_equal')
def test_random_item_retrieval_only_one_item(equal_weight_app):
    """
    GIVEN a flask app configured for testing and equal weights and with basic data and an additional project with only
        one item
    WHEN a user has an active session specfiying the group_id that only has one item
    THEN instead of items two None's are returned
    """
    # First add an extra set of data for the project that only has one item
    group_data = {
        'name': 'test_group',
        'display_name': 'Test Group',
        'created_date': datetime.now(timezone.utc),
    }
    group = Group(**group_data)
    db.session.add(group)
    item_data = {
        'name': 'item_name',
        'display_name': 'Item Name',
        'image_path': 'image.png',
        'created_date': datetime.now(timezone.utc),
    }
    item = Item(**item_data)
    db.session.add(item)
    db.session.commit()
    group_item = ItemGroup(group_id=3, item_id=13, created_date=datetime.now(timezone.utc))
    db.session.add(group_item)
    db.session.commit()
    # now add the user to access this group
    user_data = {
        'name': 'Tester Two',
        'country': 'England',
        'allergies': 'Yes',
        'age': '30',
        'accepted_ethics_agreement': '1',
    }
    user_data['created_date'] = datetime.now(timezone.utc)
    db_engine = db.engines[None]
    db_meta = MetaData()
    db_meta.reflect(bind=db_engine)
    table = db_meta.tables["user"]
    new_user_sql = table.insert().values(**user_data)
    try:
        # Insert the user into the database
        with db.engine.begin() as connection:
            result = connection.execute(new_user_sql)
        id = result.lastrowid
    except SQLAlchemyError as e:
        raise RuntimeError(str(e))
    db.session.commit
    # insert the group preferences for the user (assumes groups are always added the same way)
    user_group_data = {
        'user_id': id,
        'group_id': 3,
        'created_date': datetime.now(timezone.utc),
    }
    user_group = UserGroup(**user_group_data)
    db.session.add(user_group)
    db.session.commit()

    request = Request(equal_weight_app, {})
    request._session['user_id'] = id
    request._session['group_ids'] = [3]
    request._session['weight_conf'] = 'equal'
    request._session['previous_comparison_id'] = None
    request._session['comparison_ids'] = []
    ranker = rank.Rank(request, request._session)
    items = ranker._get_random_items()
    # check that we get two None entries because there is only 1
    assert len(items) == 2
    assert items[0] is None
    assert items[1] is None
