from flask import Blueprint

blueprint = Blueprint('api', __name__)

from comparison_interface.api import api