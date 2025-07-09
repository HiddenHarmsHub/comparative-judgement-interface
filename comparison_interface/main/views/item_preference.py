from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.expression import func

from comparison_interface.configuration.website import Settings as WS
from comparison_interface.db.connection import db
from comparison_interface.db.models import Item, ItemGroup, Participant, ParticipantGroup, ParticipantItem, WebsiteControl

from .request import Request


class ItemsPreference(Request):
    """This page allows the registered participant to specify which items are known and unknown.

    Only known items will be shown during the comparative judgment comparisons.
    """

    def get(self, _):
        """Request get handler."""
        if not self._valid_session():
            return self._redirect('.participant_registration')

        # The item selection won't be allow if either:
        # 1. Manual weights were defined.
        # 2. The participant explicitly configured the website to not render this section.
        render_item_preference = WS.should_render(WS.BEHAVIOUR_RENDER_USER_ITEM_PREFERENCE_PAGE, self._app)
        equal_weight_conf = self._session['weight_conf'] == WebsiteControl.EQUAL_WEIGHT
        if not equal_weight_conf or not render_item_preference:
            return self._redirect('.rank')

        # Get all items preferences not specified for the participant yet.
        query = (
            db.select(Participant, ParticipantGroup, ItemGroup, Item, ParticipantItem)
            .join(ParticipantGroup, ParticipantGroup.participant_id == Participant.participant_id, isouter=True)
            .join(ItemGroup, ItemGroup.group_id == ParticipantGroup.group_id, isouter=True)
            .join(Item, ItemGroup.item_id == Item.item_id, isouter=True)
            .join(ParticipantItem, (ParticipantItem.participant_id == Participant.participant_id) & (ParticipantItem.item_id == Item.item_id), isouter=True)
            .where(
                Participant.participant_id == self._session['participant_id'],
                ParticipantGroup.group_id.in_(self._session['group_ids']),
                ItemGroup.group_id.in_(self._session['group_ids']),
                # WARNING: Don't change test against None to "is None". It won't work correctly.
                ParticipantItem.participant_item_id == None,  # NoQA
            )
            .order_by(func.random())
        )
        result = db.session.execute(query).first()

        # After the participant had stated all items preferences
        # moves to the comparison itself.
        if not result:
            return self._redirect('.rank')

        # Render the item preference template
        _, _, _, item, _ = result
        return self._render_template(
            'main/pages/item_preference.html',
            {
                'item': item,
                'item_selection_question': WS.get_text(WS.ITEM_SELECTION_QUESTION_LABEL, self._app),
                'item_selection_answer_no': WS.get_text(WS.ITEM_SELECTION_NO_BUTTON_LABEL, self._app),
                'item_selection_answer_yes': WS.get_text(WS.ITEM_SELECTION_YES_BUTTON_LABEL, self._app),
            },
        )

    def post(self, request):
        """Request post handler."""
        response = request.form.to_dict(flat=True)

        known = False
        if response['action'] == 'agree':
            known = True

        # Save the participant preference into the database
        ui = ParticipantItem(participant_id=self._session['participant_id'], item_id=response['item_id'], known=known)

        try:
            db.session.add(ui)
            db.session.commit()
        except SQLAlchemyError as e:
            raise RuntimeError(str(e))

        return self._redirect('.item_selection')
