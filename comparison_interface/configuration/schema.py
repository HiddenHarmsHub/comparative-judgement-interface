import itertools
import os
import re

from marshmallow import Schema, ValidationError, fields, post_load, validate, validates
from PIL import Image

from ..db.models import WebsiteControl
from .website import Settings as WS


class Item(Schema):
    """The schema for an item (image plus metadata)."""

    id = fields.Int(required=False)
    name = fields.Str(required=True, validate=[validate.Length(min=1, max=200)])
    displayName = fields.Str(required=True, validate=[validate.Length(min=1, max=200)])
    imageName = fields.Str(required=True, validate=[validate.Length(min=1, max=500)])
    imageDescription = fields.Str(required=False)

    # Allowed Items Image size
    MIN_WIDTH = 300
    MIN_HEIGHT = 300

    @validates('name')
    def _validate_name(self, name, data_key):
        match = re.match(r'^[a-zA-Z0-9_-]+$', name)
        if not match:
            raise ValidationError(
                "Name can be only alpha numeric lower case values with underscores or dashes. "
                "i.e. this_is_a_valid_name. If you are using a csv file for the comparison configuration then you "
                "will either need to supply a column with the title 'item name' which complies with the criteria "
                "above or remove any special characters from the 'item display name' column."
            )

    @validates('imageName')
    def _validate_image_path(self, image_name, data_key):
        path = os.path.abspath(os.path.dirname(__file__)) + "/../static/images/" + image_name
        if not os.path.exists(path):
            raise ValidationError(f"Image {image_name} not found on static/images/ folder.")

        try:
            im = Image.open(path)
            h, w = im.size
            if h < self.MIN_HEIGHT or w < self.MIN_WIDTH:
                raise ValidationError(f"All item images must be at least {self.MIN_HEIGHT}x{self.MIN_WIDTH}px")
        except Exception as e:
            raise ValidationError(str(e))


class Weight(Schema):
    """The schema for a Weight."""

    item_1 = fields.Str(required=True, validate=[validate.Length(min=1, max=200)])
    item_2 = fields.Str(required=True, validate=[validate.Length(min=1, max=200)])
    weight = fields.Float(required=True, validate=[validate.Range(min=0.0, max=1.0)])

    @validates('item_1', 'item_2')
    def _validate_item_name(self, name, data_key):
        match = re.match(r'^[a-z0-9_-]+$', name)
        if not match:
            raise ValidationError(
                "Weight items name can be only alpha numeric lower case values with underscores or dashes. "
                "i.e. this_is_a_valid_name"
            )


class Group(Schema):
    """The schema for a Group."""

    name = fields.Str(required=True, validate=[validate.Length(min=1, max=200)])
    displayName = fields.Str(required=True, validate=[validate.Length(min=1, max=200)])
    items = fields.List(fields.Nested(Item()), required=True, validate=[validate.Length(min=1, max=1000)])
    weight = fields.List(fields.Nested(Weight()), required=False, validate=[validate.Length(min=1, max=499500)])

    @validates('items')
    def _validate_unique_names(self, items, data_key):
        names = []
        for f in items:
            if "name" not in f:
                continue

            if f['name'] in names:
                raise ValidationError(
                    "All items in the same group must have an unique name. Repeated name {}".format(f['name'])
                )
            else:
                names.append(f['name'])

    @validates('items')
    def _validate_consistent_ids(self, items, data_key):
        if "id" not in items[0]:
            ids_specified = False
        else:
            ids_specified = True
        for f in items:
            if ("id" not in f and ids_specified) or ("id" in f and not ids_specified):
                raise ValidationError("If any ids are specified for items then all items must have an id.")

    @validates('weight')
    def _validate_weight_sum(self, weights, data_key):
        w = 0
        for g in weights:
            w += g['weight']

        if w < 0.98 or w > 1.02:
            raise ValidationError(f"Custom weights for item's pairs must sum close to 1. Actual weight sum {w}.")

    @post_load
    def _post_load_validation(self, data, **kwargs):
        if 'weight' not in data:
            return data

        # Validate item pairs name when defined
        items = data['items']
        weights = data['weight']
        items_name = [i['name'] for i in items]
        pairs = []
        for w in weights:
            if w['item_1'] not in items_name:
                raise ValidationError(f"{w['item_1']} not defined as item name.")
            if w['item_2'] not in items_name:
                raise ValidationError(f"{w['item_2']} not defined as item name.")

            # The order of the pair is important to validate the combinations
            pairs.append((w['item_1'], w['item_2']))
            pairs.append((w['item_2'], w['item_1']))

        # Validate that a weight was custom defined for all item pairs
        possible_pair_combinations = list(itertools.combinations(items_name, 2))
        for pair in possible_pair_combinations:
            if pair not in pairs:
                raise ValidationError(f"Custom weight for item pair {pair} needs to be defined.")
        return data

    @validates('name')
    def _validate_group_name(self, name, data_key):
        match = re.match(r'^[a-z0-9_-]+$', name)
        if not match:
            raise ValidationError(
                "Group name can be only alpha numeric lower case values with underscores or dashes. "
                "i.e. this_is_a_valid_name. If you are using a csv file for the comparison configuration then you "
                "will either need to supply a column with the title 'group name' which complies with the criteria "
                "above or remove any special characters from the 'group display name' column."
            )


class ComparisonConfiguration(Schema):
    """The schema for the comparison configuration."""

    csvFile = fields.Str(required=False)
    weightConfiguration = fields.Str(required=False)
    groups = fields.List(fields.Nested(Group()), required=False, validate=[validate.Length(min=1, max=100)])

    @post_load
    def _post_load_validation(self, data, **kwargs):
        if 'csvFile' in data:
            # then we shouldn't have any other keys at all
            if 'weightConfiguration' in data or 'groups' in data:
                raise ValidationError(
                    "If a CSV file is specified then neither the weightConfiguration nor groups keys should be "
                    "present in the JSON configuration file."
                )
        else:
            if 'weightConfiguration' not in data or 'groups' not in data:
                raise ValidationError(
                    "Both the 'weightConfiguration' and 'groups' keys are required if a csv file is not being used "
                    "for the image configuration."
                )
            weight_conf = data['weightConfiguration']
            groups = data['groups']
            item_weight_conf = sum([1 if "weight" in g else 0 for g in groups])

            if item_weight_conf != 0 and weight_conf == WebsiteControl.EQUAL_WEIGHT:
                raise ValidationError(
                    "Custom weight configuration is not allowed when the weight configuration was defined as 'equal'."
                )

            if item_weight_conf != len(groups) and weight_conf == WebsiteControl.CUSTOM_WEIGHT:
                raise ValidationError(
                    "Custom weight configuration is required for all groups when the "
                    "weight configuration was defined as 'custom'."
                )

        return data


class WebsiteTextConfiguration(Schema):
    """The schema for the website text configuration."""

    websiteTitle = fields.Str(required=True, validate=[validate.Length(min=1, max=100)])
    pageTitleLogout = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    pageTitleUserRegistration = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    pageTitleEthicsAgreement = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    pageTitlePolicies = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    pageTitleIntroduction = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    pageTitleItemPreference = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    pageTitleRank = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    pageTitleThankYou = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    userRegistrationGroupQuestionLabel = fields.Str(required=False, validate=[validate.Length(min=1, max=500)])
    userRegistrationFormTitleLabel = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    userRegistrationSummitButtonLabel = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    userRegistrationGroupSelectionErr = fields.Str(required=False, validate=[validate.Length(min=1, max=500)])
    userRegistrationEthicsAgreementLabel = fields.Str(required=True, validate=[validate.Length(min=1, max=500)])
    userRegistrationEthicsAgreementLinkText = fields.Str(required=True, validate=[validate.Length(min=1, max=500)])
    itemSelectionQuestionLabel = fields.Str(required=False, validate=[validate.Length(min=1, max=500)])
    itemSelectionYesButtonLabel = fields.Str(required=False, validate=[validate.Length(min=1, max=50)])
    itemSelectionNoButtonLabel = fields.Str(required=False, validate=[validate.Length(min=1, max=50)])
    itemSelectedIndicatorLabel = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    rankItemTiedSelectionIndicatorLabel = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    rankItemSkippedIndicatorLabel = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    rankItemItemRejudgeButtonLabel = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    rankItemConfirmedButtonLabel = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    rankItemSkippedButtonLabel = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    rankItemInstructionLabel = fields.Str(required=True, validate=[validate.Length(min=1, max=500)])
    rankItemComparisonExecutedLabel = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    rankItemSkippedComparisonExecutedLabel = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    confirmButtonErrorMessageWithSkip = fields.Str(required=True, validate=[validate.Length(min=1, max=1000)])
    confirmButtonErrorMessageWithoutSkip = fields.Str(required=True, validate=[validate.Length(min=1, max=1000)])
    skipButtonErrorMessage = fields.Str(required=True, validate=[validate.Length(min=1, max=1000)])
    additionalRadioButtonInstructions = fields.Str(required=True, validate=[validate.Length(min=1, max=1000)])
    itemSelectionGroupLabel = fields.Str(required=True, validate=[validate.Length(min=1, max=100)])
    introductionContinueButtonLabel = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    thankYouContinueButtonLabel = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    thankYouTitle = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    thankYouOpeningText = fields.Str(required=True, validate=[validate.Length(min=0, max=500)])
    thankYouContinueText = fields.Str(required=True, validate=[validate.Length(min=0, max=500)])
    thankYouStopText = fields.Str(required=True, validate=[validate.Length(min=0, max=500)])
    ethicsAgreementBackButtonLabel = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    sitePoliciesBackButtonLabel = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    siteCookiesAcceptButtonLabel = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    siteCookiesTitle = fields.Str(required=True, validate=[validate.Length(min=1, max=1000)])
    siteCookiesText = fields.Str(required=True, validate=[validate.Length(min=1, max=1000)])
    error500Title = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    error500Message = fields.Str(required=True, validate=[validate.Length(min=1, max=1000)])
    error404Title = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    error404Message = fields.Str(required=True, validate=[validate.Length(min=1, max=1000)])
    error404HomeLink = fields.Str(required=True, validate=[validate.Length(min=1, max=1000)])
    error204Title = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    error204Message = fields.Str(required=True, validate=[validate.Length(min=1, max=1000)])
    additionalRegistrationPageText = fields.List(fields.Str(), required=False)


class UserField(Schema):
    """The schema for a user."""

    name = fields.Str(required=True, validate=[validate.Length(min=1, max=100)])
    displayName = fields.Str(required=True, validate=[validate.Length(min=1, max=100)])
    type = fields.Str(
        required=True,
        validate=[
            validate.OneOf(
                [
                    WS.USER_FIELD_TYPE_TEXT,
                    WS.USER_FIELD_TYPE_INT,
                    WS.USER_FIELD_TYPE_DROPDOWN,
                    WS.USER_FIELD_TYPE_RADIO,
                    WS.USER_FIELD_TYPE_EMAIL,
                ]
            )
        ],
    )
    maxLimit = fields.Int()
    minLimit = fields.Int()
    required = fields.Boolean(required=True)
    option = fields.List(fields.Str(), validate=[validate.Length(min=1, max=20)])

    @validates('name')
    def _validate_name(self, name, data_key):
        match = re.match(r'^[a-z0-9_-]+$', name)
        if not match:
            raise ValidationError(
                "Name can be only alpha numeric lower case values with underscores or dashes. i.e. this_is_a_valid_name"
            )

    @post_load
    def _post_load_validation(self, data, **kwargs):
        # Validate option definition for dropdown and radio fields
        if data['type'] in [WS.USER_FIELD_TYPE_DROPDOWN, WS.USER_FIELD_TYPE_RADIO] and 'option' not in data:
            raise ValidationError(f"{data['type']} fields require the definition of the option field.")

        # Validate no option definition for no dropdown or radio fields
        if data['type'] not in [WS.USER_FIELD_TYPE_DROPDOWN, WS.USER_FIELD_TYPE_RADIO] and 'option' in data:
            raise ValidationError(f"Option field cannot be defined for {data['type']} fields.")

        # Validate max limit for email, text and int fields
        if (
            data['type'] in [WS.USER_FIELD_TYPE_TEXT, WS.USER_FIELD_TYPE_INT, WS.USER_FIELD_TYPE_EMAIL]
            and 'maxLimit' not in data
        ):
            raise ValidationError(f"{data['type']} fields require the definition of the numerical maxLimit field.")

        # Validate not max limit for not email, text or int fields
        if (
            data['type'] not in [WS.USER_FIELD_TYPE_TEXT, WS.USER_FIELD_TYPE_INT, WS.USER_FIELD_TYPE_EMAIL]
            and 'maxLimit' in data
        ):
            raise ValidationError(f"MaxLimit field cannot be defined for {data['type']} fields.")

        # Validate min limit for int field
        if data['type'] in [WS.USER_FIELD_TYPE_INT] and 'minLimit' not in data:
            raise ValidationError(f"{data['type']} fields require the definition of the numerical minLimit field.")

        # Validate not min limit for not  int fields
        if data['type'] not in [WS.USER_FIELD_TYPE_INT] and 'minLimit' in data:
            raise ValidationError(f"MinLimit field cannot be defined for {data['type']} fields.")

        return data


class BehaviourConfiguration(Schema):
    """The schema for the behaviour configuration."""

    exportPathLocation = fields.Str(required=True, validate=[validate.Length(min=1, max=500)])
    renderUserItemPreferencePage = fields.Boolean(required=True)
    renderUserInstructionPage = fields.Boolean(required=True)
    renderEthicsAgreementPage = fields.Boolean(required=True)
    renderSitePoliciesPage = fields.Boolean(required=True)
    renderCookieBanner = fields.Boolean(required=True)
    offerEscapeRouteBetweenCycles = fields.Boolean(required=True)
    cycleLength = fields.Integer(required=False)
    maximumCyclesPerUser = fields.Integer(required=False)
    allowTies = fields.Boolean(required=True)
    allowSkip = fields.Boolean(required=True)
    allowBack = fields.Boolean(required=True)
    userInstructionHtml = fields.Str(required=False, validate=[validate.Length(min=1, max=100)])
    userEthicsAgreementHtml = fields.Str(required=False, validate=[validate.Length(min=1, max=100)])
    sitePoliciesHtml = fields.Str(required=False, validate=[validate.Length(min=1, max=100)])

    @post_load
    def _post_load_validation(self, data, **kwargs):
        if data['renderEthicsAgreementPage'] and 'userEthicsAgreementHtml' not in data:
            raise ValidationError("The userEthicsAgreementHtml field is required if renderEthicsAgreementPage is true")

        if data['renderUserInstructionPage'] and 'userInstructionHtml' not in data:
            raise ValidationError("The userInstructionHtml field is required if renderUserInstructionPage is true")

        if data['renderSitePoliciesPage'] and 'sitePoliciesHtml' not in data:
            raise ValidationError("The sitePoliciesHtml field is required if renderSitePoliciesPage is true")

        if data['offerEscapeRouteBetweenCycles'] and ('cycleLength' not in data or 'maximumCyclesPerUser' not in data):
            raise ValidationError(
                "The fields cycleLength and maximumCyclesPerUser are both required if offerEscapeRouteBetweenCycles "
                "is true"
            )

        return data


class Configuration(Schema):
    """The schema for the full configuration."""

    behaviourConfiguration = fields.Nested(BehaviourConfiguration(), required=True)
    comparisonConfiguration = fields.Nested(ComparisonConfiguration(), required=True)
    websiteTextConfiguration = fields.Nested(WebsiteTextConfiguration(), required=True)
    userFieldsConfiguration = fields.List(
        fields.Nested(UserField()), required=True, validate=[validate.Length(min=0, max=20)]
    )

    @validates('userFieldsConfiguration')
    def _validate_unique_names(self, fields, data_key):
        names = []
        for f in fields:
            if f['name'] in names:
                raise ValidationError(
                    "All defined user fields must have a unique name. Repeated name {}".format(f['name'])
                )
            else:
                names.append(f['name'])

    @post_load
    def _post_load_validation(self, data, **kwargs):
        render_item_preference = data['behaviourConfiguration']['renderUserItemPreferencePage']

        if 'weightConfiguration' in data['comparisonConfiguration']:
            # Check that we are not trying to render item preferences it we are using custom weights
            weight_conf = data['comparisonConfiguration']['weightConfiguration']
            if weight_conf == WebsiteControl.CUSTOM_WEIGHT and render_item_preference:
                raise ValidationError(
                    "User item preference section cannot be rendered when defining a manual weight configuration. "
                    "Please change renderUserItemPreferencePage to false"
                )

        # Check that if we want to show the item selection page we have the required text field too
        if render_item_preference and ('itemSelectionQuestionLabel' not in data['websiteTextConfiguration']):
            raise ValidationError(
                "If renderUserItemPreferencePage is true then itemSelectionQuestionLabel must be provided in the "
                "websiteTextConfiguration section."
            )
        if render_item_preference and (
            'itemSelectionYesButtonLabel' not in data['websiteTextConfiguration']
            or 'itemSelectionNoButtonLabel' not in data['websiteTextConfiguration']
        ):
            raise ValidationError(
                "If renderUserItemPreferencePage is true then itemSelectionYesButtonLabel and"
                "itemSelectionYesButtonLabel must be provided in the websiteTextConfiguration section."
            )

        # Check that if we have defined multiple groups then we have the relevant selection/error text available
        if 'groups' in data['comparisonConfiguration'] and len(data['comparisonConfiguration']['groups']) > 1:
            if (
                'userRegistrationGroupQuestionLabel' not in data['websiteTextConfiguration']
                or 'userRegistrationGroupSelectionErr' not in data['websiteTextConfiguration']
            ):
                raise ValidationError(
                    "If multiple item groups are defined then both userRegistrationGroupQuestionLabel and "
                    "userRegistrationGroupSelectionErr must be provided in the websiteTextConfiguration section."
                )

        return data
