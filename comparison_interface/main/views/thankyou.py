from flask import current_app
from jinja2.exceptions import TemplateNotFound

from comparison_interface.configuration.website import Settings as WS
from comparison_interface.db.connection import db
from comparison_interface.db.models import Group, Participant, ParticipantGroup

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
            'siem_reap': self._in_target_group(),
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

    def _in_target_group(self):
        """Check if the participant selected our target group."""
        query = (
            db.select(ParticipantGroup, Group.name)
            .join(Group, Group.group_id == ParticipantGroup.group_id, isouter=True)
            .where(
                ParticipantGroup.participant_id == self._session['participant_id'],
            )
        )
        result = db.session.execute(query).all()
        target = 'siemreab'
        for item in result:
            if item[1] == target:
                return True
        return False
