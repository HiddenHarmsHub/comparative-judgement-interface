from flask import Blueprint

blueprint = Blueprint('admin', __name__, template_folder="templates")

from comparison_interface.admin import models, routes  # NoQA
