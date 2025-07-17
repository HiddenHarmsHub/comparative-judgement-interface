from datetime import datetime, timezone

from flask import render_template
from sqlalchemy import MetaData
from sqlalchemy.exc import SQLAlchemyError

from comparison_interface.configuration.website import Settings as WS
from comparison_interface.db.connection import db
from comparison_interface.db.models import Group, Participant, ParticipantGroup, WebsiteControl

from .request import Request


class Register(Request):
    """Register the user doing the comparative judgment."""

    def get(self, _):
        """Request get handler."""
        print('here we are')
        print(self._valid_session())
        if self._valid_session():
            
            return self._redirect('.item_selection')

        # Load components
        user_components = []
        self._load_user_component(user_components)
        self._load_group_component(user_components)
        self._load_additional_text(user_components)
        self._load_ethics_component(user_components)

        # Render components
        return self._render_template(
            'main/pages/register.html',
            {
                'title': WS.get_text(WS.USER_REGISTRATION_FORM_TITLE_LABEL, self._app),
                'button': WS.get_text(WS.USER_REGISTRATION_SUMMIT_BUTTON_LABEL, self._app),
                'components': user_components,
            },
        )

    def post(self, request):
        """Request post handler."""
        # Remove the group id from the request.
        # This field is not related to the user model
        dic_user_attr = request.form.to_dict(flat=True)
        dic_user_attr.pop('group_ids', None)

        # Get all groups id selected by the user
        group_ids = request.form.to_dict(flat=False)['group_ids']

        # Register the user in the database.
        # Some of the user fields were dynamically added so we are using SQLAlchemy
        # reflection functionality to insert them.
        db_engine = db.engines['study_db']
        db_meta = MetaData()
        db_meta.reflect(bind=db_engine)
        table = db_meta.tables["participant"]
        dic_user_attr['created_date'] = datetime.now(timezone.utc)
        if not WS.get_behaviour_conf(WS.BEHAVIOUR_ESCAPE_ROUTE, self._app):
            dic_user_attr['completed_cycles'] = None
        new_user_sql = table.insert().values(**dic_user_attr)
        try:
            # Insert the user into the database
            with db_engine.begin() as connection:
                result = connection.execute(new_user_sql)

            # Get last inserted id
            id = result.lastrowid
            query = db.select(Participant).where(Participant.participant_id == id)
            participant = db.session.scalars(query).first()

            # Save the user's group preferences
            for id in group_ids:
                ug = ParticipantGroup()
                ug.group_id = id
                ug.participant_id = participant.participant_id

                db.session.add(ug)
                db.session.commit()

            # Save reference to the inserted values in the session
            self._session['participant_id'] = participant.participant_id
            self._session['group_ids'] = group_ids
            self._session['weight_conf'] = WebsiteControl().get_conf().weight_configuration
            self._session['previous_comparison_id'] = None
            self._session['comparison_ids'] = []
            print(self._session)
        except SQLAlchemyError as e:
            raise RuntimeError(str(e))

        return self._redirect('.item_selection')

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
        user_components.append(
            render_template(
                'main/components/group.html',
                **{
                    'groups': groups,
                    'label': label_text,
                    'multiple_selection': multiple_selection,
                    'group_selection_error': error_text,
                },
            )
        )

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
                    user_components.append(f'<p>{item}</p>')

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
                        'ethics_link_text': WS.get_text(WS.USER_REGISTRATION_ETHICS_AGREEMENT_LINK_TEXT, self._app),
                    },
                )
            )
