"""Handles all the URL routing."""

from flask import current_app, redirect, request, session

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


@blueprint.route('/set-language', methods=['POST'])
def set_language():
    """Set the user's language preference."""
    language = request.form.get('language')
    if language not in current_app["SUPPORTED_LANGUAGES"]:
        session['language'] = language
    else:
        session['language'] = current_app["SUPPORTED_LANGUAGES"][0]
    return redirect(request.referrer or '/')


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
def participant_registration():
    """Handle registration URL and the route location when no user session registered."""
    return Request.process(Register(current_app, session), request)


@blueprint.route('/selection/items', methods=['GET', 'POST'])
def item_selection():
    """Handle item selection URL (pre-ranking)."""
    return Request.process(ItemsPreference(current_app, session), request)


@blueprint.route('/rank/previous', methods=['GET', 'POST'])
def previous():
    """Handle ranking URL."""
    if request.method == 'GET':
        # reset to the most recent comparison so the previous button still works
        session['previous_comparison_id'] = session['comparison_ids'][-1]
        return redirect('/rank')
    return Request.process(Rank(current_app, session, previous=True), request)


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
