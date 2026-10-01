"""Marshmallow schemas for runtime request validation."""

from marshmallow import RAISE, Schema, ValidationError, fields, pre_load, validate, validates_schema
from sqlalchemy import Boolean, Date, DateTime, Integer, String


class RankPostSchema(Schema):
    """Validate POST data submitted by the ranking view."""

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

        HTML forms submit an empty hidden input as ``""``. Marshmallow's
        ``allow_none=True`` accepts Python ``None``, not an empty string, so
        only blank values for known optional ID fields are normalised. Any
        non-blank, non-integer value remains invalid and is rejected by
        ``fields.Int``.

        Args:
            data (dict): Untrusted form values before field deserialisation.
            **kwargs: Additional Marshmallow hook arguments.

        Returns:
            dict: A copy of the payload with blank optional ID values set to
            ``None``.
        """
        normalised = dict(data)
        for field_name in self.OPTIONAL_ID_FIELDS:
            if normalised.get(field_name) == "" or normalised.get(field_name) == "None":
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



class ParticipantSchemaFactory:
    """Build a participant write schema from reflected SQLAlchemy columns.

    Every reflected participant column is writable by default, except the
    explicitly named system-managed fields. This suits studies where all
    config-created participant columns are intended to be registration fields.
    """

    SYSTEM_FIELDS = {
        "participant_id": fields.Int(dump_only=True),
        "created_date": fields.DateTime(dump_only=True),
        "completed_cycles": fields.Int(dump_only=True),
    }

    @classmethod
    def build_from_table(
        cls,
        table,
        require_ethics_acceptance=False,
        ethics_field="accepted_ethics_agreement",
    ):
        """Return a Marshmallow schema class based on a reflected table.

        SQL column nullability supplies the required/optional rule and string
        column lengths supply maximum-length validation. The named system
        fields are dump-only, so browser input for them is rejected while
        server code may still add them after ``schema.load()``.

        Args:
            table (sqlalchemy.Table): Reflected ``participant`` table.
            require_ethics_acceptance (bool): Require a truthy ethics field.
            ethics_field (str): Dynamic participant column that records ethics
                acceptance when the requirement is enabled.

        Returns:
            type[marshmallow.Schema]: A configured schema class. Instantiate it
            once and reuse the instance for participant registration.

        Raises:
            ValueError: If ethics acceptance is required but its column is
                absent, or is not represented by a Boolean SQL column.
        """
        attrs = {
            "Meta": type("Meta", (), {"unknown": RAISE}),
            **cls.SYSTEM_FIELDS,
        }

        for column in table.columns:
            if column.name in cls.SYSTEM_FIELDS:
                continue
            attrs[column.name] = cls._field_for_column(column)

        if require_ethics_acceptance:
            ethics_column = table.columns.get(ethics_field)
            if ethics_column is None:
                raise ValueError(
                    f"Ethics acceptance is required but '{ethics_field}' is not a participant column."
                )

            def validate_ethics_acceptance(self, data, **kwargs):
                """Require the configured ethics checkbox to be accepted.

                Args:
                    data (dict): Individually validated participant values.
                    **kwargs: Additional Marshmallow validator arguments.

                Raises:
                    ValidationError: If the ethics checkbox is not truthy.
                """
                if not data.get(ethics_field):
                    raise ValidationError(
                        {ethics_field: ["Ethics agreement must be accepted to register."]}
                    )

            attrs["validate_ethics_acceptance"] = validates_schema(
                validate_ethics_acceptance
            )

        return type("ParticipantWriteSchema", (Schema,), attrs)

    @staticmethod
    def _field_for_column(column):
        """Create the Marshmallow input field corresponding to one SQL column.

        Args:
            column (sqlalchemy.Column): A non-system reflected participant
                column.

        Returns:
            marshmallow.fields.Field: Input field with type, nullability, and
            string-length constraints inferred from the SQL column.
        """
        options = {
            "required": not column.nullable,
            "allow_none": column.nullable,
        }

        if isinstance(column.type, Boolean):
            return fields.Bool(**options)
        if isinstance(column.type, Integer):
            return fields.Int(**options)
        if isinstance(column.type, DateTime):
            return fields.DateTime(**options)
        if isinstance(column.type, Date):
            return fields.Date(**options)
        if isinstance(column.type, String):
            max_length = getattr(column.type, "length", None)
            if max_length is not None:
                options["validate"] = validate.Length(max=max_length)
            return fields.Str(**options)

        # Dynamic participant fields should normally use one of the types
        # above. Treat an unrecognised column type as text rather than passing
        # an unchecked value through to the database.
        return fields.Str(**options)
