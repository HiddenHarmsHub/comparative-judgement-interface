import os
from tempfile import TemporaryDirectory

import pytest

from app import create_app
from comparison_interface.admin.models import User
from comparison_interface.configuration.validation import Validation as ConfigValidation
from comparison_interface.configuration.website import Settings as WS
from comparison_interface.db.connection import db
from comparison_interface.db.setup import Setup as DBSetup


def execute_setup(conf_file):
    """Setup a test system with admin turned on."""

    app = create_app(
        testing=True,
        test_config={"ADMIN_ACCESS": True},
    )
    temp_dir = TemporaryDirectory(dir=app.root_path)
    dir_name = temp_dir.name.replace(app.root_path + '/', '')

    app.config.from_mapping(
        {
            "IMAGE_UPLOAD_DIR": f"{dir_name}/static/images/",
            "HTML_PAGES_DIR": f"{dir_name}/pages_html",
            "CONFIG_UPLOAD_DIR": f"{dir_name}/project_configuration",
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


@pytest.fixture()
def app():
    """Set up the admin project for testing with equal weights."""

    app = execute_setup("../tests/test_configurations/config-equal-item-weights-2.json")
    with app.app_context():
        db.create_all()
        db.session.add_all([User(email="test@example.co.uk", password="password", active=1, fs_uniquifier="1")])
        db.session.commit()

    # directories need to be made already
    os.makedirs(os.path.join(app.root_path, app.config["IMAGE_UPLOAD_DIR"]))
    os.makedirs(os.path.join(app.root_path, app.config["HTML_PAGES_DIR"]))
    os.makedirs(os.path.join(app.root_path, app.config["CONFIG_UPLOAD_DIR"]))

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()
        os.unlink(os.path.join(os.path.join(app.instance_path), 'test_database.db'))
        os.unlink(os.path.join(os.path.join(app.instance_path), 'test_admin_database.db'))
