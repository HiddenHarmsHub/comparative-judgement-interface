import pytest
from marshmallow import ValidationError

from app import create_app
from comparison_interface.configuration.validation import Validation
from comparison_interface.configuration.validation import Validation as ConfigValidation
from comparison_interface.configuration.website import Settings as WS
from comparison_interface.db.setup import Setup as DBSetup


def test_validate_csv_structure_invalid_csv(equal_weight_app, tmp_path):
    """
    GIVEN the path to a csv file missing a required column header
    WHEN the csv file structure is validated
    THEN a ValidationError is raised
    """
    csv_path = tmp_path / "invalid.csv"
    csv_path.write_text('Display,PNG')
    with pytest.raises(ValidationError):
        validator = Validation(equal_weight_app)
        validator.validate_csv_structure(csv_path)


def test_validate_csv_structure_valid_csv(equal_weight_app, tmp_path):
    """
    GIVEN the path to a csv file which has the required columns
    WHEN the csv file structure is validated
    THEN no ValidationError is raised
    """
    csv_path = tmp_path / "valid.csv"
    csv_path.write_text('Item Display Name,Image')
    validator = Validation(equal_weight_app)
    try:
        validator.validate_csv_structure(csv_path)
    except ValidationError as err:
        assert False, f'ValidationError raised: {err}'


def test_setup_works_for_directory_with_csv():
    """
    GIVEN a flask application set up for testing
    WHEN the location is set using an valid directory path
    THEN the app is created
    """
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": 'sqlite:///test_database.db'})
    # 1. Validate the website configuration
    app.logger.info("Setting website configuration")
    WS.set_configuration_location(app, "../tests_python/test_configurations/csv_example_1")
    ConfigValidation(app).validate()

    # 2. Configure database
    app.logger.info("Resetting website database")
    s = DBSetup(app)
    s.exec()
    assert app


def test_setup_fails_for_directory_with_wrong_files():
    """
    GIVEN a flask application set up for testing
    WHEN the location is set using an invalid directory path
    THEN the system exits
    """
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": 'sqlite:///test_database.db'})
    # 1. Validate the website configuration
    app.logger.info("Setting website configuration")
    WS.set_configuration_location(app, "../tests_python/test_configurations")
    with pytest.raises(SystemExit):
        ConfigValidation(app).validate()


def test_check_config_path_correct(equal_weight_app):
    """
    GIVEN a path to a directory which contains the required files
    WHEN the config path is checked
    THEN the system does not exit
    """
    validator = Validation(equal_weight_app)
    validator.check_config_path("../tests_python/test_configurations/csv_example_1")


def test_check_config_path_incorrect_directory(equal_weight_app):
    """
    GIVEN a path to a directory which does not contain the required files
    WHEN the config path is checked
    THEN the system exists as the required files are not present
    """
    validator = Validation(equal_weight_app)
    with pytest.raises(SystemExit):
        validator.check_config_path("../tests_python/test_configurations")


def test_check_config_path_incorrect_file(equal_weight_app):
    """
    GIVEN a path to a csv file as the configuration file
    WHEN the config path is checked
    THEN the system exists as it is not a JSON file
    """
    validator = Validation(equal_weight_app)
    with pytest.raises(SystemExit):
        validator.check_config_path("../tests_python/test_configurations/csv_example_1/example_1.csv")
