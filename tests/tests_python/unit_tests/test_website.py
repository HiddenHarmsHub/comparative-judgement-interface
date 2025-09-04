from comparison_interface.configuration.website import Settings as WS


def test_configuration_has_key_true(equal_weight_app):
    """
    GIVEN a flask app configured for testing and with the equal weight configuration
    WHEN a key is requested that is in the configuration file
    THEN True is returned
    """
    result = WS.configuration_has_key("rankItemInstructionLabel", equal_weight_app)
    assert result is True


def test_configuration_has_key_false(equal_weight_app):
    """
    GIVEN a flask app configured for testing and with the equal weight configuration
    WHEN a key is requested that is not in the configuration file (but is in the language file)
    THEN False is returned
    """
    result = WS.configuration_has_key("pageTitleEthicsAgreement", equal_weight_app)
    assert result is False
