from marshmallow import RAISE, Schema, ValidationError, fields, validate, validates_schema


class ItemPreferencePostSchema(Schema):
    """Validate POST data submitted to the item_preference view."""

    class Meta:
        """Reject any unexpected keys."""

        unknown = RAISE

    action = fields.Str(required=True, validate=validate.OneOf(["agree", "disagree"]))
    item_id = fields.Int(required=True, validate=validate.Range(min=1))

    @validates_schema
    def check_action(self, data, **kwargs):
        """Validate the action types, can be extended if needed."""
        if data["action"] not in {"agree", "disagree"}:
            raise ValidationError({"action": ["Invalid action."]})
