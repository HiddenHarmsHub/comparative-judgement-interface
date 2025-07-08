import os

from comparison_interface.configuration.website import Settings as WS


def test_export_equal_weights(equal_weight_client, equal_weight_app, user_data):
    """
    GIVEN a flask app configured for testing and equal weights
    WHEN the export is requested on the command line
    THEN a zip file is generated in the export location
    """
    with equal_weight_client:
        equal_weight_client.post("/register", data=user_data)
    runner = equal_weight_app.test_cli_runner()
    runner.invoke(args=["export"])

    assert os.path.exists(os.path.join(WS.get_export_location(equal_weight_app), 'database_export.zip'))
