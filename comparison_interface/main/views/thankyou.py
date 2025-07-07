from ..configuration.website import Settings as WS
from ..db.connection import db
from ..db.models import User
from .request import Request


class Thankyou(Request):
    """Page to say thankyou after each cycle is complete."""

    def get(self, _):
        """Request get handler."""
        data = {
            'thank_you_page_title': WS.get_text(WS.PAGE_TITLE_THANK_YOU, self._app),
            'title': WS.get_text(WS.THANK_YOU_TITLE, self._app),
            'opening_text': WS.get_text(WS.THANK_YOU_OPENING_TEXT, self._app),
            'continue_text': WS.get_text(WS.THANK_YOU_CONTINUE_TEXT, self._app),
            'stop_text': WS.get_text(WS.THANK_YOU_STOP_TEXT, self._app),
            'button': WS.get_text(WS.THANK_YOU_CONTINUE_BUTTON_LABEL, self._app),
        }
        if self._can_continue():
            data['continue'] = True
        return self._render_template('main/pages/thankyou.html', data)

    def _can_continue(self):
        """Check if this user can complete another cycle."""
        user = db.session.get(User, self._session['user_id'])
        if user.completed_cycles is None or user.completed_cycles < WS.get_behaviour_conf(
            WS.BEHAVIOUR_MAX_CYCLES, self._app
        ):
            return True
        return False
