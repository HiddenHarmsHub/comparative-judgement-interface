from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.expression import func

from comparison_interface.configuration.website import Settings as WS
from comparison_interface.db.connection import db
from comparison_interface.db.models import (
    Comparison,
    CustomItemPair,
    Item,
    ItemGroup,
    Participant,
    ParticipantGroup,
    ParticipantItem,
    WebsiteControl,
)

from .request import Request


class Rank(Request):
    """Page to rank each of the items being compared."""

    # Available rank actions
    REJUDGE = 'rejudged'
    CONFIRMED = 'confirmed'
    SKIPPED = 'skipped'

    def get(self, request):
        """Request get handler."""
        if not self._valid_session():
            return self._redirect('.participant_registration')

        allow_ties = WS.get_behaviour_conf(WS.BEHAVIOUR_ALLOW_TIES, self._app)
        allow_skip = WS.get_behaviour_conf(WS.BEHAVIOUR_ALLOW_SKIP, self._app)
        allow_back = WS.get_behaviour_conf(WS.BEHAVIOUR_ALLOW_BACK, self._app)

        use_escape_route = WS.get_behaviour_conf(WS.BEHAVIOUR_ESCAPE_ROUTE, self._app)

        if use_escape_route and self._get_current_cycle() >= WS.get_behaviour_conf(WS.BEHAVIOUR_MAX_CYCLES, self._app):
            return self._redirect('.thankyou')

        comparison_id = None
        args = request.args.to_dict(flat=True)
        if 'comparison_id' in args:
            comparison_id = args['comparison_id']

        item_1, item_2 = self._get_items_to_compare(comparison_id)
        # Show a "no content error" in case of not enough selected known items.
        if item_1 is None or item_2 is None:
            return self._render_template(
                'main/204.html',
                {
                    'error_204_title': WS.get_text(WS.ERROR_204_TITLE, self._app),
                    'error_204_message': WS.get_text(WS.ERROR_204_MESSAGE, self._app),
                },
            )

        if comparison_id is not None:
            # if we are in a rejudging state get the current state to show to the participant
            current_state, selected_item_id = self._get_current_comparison_state(comparison_id)
        else:
            current_state = None
            selected_item_id = None

        # The participant can rejudge comparisons if:
        # - at least one comparison has already been made in the session
        # - there is a previous comparison id in the session.
        # this boolean determines whether the previous button is present or not
        can_rejudge = len(self._session['comparison_ids']) > 0 and self._session['previous_comparison_id'] is not None

        compared, skipped = self._get_comparison_stats()

        if use_escape_route:
            # If we have asked for an escape route check the counts and redirect if necessary
            completed_cycles = self._get_current_cycle()

            if compared + skipped >= WS.get_behaviour_conf(WS.BEHAVIOUR_CYCLE_LENGTH, self._app) * (
                completed_cycles + 1
            ):
                self._increment_cycle_count()
                return self._redirect('.thankyou')

        if allow_ties:
            additional_screen_reader_instructions = ""
        else:
            additional_screen_reader_instructions = WS.get_text(WS.ADDITIONAL_RADIO_BUTTON_INSTRUCTIONS, self._app)

        if allow_skip:
            confirm_button_error_message = WS.get_text(WS.CONFIRM_BUTTON_ERROR_MESSAGE_WITH_SKIP, self._app)
        else:
            confirm_button_error_message = WS.get_text(WS.CONFIRM_BUTTON_ERROR_MESSAGE_WITHOUT_SKIP, self._app)
        return self._render_template(
            'main/pages/rank.html',
            {
                'item_1': item_1,
                'item_2': item_2,
                'selected_item_label': WS.get_text(WS.RANK_ITEM_SELECTED_INDICATOR_LABEL, self._app),
                'tied_selection_label': WS.get_text(WS.RANK_ITEM_TIED_SELECTION_INDICATOR_LABEL, self._app),
                'skipped_selection_label': WS.get_text(WS.RANK_ITEM_SKIPPED_SELECTION_INDICATOR_LABEL, self._app),
                'rejudge_label': WS.get_text(WS.RANK_ITEM_REJUDGE_BUTTON_LABEL, self._app),
                'confirmed_label': WS.get_text(WS.RANK_ITEM_CONFIRMED_BUTTON_LABEL, self._app),
                'confirm_button_error_message': confirm_button_error_message,
                'skip_button_error_message': WS.get_text(WS.SKIP_BUTTON_ERROR_MESSAGE, self._app),
                'skipped_label': WS.get_text(WS.RANK_ITEM_SKIPPED_BUTTON_LABEL, self._app),
                'comparison_instruction_label': WS.get_text(WS.RANK_ITEM_INSTRUCTION_LABEL, self._app),
                'comparison_number_label': WS.get_text(WS.RANK_ITEM_COMPARISON_EXECUTED_LABEL, self._app),
                'comparison_number': compared,
                'skipped_number_label': WS.get_text(WS.RANK_ITEM_SKIPPED_COMPARISON_EXECUTED_LABEL, self._app),
                'skipped_number': skipped,
                'rejudge_value': self.REJUDGE,
                'confirmed_value': self.CONFIRMED,
                'skipped_value': self.SKIPPED,
                'can_rejudge': can_rejudge,
                'comparison_id': comparison_id,
                'initial_state': current_state,
                'initial_selected_item_id': selected_item_id,
                'allow_ties': str(allow_ties).lower(),
                'allow_skip': allow_skip,
                'allow_back': allow_back,
                'additional_screen_reader_instructions': additional_screen_reader_instructions,
                'item_group_selection_label': WS.get_text(WS.ITEM_SELECTION_GROUP_LABEL, self._app),
            },
        )

    def post(self, request):
        """Request post handler."""
        response = request.form.to_dict(flat=True)
        action = response['state']
        if action != self.REJUDGE:
            # Set the comparison state based on the participant's action
            state, selected_item_id = self._calculate_comparison_state(action, response)

            # Verify if the participant want to rejudge an item
            comparison_id = None
            if 'comparison_id' in response and response['comparison_id'] != "":
                comparison_id = response['comparison_id']

            if comparison_id is None:
                # Save the new participant comparison in the database.
                c = Comparison(
                    participant_id=self._session['participant_id'],
                    item_1_id=response['item_1_id'],
                    item_2_id=response['item_2_id'],
                    state=state,
                    selected_item_id=selected_item_id,
                )
                try:
                    db.session.add(c)
                    db.session.commit()
                    # Save the comparison for future possible rejudging
                    self._session['previous_comparison_id'] = c.comparison_id
                    self._session['comparison_ids'] = self._session['comparison_ids'] + [c.comparison_id]
                except SQLAlchemyError as e:
                    raise RuntimeError(str(e))
            else:
                # Rejudge an existence comparison.
                query = db.select(Comparison).where(
                    Comparison.comparison_id == comparison_id,
                    Comparison.participant_id == self._session['participant_id'],
                )
                comparison = db.session.scalars(query).first()

                if comparison is None:
                    raise RuntimeError("Invalid comparison id provided")
                try:
                    comparison.selected_item_id = selected_item_id
                    comparison.state = state
                    comparison.updated = datetime.now(timezone.utc)
                    db.session.commit()
                    # Return the pointer to the last comparison made because the participant will be given a new one next
                    self._session['previous_comparison_id'] = self._session['comparison_ids'][
                        len(self._session['comparison_ids']) - 1
                    ]
                except SQLAlchemyError as e:
                    raise RuntimeError(str(e))

            return self._redirect('.rank')
        else:
            return self._redirect('.rank', comparison_id=self._session['previous_comparison_id'])

    def _get_current_comparison_state(self, comparison_id):
        """Get the current comparison state and selected item id for the requested comparison id.

        Args:
            comparison_id (int): The primary key of the comparison to retrieve
        """
        res = (
            db.session.query(Comparison.state, Comparison.selected_item_id)
            .where(Comparison.comparison_id == comparison_id)
            .first()
        )
        return res

    def _calculate_comparison_state(self, action: str, response: dict):
        """Get the right comparison parameters based on the participant's action.

        Args:
            action (str): Action triggered by the participant
            response (dict): POST from response

        Returns:
            state: Comparison state | None
            selected_item_id: Selected item | None
        """
        state = None
        selected_item_id = None
        if action == self.CONFIRMED and ('selected_item_id' not in response or response['selected_item_id'] == ""):
            state = Comparison.TIED

        if action == self.CONFIRMED and 'selected_item_id' in response and response['selected_item_id'] != "":
            state = Comparison.SELECTED
            selected_item_id = response['selected_item_id']

        if action == self.SKIPPED:
            state = Comparison.SKIPPED

        return state, selected_item_id

    def _get_current_cycle(self):
        """Get the current cycle count for this participant.

        Returns:
            cycle_count: current cycle of the participant
        """
        participant = db.session.get(Participant, self._session['participant_id'])
        if participant is None:
            return 0
        return participant.completed_cycles

    def _increment_cycle_count(self):
        """Increment the current participant's cycle count."""
        participant = db.session.get(Participant, self._session['participant_id'])
        participant.completed_cycles = participant.completed_cycles + 1
        db.session.commit()

    def _get_comparison_stats(self):
        """Get summary statistics about the comparison made.

        Returns:
            compared: Number of comparisons made
            skipped: Number of comparisons skipped
        """
        compared = 0
        skipped = 0

        query = (
            db.select(Comparison.state, func.count(Comparison.comparison_id))
            .where(Comparison.participant_id == self._session['participant_id'])
            .group_by(Comparison.state)
        )
        counts = db.session.execute(query).all()

        if len(counts) == 0:
            return compared, skipped

        for states in counts:
            stateName, number = states
            if stateName == Comparison.SELECTED or stateName == Comparison.TIED:
                compared = compared + number
            if stateName == Comparison.SKIPPED:
                skipped = number

        return compared, skipped

    def _get_items_to_compare(self, comparison_id=None):
        """Get the items to compare.

        Args:
            comparison_id (int, optional): Gets the items related to a particular comparison. This parameter allows
            the rejudging functionality. Defaults to None.

        Returns:
            Item: Model Item | None
            Item: Model Item | None
        """
        render_item_prefer = WS.should_render(WS.BEHAVIOUR_RENDER_USER_ITEM_PREFERENCE_PAGE, self._app)

        # Case 1: Returns the items related to a particular comparison.
        if comparison_id is not None:
            return self._get_comparison_items(comparison_id)

        # Case 2: Get a random pair from list of custom defined weights
        if self._session['weight_conf'] == WebsiteControl.CUSTOM_WEIGHT:
            return self._get_custom_items()

        # Case 3: Get a random item pair when equal weights and item preference was defined
        if self._session['weight_conf'] == WebsiteControl.EQUAL_WEIGHT and render_item_prefer:
            return self._get_preferred_items()

        # Case 4: Get a random item pair when equal weights and no item preference was defined
        if self._session['weight_conf'] == WebsiteControl.EQUAL_WEIGHT and not render_item_prefer:
            return self._get_random_items()

        # All no implemented cases
        return None, None

    def _get_comparison_items(self, comparison_id: int):
        """Get the items related to a particular comparison already made.

        Also reset the session information to record the new previous comparison id (allows previous to be used again).

        Args:
            comparison_id (int): Comparison id to be rejudged

        Raises:
            RuntimeError: Invalid comparison id provided

        Returns:
            Item: Model Item | None
            Item: Model Item | None
        """
        # 1. Get the items related to the comparison.
        query = db.select(Comparison).where(
            Comparison.comparison_id == comparison_id, Comparison.participant_id == self._session['participant_id']
        )
        comparison = db.session.scalars(query).first()

        if comparison is None:
            raise RuntimeError("Invalid comparison id provided")

        # 2. Get the items information)
        query = db.select(Item).where(Item.item_id.in_([comparison.item_1_id, comparison.item_2_id]))
        items = db.session.scalars(query).all()

        # 3. Update the session parameters
        comparison_id_index = self._session['comparison_ids'].index(int(comparison_id))
        if comparison_id_index == 0:
            self._session['previous_comparison_id'] = None
        else:
            self._session['previous_comparison_id'] = self._session['comparison_ids'][comparison_id_index - 1]
        # return them in the order they were originally displayed
        if items[0].item_id == comparison.item_1_id:
            return items[0], items[1]
        return items[1], items[0]

    def _get_custom_items(self):
        """Get a random pair of items respecting the weights provided in config file.

        Returns:
            Item: Model Item | None
            Item: Model Item | None
        """
        # 1. Get the the custom pairs. This query assumes that just one group
        # can be selected by the participant when defining custom weights.
        query = (
            db.select(ParticipantGroup, CustomItemPair)
            .join(CustomItemPair, CustomItemPair.group_id == ParticipantGroup.group_id, isouter=True)
            .where(
                ParticipantGroup.participant_id == self._session['participant_id'],
                ParticipantGroup.group_id.in_(self._session['group_ids']),
            )
        )
        result = db.session.execute(query).all()
        pair_ids = []
        pair_weights = []
        pairs = {}
        for _, p in result:
            pairs[p.custom_item_pair_id] = p
            pair_ids.append(p.custom_item_pair_id)
            pair_weights.append(p.weight)
        if len(pair_ids) == 0:
            return None, None

        # 2. Select the item pair to compare but respecting the custom weights
        pair_id = self._app.rng.choice(pair_ids, 1, p=pair_weights, replace=False)
        item_1_id = pairs[pair_id[0]].item_1_id
        item_2_id = pairs[pair_id[0]].item_2_id

        # 3. Get the items information
        query = db.select(Item).where(Item.item_id.in_([item_1_id, item_2_id]))
        items = db.session.scalars(query).all()

        return items[0], items[1]

    def _get_preferred_items(self):
        """Get a random pair of items from the preferred participant's item selection.

        Returns:
            Item: Model Item | None
            Item: Model Item | None
        """
        # 1. Get the participant's item preferences
        query = (
            db.select(ParticipantItem, Item)
            .join(Item, Item.item_id == ParticipantItem.item_id, isouter=True)
            .where(ParticipantItem.participant_id == self._session['participant_id'], ParticipantItem.known == 1)
        )
        result = db.session.execute(query).all()

        items_id = []
        items = {}
        for _, i in result:
            # Insert only unique values to guarantee an equal item distribution.
            if i.item_id not in items_id:
                items_id.append(i.item_id)
                items[i.item_id] = i

        if len(items_id) < 2:
            return None, None

        # 2. Select randomly two items from the participant's item preferences
        selected_items_id = [None, None]
        selected_items_id = self._app.rng.choice(items_id, 2, replace=False)

        return items[selected_items_id[0]], items[selected_items_id[1]]

    def _get_random_items(self):
        """Get a random pair of items from the website configuration list.

        Returns:
            Item: Model Item | None
            Item: Model Item | None
        """
        # 1. Get the items related to the participant's group preferences
        query = (
            db.select(ParticipantGroup, ItemGroup, Item)
            .join(ItemGroup, ItemGroup.group_id == ParticipantGroup.group_id, isouter=True)
            .join(Item, ItemGroup.item_id == Item.item_id, isouter=True)
            .where(
                ParticipantGroup.participant_id == self._session['participant_id'],
                ParticipantGroup.group_id.in_(self._session['group_ids']),
                ItemGroup.group_id.in_(self._session['group_ids']),
            )
        )
        result = db.session.execute(query).all()

        items_id = []
        items = {}
        for _, _, i in result:
            # Insert only unique values to guarantee an equal item distribution.
            if i.item_id not in items_id:
                items_id.append(i.item_id)
                items[i.item_id] = i

        if len(items_id) < 2:
            return None, None

        # 2. Select randomly two items using the participant's group preferences
        selected_items_id = [None, None]
        selected_items_id = self._app.rng.choice(items_id, 2, replace=False)

        return items[selected_items_id[0]], items[selected_items_id[1]]
