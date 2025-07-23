"""Commands which are used to setup and control the application."""

import os

import click
from flask import current_app
from flask.cli import with_appcontext
from marshmallow import ValidationError
from sqlalchemy.exc import OperationalError

from comparison_interface.cli import blueprint
from comparison_interface.configuration.validation import Validation as ConfigValidation
from comparison_interface.configuration.website import Settings as WS
from comparison_interface.db.connection import db
from comparison_interface.db.export import Exporter
from comparison_interface.db.models import WebsiteControl
from comparison_interface.db.setup import Setup as DBSetup


@blueprint.cli.command("setup_admin")
@with_appcontext
def setup_admin():
    app = current_app
    with app.app_context():
        db.create_all(None)


@blueprint.cli.command("setup")
@click.argument("conf", type=click.Path(file_okay=True, dir_okay=True))
@with_appcontext
def setup(conf):
    """Call the methods to set up the application.

    This operation will be ignored if the application has already been setup. Run flask reset to delete the existing
    application and start from a clean setup after the initial setup has been completed.

    Args:
        conf (string): Website configuration location (either the path to a JSON file or a dir path to a dir containing
                       one JSON file and one CSV file.)
    """
    # 1. Validate the website configuration
    app = current_app
    ConfigValidation(app).check_config_path(conf)
    app.logger.info("Setting website configuration")
    WS.set_configuration_location(app, conf)
    try:
        ConfigValidation(app).validate()
    except ValidationError as err:
        app.logger.critical(err)
        exit()

    # 2. Configure database
    with app.app_context():
        try:
            # 2.1 Ignore, if the application was already set-up
            w = WebsiteControl()
            conf = w.get_conf()
            app.logger.info('Application setup already executed.')
        except OperationalError:
            # 2.2 If not, configure the website database.
            app.logger.info("Configuring website database")
            s = DBSetup(app)
            s.exec()
        except Exception as e:
            # 2.3 Report the error in any other case.
            app.logger.critical(e)
            exit()


@blueprint.cli.command("reset")
@click.argument("conf")
@with_appcontext
def reset(conf):
    """Reset the application to an initial empty state.

    WARNING:  This will delete the database content as well other exported information.

    Args:
        conf (string): Website configuration location
    """
    app = current_app
    confirm = input(
        'Running this command will delete all of the data in the database and all existing export files. '
        'If you still want to run this command type yes, if you want to cancel type no. yes/no: '
    )
    if confirm.strip() == 'yes':
        # 1. Validate the website configuration
        ConfigValidation(app).check_config_path(conf)
        app.logger.info("Setting website configuration")
        WS.set_configuration_location(app, conf)
        try:
            ConfigValidation(app).validate()
        except ValidationError as err:
            app.logger.critical(err)
            exit()

        # 2. Configure database
        app.logger.info("Resetting website database")
        s = DBSetup(app)
        s.exec()

    else:
        app.logger.info("Reset command cancelled")
        return


@blueprint.cli.command("export")
@click.option("--format", default="csv", show_default=True, help="The file format required (csv or tsv)")
@with_appcontext
def export(format):
    """Export the database to a zip file containing either csv or tsv files (csv by default).

    Each file in the zip file will contain a database table. The file will be saved to the location specified by the
    behaviour configuration key 'exportPathLocation'.

    Args:
        format (string, optional): The file format required for each table, must be either csv or tsv. Default is csv.
    """
    app = current_app
    location = None
    with app.app_context():
        if format not in ['csv', 'tsv']:
            app.logger.critical('Invalid file type requested. Must be csv or tsv.')
            exit()
        try:
            # Get the website control variables
            w = WebsiteControl()
            conf = w.get_conf()
            # Set the application configuration
            app.logger.info("Setting website configuration")
            WS.set_configuration_location(app, conf.configuration_file)
            ConfigValidation(app).validate()
            location = WS.get_export_location(app)
            if not os.path.exists(location):
                os.makedirs(location)
                app.logger.info('Creating folder for data export.')

        except OperationalError:
            app.logger.critical('Application not yet initialised.')
            exit()
        except Exception as e:
            # Report any other error
            app.logger.critical(e)
            exit()

    app.logger.info("Exporting database tables into {}".format(location))
    Exporter(app).save(location, format)
