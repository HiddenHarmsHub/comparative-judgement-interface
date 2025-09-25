import pytest
from marshmallow import ValidationError

from comparison_interface.configuration.schema import BehaviourConfiguration, Group, Weight


def test_empty_weight_schema_raises_error():
    """
    GIVEN an empty JSON object
    WHEN that object is validated with the weight schema
    THEN a Validation Error is raised
    """
    test_schema = {}
    with pytest.raises(ValidationError) as err:
        weight_schema = Weight()
        weight_schema.load(test_schema)
    assert len(err.value.messages_dict.keys()) == 3


def test_behaviour_configuration_for_escape_route_false():
    """
    GIVEN a behaviour chunk of a JSON schema which has the escape root set to False
    WHEN the behaviour chunk is validated using the BehaviourConfiguration
    THEN no error is raised
    """
    test_behaviour_schema = {
        "exportPathLocation": "exports",
        "renderUserItemPreferencePage": False,
        "renderUserInstructionPage": False,
        "renderEthicsAgreementPage": False,
        "renderSitePoliciesPage": False,
        "renderCookieBanner": False,
        "offerEscapeRouteBetweenCycles": False,
        "allowTies": False,
        "allowSkip": True,
        "allowBack": True,
    }
    behaviour_schema = BehaviourConfiguration()
    try:
        behaviour_schema.load(test_behaviour_schema)
    except ValidationError as err:
        assert False, f'ValidationError raised: {err}'


def test_behaviour_configuration_for_escape_route_true_with_all_requirements():
    """
    GIVEN a behaviour chunk of a JSON schema which is has the escape root set to True and all other required keys
    WHEN the behaviour chunk is validated using the BehaviourConfiguration
    THEN no error is raised
    """
    test_behaviour_schema = {
        "exportPathLocation": "exports",
        "renderUserItemPreferencePage": False,
        "renderUserInstructionPage": False,
        "renderEthicsAgreementPage": False,
        "renderSitePoliciesPage": False,
        "renderCookieBanner": False,
        "offerEscapeRouteBetweenCycles": True,
        "cycleLength": 30,
        "maximumCyclesPerUser": 3,
        "allowTies": False,
        "allowSkip": True,
        "allowBack": True,
    }
    behaviour_schema = BehaviourConfiguration()
    try:
        behaviour_schema.load(test_behaviour_schema)
    except ValidationError as err:
        assert False, f'ValidationError raised: {err}'


def test_behaviour_configuration_for_escape_route_true_with_missing_requirements():
    """
    GIVEN a behaviour chunk of a JSON schema which is has the escape root set to True and is missing the required keys
    WHEN the behaviour chunk is validated using the BehaviourConfiguration
    THEN a Validation Error is raised
    """
    test_behaviour_schema = {
        "exportPathLocation": "exports",
        "renderUserItemPreferencePage": False,
        "renderUserInstructionPage": False,
        "renderEthicsAgreementPage": False,
        "renderSitePoliciesPage": False,
        "renderCookieBanner": False,
        "offerEscapeRouteBetweenCycles": True,
        "cycleLength": 30,
        "allowTies": False,
        "allowSkip": True,
        "allowBack": True,
    }
    with pytest.raises(ValidationError) as err:
        behaviour_schema = BehaviourConfiguration()
        behaviour_schema.load(test_behaviour_schema)
    assert len(err.value.messages_dict.keys()) == 1


def test_group_configuration_with_inconsistent_item_ids():
    """
    GIVEN an group chunk of a JSON schema with some items containing ids
    WHEN the group chunk is validated using the Group schema class
    THEN a Validation Error is raised
    """
    test_group_schema = {
        "name": "group1",
        "displayName": "Group 1",
        "items": [
            {"name": "north_east", "displayName": "North East", "imageName": "item_1.png"},
            {"id": 1, "name": "north_west", "displayName": "North West", "imageName": "item_2.png"},
        ],
    }
    with pytest.raises(ValidationError):
        group_schema = Group()
        group_schema.load(test_group_schema)
