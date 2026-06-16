from flask import current_app
from jinja2.exceptions import TemplateNotFound
from sqlalchemy import MetaData, Table, text

from comparison_interface.configuration.website import Settings as WS
from comparison_interface.db.connection import db
from comparison_interface.db.models import Participant

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
            'participant_id': self._session['participant_id'],
            'siem_reap': self._get_siem_reap(),
        }
        if self._can_continue():
            data['continue'] = True
        if 'CUSTOM_TEMPLATES' in current_app.config and current_app.config['CUSTOM_TEMPLATES'] is True:
            try:
                return self._render_template('custom_templates/thankyou.html', data)
            except TemplateNotFound:
                pass
        return self._render_template('main/pages/thankyou.html', data)

    def _can_continue(self):
        """Check if this participant can complete another cycle."""
        participant = db.session.get(Participant, self._session['participant_id'])
        if participant.completed_cycles is None or participant.completed_cycles < WS.get_behaviour_conf(
            WS.BEHAVIOUR_MAX_CYCLES, self._app
        ):
            return True
        return False

    def _get_siem_reap(self):
        """Check if the participant selected siem reap in study 1."""
        participant = db.session.get(Participant, self._session['participant_id'])
        print(participant)
        print(dir(participant))
        db_engine = db.engines['study_db']
        db_meta = MetaData()
        db_meta.reflect(bind=db_engine)
        sql = text("select {} from participant where participant_id={};".format(
            'siem_reap', self._session['participant_id'])
        )
        with db_engine.begin() as connection:
            results = connection.execute(sql)
        for record in results:
            if record[0] == 'true':
                return True
        return False
