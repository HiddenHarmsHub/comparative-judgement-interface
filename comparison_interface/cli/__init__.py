from flask import Blueprint

blueprint = Blueprint('cli', __name__, cli_group=None)

from comparison_interface.cli import cli
