from flask import render_template
from flask_security import auth_required

from comparison_interface.admin import blueprint


@blueprint.route('/dashboard', methods=['GET'])
@blueprint.route('/', methods=['GET'])
@auth_required('session', within=10)
def dashboard():
    """Show the admin dashboard."""
    return render_template("dashboard.html")


@blueprint.route('/setup-study', methods=['POST'])
@auth_required('session', within=10)
def setup_study():
    """Set up a new study."""
    return
