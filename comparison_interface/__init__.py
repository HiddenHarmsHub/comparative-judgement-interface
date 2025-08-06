"""Initialize the website application."""

import json
import os
from datetime import datetime, timedelta, timezone

from flask import Flask, current_app, render_template, request, session
from flask_mailman import Mail
from flask_security import Security, SQLAlchemyUserDatastore
from numpy.random import default_rng
from whitenoise import WhiteNoise

from comparison_interface.admin import blueprint as admin_bp
from comparison_interface.admin import models
from comparison_interface.cli import blueprint as commands_bp
from comparison_interface.configuration.flask import Settings as FlaskSettings
from comparison_interface.configuration.website import Settings as WS
from comparison_interface.db.connection import db
from comparison_interface.db.models import WebsiteControl
from comparison_interface.main import blueprint as main_bp
from comparison_interface.main.views.request import Request


def create_app(test_config=None):
    """Start Flask website application.

    Args:
        config_filename (object, optional): Default configuration file. Defaults to None. Used for testing.
    """
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True, static_folder="static")
    app.config.from_object(FlaskSettings)
    if test_config is not None:
        app.config.from_mapping(test_config)
    try:
        language = app.config["LANGUAGE"]
    except KeyError:
        language = 'en'

    language_filepath = os.path.join(os.path.dirname(__file__), "languages", f"{language}.json")
    if not os.path.exists(language_filepath):
        raise RuntimeError("The required file for the language requested in the flask configuration is not available.")

    with open(
        language_filepath,
        mode='r',
        encoding='utf-8',
    ) as config_file:
        app.language_config = json.load(config_file)

    # Register the database
    db.init_app(app)

    # Register the custom Flask commands
    app.register_blueprint(commands_bp)

    # Register the application views
    app.register_blueprint(main_bp)

    # Register the admin blueprint (might be made optional eventually)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Setup Flask-Security
    user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
    security = Security(app, user_datastore)
    mail = Mail(app)  # NoQA

    @security.context_processor
    def security_context_processor():
        if WS.CONFIGURATION_LOCATION in app.config:
            return {"website_title": WS.get_text(WS.WEBSITE_TITLE, app)}
        else:
            return {"website_title": "No active study"}

    # if we have asked for the api blueprint then register this here
    if "API_ACCESS" in app.config and app.config["API_ACCESS"] is True:
        from comparison_interface.api import blueprint as api_bp

        app.register_blueprint(api_bp)

    # Register function executed before any request
    app.before_request(_before_request)

    # Register page errors
    app.register_error_handler(404, _page_not_found)
    app.register_error_handler(500, _page_unexpected_condition)

    # Add the management for static libraries
    WHITENOISE_MAX_AGE = 31536000 if not app.config["DEBUG"] else 0
    app.wsgi_app = WhiteNoise(
        app.wsgi_app,
        root=os.path.join(os.path.dirname(__file__), "static"),
        prefix="assets/",
        max_age=WHITENOISE_MAX_AGE,
    )

    # seed the random number generator per process if we are in a uwsgi environment
    try:
        from uwsgidecorators import postfork
    except ModuleNotFoundError:
        app.rng = default_rng()
    else:

        @postfork
        def _seed_random_number():
            app.rng = default_rng()

        _seed_random_number()

    return app


def _before_request():
    """Run functions before every request except the admin routes and the static files."""
    if (
        request.endpoint is not None
        and not request.endpoint.startswith('admin.')
        and not request.endpoint.startswith('security.')
        and request.endpoint not in ['static']
    ):
        _validate_app_integrity()
    _configure_user_session()


def _configure_user_session():
    """Configure the user's session behaviour."""
    app = current_app
    print(session)
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=app.config['SESSION_MINUTES_VALIDITY'])
    session.modified = True


def _validate_app_integrity():
    """Stop the server execution if the configuration file was modified after the application setup was executed.

    The configuration file is used by the website during runtime. Modification of this file can cause
    unexpected results so changes are monitored and a RuntimeError will be raised if a change is detected.
    """
    app = current_app
    modification_date = None
    with app.app_context():
        try:
            # Get the application control variables
            w = WebsiteControl()
            conf = w.get_conf()

            WS.set_configuration_location(app, conf.configuration_file)
            setup_exec_date = conf.setup_exec_date.replace(tzinfo=timezone.utc)

            # Get the last modification date of the configuration file (UTC)
            modification_date = os.path.getmtime(WS.get_configuration_location(app))
            modification_date = datetime.fromtimestamp(modification_date, tz=timezone.utc)
        except Exception as e:
            app.logger.critical(str(e))
            raise RuntimeError("Application not yet initialised. Please read the README.md file for instructions.")

        # Stop the server execution if the configuration file was modified after the setup of the application.
        if modification_date is None or modification_date > setup_exec_date:
            app.logger.critical(
                "The configuration file cannot be modified after the website has been initialised "
                "with the setup command. The file was modified on: %s UTC. Setup executed on : %s UTC. "
                "Please execute >Flask setup< again if you want to re-initialise the database."
                % (modification_date.strftime("%m/%d/%Y, %H:%M:%S"), setup_exec_date.strftime("%m/%d/%Y, %H:%M:%S"))
            )
            raise RuntimeError("Application unhealthy state. Please contact the website administrator.")


def _page_not_found(e):
    """Return 404 page."""
    data = {
        'error_404_title': WS.get_text(WS.ERROR_404_TITLE, current_app),
        'error_404_message': WS.get_text(WS.ERROR_404_MESSAGE, current_app),
        'error_404_home_link': WS.get_text(WS.ERROR_404_HOME_LINK, current_app),
    }
    return render_template('404.html', **{**data, **Request(current_app, session).get_layout_text()}), 404


def _page_unexpected_condition(e):
    """Return 500 page."""
    data = {
        'error_500_title': WS.get_text(WS.ERROR_500_TITLE, current_app),
        'error_500_message': WS.get_text(WS.ERROR_500_MESSAGE, current_app),
    }
    return render_template('500.html', **{**data, **Request(current_app, session).get_layout_text()}), 500
