from marshmallow import RAISE, Schema, ValidationError, fields, pre_load, validate, validates_schema


class RankPostSchema(Schema):
    """Validate POST data submitted to the rank view."""

    class Meta:
        """Reject any unexpected keys."""
        unknown = RAISE

    OPTIONAL_ID_FIELDS = {
        "comparison_id",
        "selected_item_id",
        "item_1_id",
        "item_2_id",
        "weighted_pair_id",
    }

    state = fields.Str(
        required=True,
        validate=validate.OneOf(["rejudged", "confirmed", "skipped"]),
    )
    comparison_id = fields.Int(required=False, allow_none=True)
    selected_item_id = fields.Int(required=False, allow_none=True)
    item_1_id = fields.Int(required=False, allow_none=True)
    item_2_id = fields.Int(required=False, allow_none=True)
    weighted_pair_id = fields.Int(required=False, allow_none=True)

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
        for field_name in self.OPTIONAL_ID_FIELDS:
            if normalised.get(field_name) == "":
                normalised[field_name] = None
        return normalised

    @validates_schema
    def validate_action_shape(self, data, **kwargs):
        """Validate field combinations required for each rank action.

        Args:
            data (dict): Individually validated rank request values.
            **kwargs: Additional Marshmallow validator arguments.

        Raises:
            ValidationError: If the submitted fields are incompatible with the
                declared ranking action.
        """
        if data["state"] == "skipped" and data.get("selected_item_id") is not None:
            raise ValidationError(
                {"selected_item_id": ["selected_item_id must not be set when state is skipped."]}
            )

        if data["state"] != "rejudged" and (
            data.get("item_1_id") is None or data.get("item_2_id") is None
        ):
            raise ValidationError(
                {"item_1_id": ["item_1_id and item_2_id are required for new comparisons."]}
            )
