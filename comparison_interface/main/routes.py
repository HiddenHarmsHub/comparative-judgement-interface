"""Handles all the URL routing."""

from flask import current_app, request, session

from comparison_interface.main import blueprint

from .views.ethics import Ethics
from .views.introduction import Introduction
from .views.item_preference import ItemsPreference
from .views.logout import Logout
from .views.policies import Policies
from .views.rank import Rank
from .views.register import Register
from .views.request import Request
from .views.thankyou import Thankyou


@blueprint.route('/introduction', methods=['GET'])
def introduction():
    """Handle introduction URL."""
    return Request.process(Introduction(current_app, session), request)


@blueprint.route('/ethics-agreement', methods=['GET'])
def ethics_agreement():
    """Handle ethics agreement URL."""
    return Request.process(Ethics(current_app, session), request)


@blueprint.route('/policies', methods=['GET'])
def policies():
    """Handle policies URL."""
    return Request.process(Policies(current_app, session), request)


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/register', methods=['GET', 'POST'])
def user_registration():
    """Handle registration URL and the route location when no user session registered."""
    return Request.process(Register(current_app, session), request)


@blueprint.route('/selection/items', methods=['GET', 'POST'])
def item_selection():
    """Handle item selection URL (pre-ranking)."""
    return Request.process(ItemsPreference(current_app, session), request)


@blueprint.route('/rank', methods=['GET', 'POST'])
def rank():
    """Handle ranking URL."""
    return Request.process(Rank(current_app, session), request)


@blueprint.route('/logout', methods=['GET'])
def logout():
    """Handle logout URL."""
    return Request.process(Logout(current_app, session), request)


@blueprint.route('/thankyou', methods=['GET'])
def thankyou():
    """Handle thankyou/escape route URL."""
    return Request.process(Thankyou(current_app, session), request)
