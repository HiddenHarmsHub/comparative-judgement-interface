from marshmallow import RAISE, Schema, ValidationError, fields, pre_load, validate, validates_schema


class RankPostSchema(Schema):
    """Validate POST data submitted to the rank view."""

    def __init__(self, *, expected_item_ids, questions=(), none_allowed=False, ties_allowed=False, **kwargs):
        """Initialise the schema with various settings from the current study."""
        super().__init__(**kwargs)
        self.expected_item_ids = expected_item_ids
        self.question_ids = frozenset(int(question.question_id) for question in questions)
        self.none_allowed_fields = set(self.OPTIONAL_ID_FIELDS)
        self.ties_allowed = ties_allowed
        for question_id in self.question_ids:
            field_name = f"question_{question_id}"
            self.none_allowed_fields.add(field_name)

            question_field = fields.List(
                fields.Int(required=False, allow_none=True),
                required=True,
                allow_none=none_allowed,
            )
            self.fields[field_name] = question_field
            self.load_fields[field_name] = question_field

    class Meta:
        """Reject any unexpected keys."""

        unknown = RAISE

    OPTIONAL_ID_FIELDS = {
        "selected_item_id",
        "item_1_id",
        "item_2_id",
        "weighted_pair_id",
    }

    action = fields.Str(
        required=True,
        validate=validate.OneOf(["rejudged", "confirmed", "skipped"]),
    )
    selected_item_id = fields.Int(required=False, allow_none=True)
    item_1_id = fields.Int(required=False, allow_none=True)
    item_2_id = fields.Int(required=False, allow_none=True)
    weighted_pair_id = fields.Int(required=False, allow_none=True)

    @pre_load
    def normalise_question_responses(self, data, **kwargs):
        """Remove unselected entries from the list of responses (they are skips).

        Args:
            data (dict): Untrusted form values before field deserialisation.
            **kwargs: Additional Marshmallow hook arguments.

        Returns:
            dict: A copy of the payload with the question response lists normalised.
        """
        normalised = dict(data)
        for key in normalised:
            if key.startswith('question_'):
                normalised[key] = [x for x in normalised[key] if x != ""]
        return normalised

    @pre_load
    def normalise_optional_ids(self, data, **kwargs):
        """Convert blank optional HTML ID inputs to None before validation.

        Args:
            data (dict): Untrusted form values before field deserialisation.
            **kwargs: Additional Marshmallow hook arguments.

        Returns:
            dict: A copy of the payload with blank optional ID values set to
            ``None``.
        """
        normalised = dict(data)
        for field_name in self.none_allowed_fields:
            if normalised.get(field_name) == "":
                normalised[field_name] = None
        return normalised

    @validates_schema
    def validate_combinations(self, data, **kwargs):
        """Validate field combinations required for each rank action.

        Args:
            data (dict): Individually validated rank request values.
            **kwargs: Additional Marshmallow validator arguments.

        Raises:
            ValidationError: If the submitted fields are incompatible with the
                declared ranking action.
        """
        if data["item_1_id"] not in self.expected_item_ids or data["item_2_id"] not in self.expected_item_ids:
            raise ValidationError("the item ids returned were not the expected item ids.")

        if data["action"] == "skipped" and data.get("selected_item_id") is not None:
            raise ValidationError({"selected_item_id": ["selected_item_id must not be set when state is skipped."]})

        if data["selected_item_id"] is not None and data["selected_item_id"] not in self.expected_item_ids:
            raise ValidationError("the selected item id is not one of the items shown.")

        for question_id in self.question_ids:
            question_key = f"question_{question_id}"
            if self.ties_allowed:
                if len(data[question_key]) > 2:
                    raise ValidationError(f"the response for {question_key} is not within the expected repsonses")
            else:
                if len(data[question_key]) > 1:
                    raise ValidationError(f"the response for {question_key} is not within the expected repsonses")
