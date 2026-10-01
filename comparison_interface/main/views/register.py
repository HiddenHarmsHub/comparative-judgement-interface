from datetime import datetime, timezone

from flask import abort, render_template
from marshmallow import ValidationError
from sqlalchemy import MetaData, Table
from sqlalchemy.exc import SQLAlchemyError

from comparison_interface.configuration.website import Settings as WS
from comparison_interface.db.connection import db
from comparison_interface.db.models import Group, Participant, ParticipantGroup, WebsiteControl
from comparison_interface.schema.request_schema import ParticipantSchemaFactory

from .request import Request


class Register(Request):
    """Register the user doing the comparative judgment."""

    def get(self, _):
        """Request get handler."""
        if self._valid_session():
            return self._redirect('.item_selection')

        # Load components
        user_components = []
        self._load_user_component(user_components)
        group_columns = self._load_group_component(user_components)
        self._load_additional_text(user_components)
        self._load_ethics_component(user_components)

        # Render components
        return self._render_template(
            'main/pages/register.html',
            {
                'title': WS.get_text(WS.USER_REGISTRATION_FORM_TITLE_LABEL, self._app),
                'button': WS.get_text(WS.USER_REGISTRATION_SUMMIT_BUTTON_LABEL, self._app),
                'components': user_components,
                'group_columns': group_columns,
            },
        )

    def post(self, request):
        """Handle participant registration submission.

        Validates the submitted registration form against the dynamically built
        participant schema, then inserts the participant row and the selected
        group preferences in a single transaction, and initialises the user
        session.

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
        # 1. Read the form once in multi-value mode so repeated checkbox fields
        #    (group_ids) are preserved, then flatten the remaining single-value
        #    fields for the schema.
        raw_form = request.form.to_dict(flat=False)
        raw_form.pop('csrf_token', None)
        raw_group_ids = raw_form.pop('group_ids', [])
        form_data = {key: values[0] for key, values in raw_form.items()}

        # 2. Validate the participant fields.
        schema = self._get_participant_write_schema()
        try:
            dic_user_attr = schema.load(form_data)
        except ValidationError as err:
            self._app.logger.warning("Rejected registration payload: %s", err.messages)
            abort(400)

        # 3. Structural check on the group selection only. The front end enforces
        #    "at least one group" in the participant's language; here we only
        #    confirm we have a list of integers we can safely insert.
        try:
            group_ids = [int(gid) for gid in raw_group_ids]
        except (TypeError, ValueError):
            self._app.logger.warning("Rejected non-integer group_ids: %r", raw_group_ids)
            abort(400)

        # 4. Add server-managed fields. These are dump_only in the schema, so they
        #    can never arrive from the client, but the app is free to set them.
        dic_user_attr['created_date'] = datetime.now(timezone.utc)
        if not WS.get_behaviour_conf(WS.BEHAVIOUR_ESCAPE_ROUTE, self._app):
            # Cycles are not tracked for this study configuration.
            dic_user_attr['completed_cycles'] = None
        else:
            dic_user_attr['completed_cycles'] = 0

        # 5. Insert the participant and the group preferences together, on one
        #    connection and in one transaction, so that a foreign key failure on
        #    any group id rolls the participant row back too.
        table = self._get_participant_table()

        try:
            with db.engines['study_db'].begin() as connection:
                result = connection.execute(table.insert().values(**dic_user_attr))
                participant_id = result.inserted_primary_key[0]

                if group_ids:
                    # executemany raises on an empty list, hence the guard above.
                    connection.execute(
                        ParticipantGroup.__table__.insert(),
                        [
                            {'group_id': group_id, 'participant_id': participant_id}
                            for group_id in group_ids
                        ],
                    )
        except SQLAlchemyError as e:
            # The transaction has already been rolled back by the context manager.
            # An IntegrityError here means a crafted request (unknown group id or
            # a duplicate pair), not a server fault, so 400 rather than 500.
            self._app.logger.warning("Participant registration failed: %s", e)
            abort(400)

        # 6. Initialise the session.
        self._session['participant_id'] = participant_id
        self._session['group_ids'] = group_ids
        self._session['weight_conf'] = WebsiteControl().get_conf().weight_configuration
        self._session['previous_comparison_id'] = None
        self._session['comparison_ids'] = []

        return self._redirect('.item_selection')

    def _get_participant_table(self):
        """Use the cached participant table of reflect a new one."""
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

    def _load_user_component(self, user_components: list):
        """Load custom user fields.

        Args:
            user_components (list): Components render in the user registry view
        """
        user_fields = WS.get_user_conf(self._app)
        # Add the custom user fields
        for field in user_fields:
            component = 'main/components/{}.html'.format(field[WS.USER_FIELD_TYPE])
            user_components.append(render_template(component, **field))

    def _load_group_component(self, user_components: list):
        """Load the group selection component.

        Args:
            user_components (list): Components render in the user registry view
        """
        # Allow multiple item selection only if the item's weight distribution is "equal"
        multiple_selection = False
        if WebsiteControl().get_conf().weight_configuration == WebsiteControl.EQUAL_WEIGHT:
            multiple_selection = True

        groups = db.session.scalars(db.select(Group)).all()
        if len(groups) > 1:
            label_text = WS.get_text(WS.USER_REGISTRATION_GROUP_QUESTION_LABEL, self._app)
            error_text = WS.get_text(WS.USER_REGISTRATION_GROUP_SELECTION_ERROR, self._app)
        else:
            label_text = ''
            error_text = ''
        if len(groups) >= 10:
            group_length = (len(groups) + 1) // 2
            groups = [groups[:group_length], groups[group_length:]]
            group_columns = True
        else:
            group_columns = False
        user_components.append(
            render_template(
                'main/components/group.html',
                **{
                    'groups': groups,
                    'label': label_text,
                    'multiple_selection': multiple_selection,
                    'group_selection_error': error_text,
                    'group_columns': group_columns,
                },
            )
        )
        return group_columns

    def _load_additional_text(self, user_components: list):
        """Load any additional text for the registration page.

        This is supplied as a list of strings and ends up as one paragraph for each string in the list.

        Args:
            user_components (list): Components render in the user registry view
        """
        additional_list = WS.get_optional_text(WS.ADDITIONAL_REGISTRATION_TEXT, self._app)
        if additional_list is not None:
            if len(additional_list) > 0:
                user_components.append('<hr/>')
                for item in additional_list:
                    user_components.append(render_template('main/components/additional_text.html', **{'text': item}))

    def _load_ethics_component(self, user_components: list):
        """Load the ethics agreement component.

        Args:
            user_components (list): Components render in the user registry view
        """
        render_ethics = WS.should_render(WS.BEHAVIOUR_RENDER_ETHICS_AGREEMENT_PAGE, self._app)
        if render_ethics:
            user_components.append(
                render_template(
                    'main/components/ethics.html',
                    **{
                        'ethics_agreement_label': WS.get_text(WS.USER_REGISTRATION_ETHICS_AGREEMENT_LABEL, self._app),
                        'ethics_link_text': WS.get_text(WS.PAGE_TITLE_ETHICS_AGREEMENT, self._app),
                    },
                )
            )

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
            require_ethics_acceptance=WS.get_behaviour_conf(
                WS.BEHAVIOUR_RENDER_ETHICS_AGREEMENT_PAGE, self._app
            ),
        )
        schema = schema_class()
        self._app._participant_write_schema = schema
        return schema
