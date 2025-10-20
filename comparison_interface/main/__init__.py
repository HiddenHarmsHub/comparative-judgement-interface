from flask import Blueprint

blueprint = Blueprint('main', __name__)

from comparison_interface.main import routes  # NoQA
