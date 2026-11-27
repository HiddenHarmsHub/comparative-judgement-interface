from datetime import datetime, timezone

from flask import abort
from marshmallow import ValidationError
from sqlalchemy import MetaData, Table

from comparison_interface.configuration.website import Settings as WS
from comparison_interface.db.connection import db
from comparison_interface.db.models import Group, Participant, ParticipantGroup, ParticipantStudy, StudyControl
from comparison_interface.main.schemas.register import ParticipantSchemaFactory

from .request import Request

COMPONENT_TEMPLATES = {
    "int": "main/components/int.html",
    "text": "main/components/text.html",
    "radio": "main/components/radio.html",
    "dropdown": "main/components/dropdown.html",
    "email": "main/components/email.html",
}


class Register(Request):
    """Register the user doing the comparative judgment."""

    def __init__(self, app, session, study_seq=None):
        """Initialise Registration with a flag determining if this is not the first study."""
        super().__init__(app, session)
        self.study_seq = study_seq

    def get(self, _):
        """Request get handler."""
        if self.study_seq is not None:
            # Then this is just group selection for the next study
            user_components = []
            group_columns = False
            direct_registration = True
            study = db.session.scalars(
                db.select(StudyControl).where(StudyControl.study_sequence == self.study_seq)
            ).one()
            groups = db.session.scalars(db.select(Group).where(Group.study_id == study.study_id)).all()
            if len(groups) > 1:
                groups = self._load_group_component(study.study_id)
                user_components.append(groups)
                group_columns = groups['group_columns']

            return self._render_template(
                'main/pages/internal_register.html',
                {
                    'title': WS.get_text(WS.USER_REGISTRATION_FORM_TITLE_LABEL, self._language, self._app),
                    'button': WS.get_text(WS.USER_REGISTRATION_SUMMIT_BUTTON_LABEL, self._language, self._app),
                    'next_study': WS.get_text(WS.THANK_YOU_NEXT_STUDY_TEXT, self._language, self._app),
                    'next_button': WS.get_text(WS.THANK_YOU_NEXT_STUDY_BUTTON_LABEL, self._language, self._app),
                    'registration_legend': WS.get_text(
                        WS.USER_REGISTRATION_SCREEN_READER_LEGEND, self._language, self._app
                    ),
                    'components': user_components,
                    'group_columns': group_columns,
                    'direct_registration': direct_registration,
                },
            )

        if self._valid_session():
            return self._redirect('.item_selection')

        # Load components
        user_components = []
        user_components.extend(self._load_user_component())
        study_id = db.session.scalars(db.select(StudyControl.study_id).where(StudyControl.study_sequence == 1)).first()
        groups = self._load_group_component(study_id)
        user_components.append(groups)
        user_components.extend(self._load_additional_text())
        ethics_component = self._load_ethics_component()
        if ethics_component is not None:
            user_components.append(ethics_component)

        # Render components
        return self._render_template(
            'main/pages/register.html',
            {
                'title': WS.get_text(WS.USER_REGISTRATION_FORM_TITLE_LABEL, self._language, self._app),
                'button': WS.get_text(WS.USER_REGISTRATION_SUMMIT_BUTTON_LABEL, self._language, self._app),
                'registration_legend': WS.get_text(
                    WS.USER_REGISTRATION_SCREEN_READER_LEGEND, self._language, self._app
                ),
                'components': user_components,
                'group_columns': groups['group_columns'],
            },
        )

    def post(self, request):
        """Handle participant registration submission.

        User-facing validation is handled by the front end so that messages can be
        localised. This handler therefore treats any validation failure as a
        malformed or crafted request and aborts with 400.

        Args:
            request (flask.Request): The incoming Flask request containing the
                registration form data.

        Returns:
            werkzeug.wrappers.Response: A redirect to the item selection page on
                success.

        Raises:
            werkzeug.exceptions.BadRequest: If the payload is structurally invalid,
                or if the database rejects it (for example an unknown group id).
        """
        raw_form = request.form.to_dict(flat=True)
        raw_form.pop('csrf_token', None)
        raw_form.pop('group_ids', None)

        schema = self._get_participant_write_schema()
        try:
            form_data = schema.load(raw_form)
        except ValidationError:
            self._app.logger.warning("Rejected registration")
            abort(400)
        raw_group_ids = request.form.getlist("group_ids")

        study_id = db.session.scalars(db.select(StudyControl.study_id).where(StudyControl.study_sequence == 1)).first()
        # Confirm we have a list of integers we can safely insert and that they belong to the right study.
        try:
            group_ids = [int(gid) for gid in raw_group_ids]
        except (TypeError, ValueError):
            self._app.logger.warning("Rejected group_ids")
            abort(400)
        allowed_groups = db.session.scalars(db.select(Group.group_id).where(Group.study_id == study_id)).all()
        if not set(group_ids).issubset(allowed_groups):
            self._app.logger.warning("Rejected group_ids")
            abort(400)

        # Add server-managed fields. These are dump_only in the schema, so they can never arrive from the client.
        form_data['created_date'] = datetime.now(timezone.utc)
        form_data['current_study_id'] = study_id

        study_tracking = {
            'study_id': study_id,
        }

        if not WS.get_study_conf(WS.BEHAVIOUR_ESCAPE_ROUTE, study_id, self._app):
            # Cycles are not tracked for this study configuration.
            study_tracking['completed_cycles'] = None
        else:
            study_tracking['completed_cycles'] = 0

        table = self._get_participant_table()

        try:
            engine = db.engines['study_db']
            connection = db.session.connection(bind_arguments={'bind': engine})
            result = connection.execute(table.insert().values(**form_data))
            participant_id = result.inserted_primary_key[0]
            # now add the study tracking
            participant_study = ParticipantStudy(participant_id=participant_id, **study_tracking)
            db.session.add(participant_study)
            # now add the group ids
            if group_ids:
                db.session.add_all(
                    [
                        ParticipantGroup(group_id=group_id, study_id=study_id, participant_id=participant_id)
                        for group_id in group_ids
                    ]
                )
            db.session.commit()
        except Exception:
            db.session.rollback()
            self._app.logger.warning("Participant registration failed")
            abort(400)

        self._session['participant_id'] = participant_id
        self._session['group_ids'] = group_ids
        self._session['weight_conf'] = StudyControl().get_conf(study_id).weight_configuration
        self._session['previous_comparison_id'] = None
        self._session['comparison_ids'] = []
        self._session['study_id'] = study_id

        return self._redirect('.item_selection')

    def _get_participant_table(self):
        """Use the cached participant table or reflect a new one."""
        cached = getattr(self._app, '_participant_table', None)
        if cached is not None:
            return cached

        table = Table(
            'participant',
            MetaData(),
            autoload_with=db.engines['study_db'],
        )

        self._app._participant_table = table
        return table

    def _load_user_component(self):
        """Load custom user fields.

        Args:
            user_components (list): Components render in the user registry view
        """
        user_components = []
        user_fields = WS.get_user_conf(self._app)
        # Add the custom user fields
        for field in user_fields:
            field_type = field[WS.USER_FIELD_TYPE]
            if field_type in COMPONENT_TEMPLATES:
                text = {
                    "template": COMPONENT_TEMPLATES[field_type],
                    "question_text": WS.get_text(
                        f"{field[WS.USER_FIELD_NAME]}_question_text", self._language, self._app
                    ),
                    "field": field,
                }
                if 'option' in field:
                    text['option_text'] = WS.get_text(
                        f"{field[WS.USER_FIELD_NAME]}_option_text", self._language, self._app
                    ).split("||")
            user_components.append(text)
        return user_components

    def _load_group_component(self, study_id):
        """Load the group selection component.

        Args:
            study_id (int): The id of the current study.
        """
        # Allow multiple item selection only if the item's weight distribution in this study is "equal"
        multiple_selection = False
        if StudyControl().get_conf(study_id).weight_configuration == StudyControl.EQUAL_WEIGHT:
            multiple_selection = True
        groups = db.session.scalars(db.select(Group).where(Group.study_id == study_id)).all()
        if len(groups) > 1:
            label_text = WS.get_study_text(
                WS.USER_REGISTRATION_GROUP_QUESTION_LABEL, self._language, study_id, self._app
            )
            error_text = WS.get_study_text(
                WS.USER_REGISTRATION_GROUP_SELECTION_ERROR, self._language, study_id, self._app
            )
        else:
            label_text = ""
            error_text = ""
        if len(groups) >= 10:
            group_length = (len(groups) + 1) // 2
            groups = [groups[:group_length], groups[group_length:]]
            group_columns = True
        else:
            group_columns = False
        return {
            "template": "main/components/group.html",
            "groups": groups,
            "label": label_text,
            "multiple_selection": multiple_selection,
            "group_selection_error": error_text,
            "group_columns": group_columns,
        }

    def _load_additional_text(self):
        """Load any additional text for the registration page.

        This is supplied as a list of strings and ends up as one paragraph for each string in the list.
        """
        additional_list = WS.get_text(WS.ADDITIONAL_REGISTRATION_TEXT, self._language, self._app)
        if additional_list is None or len(additional_list) == 0:
            return []
        additional_text_components = []
        first = True
        for item in additional_list.split("||"):
            additional_text_components.append(
                {"template": "main/components/additional_text.html", "text": item, "add_hr": first}
            )
            first = False
        return additional_text_components

    def _load_ethics_component(self):
        """Load the ethics agreement component."""
        render_ethics = WS.should_render(WS.BEHAVIOUR_RENDER_ETHICS_AGREEMENT_PAGE, self._app)
        if not render_ethics:
            return None
        ethics_component = {
            "template": "main/components/ethics.html",
            "ethics_agreement_label": WS.get_text(
                WS.USER_REGISTRATION_ETHICS_AGREEMENT_LABEL, self._language, self._app
            ),
            "ethics_link_text": WS.get_text(WS.PAGE_TITLE_ETHICS_AGREEMENT, self._language, self._app),
        }
        return ethics_component

    def _get_participant_write_schema(self):
        """Return the cached participant write schema, building it on first use.

        The schema is derived from the reflected participant table, so it
        always matches the actual database columns. It is cached on the app
        because the active study configuration cannot change while the
        process is running.

        Returns:
            marshmallow.Schema: Participant write-schema instance.
        """
        cached = getattr(self._app, '_participant_write_schema', None)
        if cached is not None:
            return cached

        table = self._get_participant_table()
        schema_class = ParticipantSchemaFactory.build_from_table(
            table=table,
            require_ethics_acceptance=WS.should_render(WS.BEHAVIOUR_RENDER_ETHICS_AGREEMENT_PAGE, self._app),
        )
        schema = schema_class()
        self._app._participant_write_schema = schema
        return schema


class RegisterNext(Register):
    """Register group selections for follow on studies."""

    def post(self, request):
        """Handle participant registration submission.

        User-facing validation is handled by the front end so that messages can be
        localised. This handler therefore treats any validation failure as a
        malformed or crafted request and aborts with 400.

        Args:
            request (flask.Request): The incoming Flask request containing the
                registration form data.

        Returns:
            werkzeug.wrappers.Response: A redirect to the item selection page on
                success.

        Raises:
            werkzeug.exceptions.BadRequest: If the payload is structurally invalid,
                or if the database rejects it (for example an unknown group id).
        """
        raw_group_ids = request.form.getlist("group_ids")

        study_id = db.session.scalars(
            db.select(StudyControl.study_id).where(StudyControl.study_sequence == self.study_seq)
        ).first()

        # Confirm we have a list of integers we can safely insert and that they belong to the right study.
        try:
            group_ids = [int(gid) for gid in raw_group_ids]
        except (TypeError, ValueError):
            self._app.logger.warning("Rejected group_ids")
            abort(400)
        allowed_groups = db.session.scalars(db.select(Group.group_id).where(Group.study_id == study_id)).all()

        if not set(group_ids).issubset(allowed_groups):
            self._app.logger.warning("Rejected group_ids")
            abort(400)

        study_tracking = {
            'study_id': study_id,
        }

        if not WS.get_study_conf(WS.BEHAVIOUR_ESCAPE_ROUTE, study_id, self._app):
            # Cycles are not tracked for this study configuration.
            study_tracking['completed_cycles'] = None
        else:
            study_tracking['completed_cycles'] = 0

        try:
            # now add the study tracking
            participant_study = ParticipantStudy(participant_id=self._session['participant_id'], **study_tracking)
            db.session.add(participant_study)
            # change the partipants current study
            participant = db.session.get(Participant, self._session['participant_id'])
            participant.current_study_id = study_id
            # now add the group ids
            if group_ids:
                db.session.add_all(
                    [
                        ParticipantGroup(
                            group_id=group_id, study_id=study_id, participant_id=self._session['participant_id']
                        )
                        for group_id in group_ids
                    ]
                )
            db.session.commit()
        except Exception:
            db.session.rollback()
            self._app.logger.warning("Participant registration failed")
            abort(400)

        self._session['group_ids'] = group_ids
        self._session['weight_conf'] = StudyControl().get_conf(study_id).weight_configuration
        self._session['previous_comparison_id'] = None
        self._session['comparison_ids'] = []
        self._session['study_id'] = study_id

        return self._redirect('.item_selection')
