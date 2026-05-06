from flask import Blueprint

blueprint = Blueprint('custom_templates', __name__, template_folder="templates", static_folder='static', static_url_path='/custom')

#from comparison_interface.custom_templates import models, routes  # NoQA
