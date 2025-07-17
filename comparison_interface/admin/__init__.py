from flask import Blueprint

blueprint = Blueprint('admin', __name__, template_folder="templates", static_folder='static')

from comparison_interface.admin import models, routes  # NoQA
