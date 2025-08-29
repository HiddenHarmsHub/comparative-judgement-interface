import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import MetaData
from sqlalchemy.exc import SQLAlchemyError

from app import create_app
from comparison_interface.admin.models import User
from comparison_interface.configuration.validation import Validation as ConfigValidation
from comparison_interface.configuration.website import Settings as WS
from comparison_interface.db.connection import db
from comparison_interface.db.setup import Setup as DBSetup


def execute_setup(conf_file):
    app = create_app(
        {
            "TESTING": True,
            "API_ACCESS": False,
            "ADMIN_ACCESS": True,
            "LANGUAGE": "en",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///test_admin_database.db",
            "SQLALCHEMY_BINDS": {"study_db": "sqlite:///test_database.db"},
            "SECURITY_TWO_FACTOR": False,
            "SECURITY_TWO_FACTOR_REQUIRED": False,
            "WTF_CSRF_ENABLED": False,
            "SECURITY_PASSWORD_HASH": "plaintext",
            "LOGIN_DISABLED": False
        }
    )

    # 1. Validate the website configuration
    app.logger.info("Setting website configuration")
    WS.set_configuration_location(app, conf_file)
    ConfigValidation(app).validate()

    # 2. Configure database
    app.logger.info("Resetting website database")
    s = DBSetup(app)
    s.exec()
    return app


@pytest.fixture(scope="session")
def app():
    """Set up the project for testing with equal weights."""
    app = execute_setup("../tests_python/test_configurations/config-equal-item-weights.json")
    with app.app_context():
        db.create_all()
        db.session.add_all([
            User(email="test@example.co.uk", password="password", active=1, fs_uniquifier="1")
        ])
        db.session.commit()
        user = app.security.datastore.find_user(email="test@example.co.uk")
        print(user)
    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()
        os.unlink(os.path.join(os.path.join(app.instance_path), 'test_database.db'))
        os.unlink(os.path.join(os.path.join(app.instance_path), 'test_admin_database.db'))
