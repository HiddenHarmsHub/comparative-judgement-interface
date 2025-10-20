from comparison_interface.configuration.website import Settings


def test_set_configuration_location(equal_weight_app):
    """
    GIVEN a flask app configured for testing and with equal weights
    WHEN the configuration location is set
    THEN the configuration file location is set and the configuration in memory is set to None
    """
    settings = Settings()
    settings.set_configuration_location(equal_weight_app, 'test_location.json')
    location = equal_weight_app.config[settings.CONFIGURATION_LOCATION]
    configuration = settings.configuration
    assert location == 'test_location.json'
    assert configuration is None


def test_get_configuration_location(equal_weight_app):
    """
    GIVEN a flask app configured for testing and with equal weights
    WHEN the configuration location is requested
    THEN the configuration location is returned
    """
    settings = Settings()
    location = settings.get_configuration_location(equal_weight_app)
    split_location = location.split('/')
    assert split_location[-1] == 'config-equal-item-weights.json'


def test_website_get_text(equal_weight_app):
    """
    GIVEN a flask app configured for testing and with equal weights
    WHEN a text string is requested from the config
    THEN the correct text is returned
    """
    settings = Settings()
    result = settings.get_text(settings.PAGE_TITLE_USER_REGISTRATION, equal_weight_app)
    assert result == 'User Registration'


def test_get_comparison_conf(equal_weight_app):
    """
    GIVEN a flask app configured for testing and with equal weights
    WHEN the weight configuration is requested
    THEN the correct information is returned
    """
    settings = Settings()
    result = settings.get_comparison_conf(settings.GROUP_WEIGHT_CONFIGURATION, equal_weight_app)
    assert result == 'equal'


def test_get_user_conf(equal_weight_app):
    """
    GIVEN a flask app configured for testing and with equal weights
    WHEN the user configuration is requested
    THEN the correct details are returned
    """
    settings = Settings()
    result = settings.get_user_conf(equal_weight_app)
    assert len(result) == 5
    assert result[0] == {"name": "name", "displayName": "First Name", "type": "text", "maxLimit": 250, "required": True}  # NoQA


def test_get_behaviour_conf(equal_weight_app):
    """
    GIVEN a flask app configured for testing and with equal weights
    WHEN the export path is requested from the config
    THEN the export path is returned
    """
    settings = Settings()
    result = settings.get_behaviour_conf('exportPathLocation', equal_weight_app)
    assert result == '../exports'


def test_should_render(equal_weight_app):
    """
    GIVEN a flask app configured for testing and with equal weights
    WHEN a check for whether a section of the website should be rendered is run
    THEN the correct boolean is returned
    """
    settings = Settings()
    result = settings.should_render('renderUserItemPreferencePage', equal_weight_app)
    assert result is True
