from comparison_interface.main.views import register
from comparison_interface.main.views.request import Request


def test_load_user_component(mocker, equal_weight_app):
    """
    GIVEN a flask app configured for testing and with equal weights
    WHEN the user components are requested
    THEN the correct number of templated items is returned
    """
    with equal_weight_app.app_context():
        user_components = []
        request = Request(equal_weight_app, {})
        reg = register.Register(request, request._session)
        get_user_conf = mocker.patch.object(register.WS, 'get_user_conf')
        get_user_conf.side_effect = [
            [
                {"name": "name", "displayName": "First Name", "type": "text", "maxLimit": 250, "required": True},
                {
                    "name": "country",
                    "displayName": "In which country do you live?",
                    "type": "radio",
                    "option": ["England", "Northern Ireland", "Scotland", "Wales", "Outside the UK"],
                    "required": True,
                },
            ]
        ]
        reg._load_user_component(user_components)
        assert len(user_components) == 2
