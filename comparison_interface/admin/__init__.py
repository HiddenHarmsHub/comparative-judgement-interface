from flask import Blueprint

blueprint = Blueprint('admin', __name__)

from comparison_interface.admin import *  # NoQA
