import json
import os

from .csv_processor import CsvProcessor


class Settings:
    """The configuration settings for this instance of the website."""

    # Json configuration object
    configuration = None

    # Configuration file key values
    CONFIGURATION_LOCATION = "CONFIG_LOC"
    # Website configuration sections
    CONFIGURATION_BEHAVIOUR = "behaviourConfiguration"
    CONFIGURATION_COMPARISON = "comparisonConfiguration"
    CONFIGURATION_USER_FIELDS = "userFieldsConfiguration"
    CONFIGURATION_WEBSITE_TEXT = "websiteTextConfiguration"
    # Website behaviour configuration keys
    BEHAVIOUR_EXPORT_PATH_LOCATION = "exportPathLocation"
    BEHAVIOUR_RENDER_USER_ITEM_PREFERENCE_PAGE = "renderUserItemPreferencePage"
    BEHAVIOUR_RENDER_USER_INSTRUCTION_PAGE = "renderUserInstructionPage"
    BEHAVIOUR_RENDER_ETHICS_AGREEMENT_PAGE = "renderEthicsAgreementPage"
    BEHAVIOUR_RENDER_SITE_POLICIES = "renderSitePoliciesPage"
    BEHAVIOUR_RENDER_COOKIE_BANNER = "renderCookieBanner"
    BEHAVIOUR_ESCAPE_ROUTE = "offerEscapeRouteBetweenCycles"
    BEHAVIOUR_CYCLE_LENGTH = "cycleLength"
    BEHAVIOUR_MAX_CYCLES = "maximumCyclesPerUser"
    BEHAVIOUR_ALLOW_TIES = "allowTies"
    BEHAVIOUR_ALLOW_SKIP = "allowSkip"
    BEHAVIOUR_ALLOW_BACK = "allowBack"
    BEHAVIOUR_USER_INSTRUCTION_HTML = "userInstructionHtml"
    BEHAVIOUR_ETHICS_AGREEMENT_HTML = "userEthicsAgreementHtml"
    BEHAVIOUR_SITE_POLICIES_HTML = "sitePoliciesHtml"
    # Group related configuration keys
    GROUPS = "groups"
    GROUP_WEIGHT_CONFIGURATION = "weightConfiguration"
    GROUP_NAME = "name"
    GROUP_DISPLAY_NAME = "displayName"
    GROUP_ITEMS = "items"
    GROUP_ITEMS_WEIGHT = "weight"
    # Items related configuration keys
    ITEM_ID = "id"
    ITEM_NAME = "name"
    ITEM_GROUP_ID = "group_id"
    ITEM_DISPLAY_NAME = "displayName"
    ITEM_IMAGE_DESCRIPTION = "imageDescription"
    ITEM_IMAGE_NAME = "imageName"
    # User fields configuration fields
    USER_FIELD_NAME = "name"
    USER_FIELD_DISPLAY_NAME = "displayName"
    USER_FIELD_TYPE = "type"
    USER_FIELD_MAX_LIMIT = "maxLimit"
    USER_FIELD_MIN_LIMIT = "minLimit"
    USER_FIELD_REQUIRED = "required"
    USER_FIELD_SELECT_OPTION = "option"
    USER_FIELD_TYPE_TEXT = "text"
    USER_FIELD_TYPE_INT = "int"
    USER_FIELD_TYPE_DROPDOWN = "dropdown"
    USER_FIELD_TYPE_RADIO = "radio"
    USER_FIELD_TYPE_EMAIL = "email"
    # Website labels
    SKIP_TO_MAIN_CONTENT = "skipToMainContent"
    WEBSITE_TITLE = "websiteTitle"
    PAGE_TITLE_LOGOUT = "pageTitleLogout"
    PAGE_TITLE_USER_REGISTRATION = "pageTitleUserRegistration"
    PAGE_TITLE_ETHICS_AGREEMENT = "pageTitleEthicsAgreement"
    PAGE_TITLE_POLICIES = "pageTitlePolicies"
    PAGE_TITLE_INTRODUCTION = "pageTitleIntroduction"
    PAGE_TITLE_ITEM_PREFERENCE = "pageTitleItemPreference"
    PAGE_TITLE_RANK = "pageTitleRank"
    PAGE_TITLE_THANK_YOU = "pageTitleThankYou"
    USER_REGISTRATION_GROUP_QUESTION_LABEL = "userRegistrationGroupQuestionLabel"
    USER_REGISTRATION_FORM_TITLE_LABEL = "userRegistrationFormTitleLabel"
    USER_REGISTRATION_SUMMIT_BUTTON_LABEL = "userRegistrationSummitButtonLabel"
    USER_REGISTRATION_GROUP_SELECTION_ERROR = "userRegistrationGroupSelectionErr"
    USER_REGISTRATION_ETHICS_AGREEMENT_LABEL = "userRegistrationEthicsAgreementLabel"
    USER_REGISTRATION_ETHICS_AGREEMENT_LINK_TEXT = "userRegistrationEthicsAgreementLinkText"
    ITEM_SELECTION_QUESTION_LABEL = "itemSelectionQuestionLabel"
    ITEM_SELECTION_YES_BUTTON_LABEL = "itemSelectionYesButtonLabel"
    ITEM_SELECTION_NO_BUTTON_LABEL = "itemSelectionNoButtonLabel"
    RANK_ITEM_SELECTED_INDICATOR_LABEL = "itemSelectedIndicatorLabel"
    RANK_ITEM_TIED_SELECTION_INDICATOR_LABEL = "rankItemTiedSelectionIndicatorLabel"
    RANK_ITEM_SKIPPED_SELECTION_INDICATOR_LABEL = "rankItemSkippedIndicatorLabel"
    RANK_ITEM_INSTRUCTION_LABEL = "rankItemInstructionLabel"
    RANK_ITEM_COMPARISON_EXECUTED_LABEL = "rankItemComparisonExecutedLabel"
    RANK_ITEM_SKIPPED_COMPARISON_EXECUTED_LABEL = "rankItemSkippedComparisonExecutedLabel"
    RANK_ITEM_REJUDGE_BUTTON_LABEL = "rankItemItemRejudgeButtonLabel"
    RANK_ITEM_CONFIRMED_BUTTON_LABEL = "rankItemConfirmedButtonLabel"
    RANK_ITEM_SKIPPED_BUTTON_LABEL = "rankItemSkippedButtonLabel"
    CONFIRM_BUTTON_ERROR_MESSAGE_WITH_SKIP = "confirmButtonErrorMessageWithSkip"
    CONFIRM_BUTTON_ERROR_MESSAGE_WITHOUT_SKIP = "confirmButtonErrorMessageWithoutSkip"
    SKIP_BUTTON_ERROR_MESSAGE = "skipButtonErrorMessage"
    ADDITIONAL_RADIO_BUTTON_INSTRUCTIONS = "additionalRadioButtonInstructions"
    ADDITIONAL_CHECKBOX_INSTRUCTIONS = "additionalCheckboxInstructions"
    ITEM_SELECTION_GROUP_LABEL = "itemSelectionGroupLabel"
    INTRODUCTION_CONTINUE_BUTTON_LABEL = "introductionContinueButtonLabel"
    THANK_YOU_CONTINUE_BUTTON_LABEL = "thankYouContinueButtonLabel"
    THANK_YOU_TITLE = "thankYouTitle"
    THANK_YOU_OPENING_TEXT = "thankYouOpeningText"
    THANK_YOU_CONTINUE_TEXT = "thankYouContinueText"
    THANK_YOU_STOP_TEXT = "thankYouStopText"
    ETHICS_AGREEMENT_BACK_BUTTON_LABEL = "ethicsAgreementBackButtonLabel"
    SITE_POLICIES_BACK_BUTTON_LABEL = "sitePoliciesBackButtonLabel"
    SITE_COOKIES_ACCEPT_BUTTON_LABEL = "siteCookiesAcceptButtonLabel"
    SITE_COOKIES_TITLE = "siteCookiesTitle"
    SITE_COOKIES_TEXT = "siteCookiesText"
    ERROR_500_TITLE = "error500Title"
    ERROR_500_MESSAGE = "error500Message"
    ERROR_404_TITLE = "error404Title"
    ERROR_404_MESSAGE = "error404Message"
    ERROR_404_HOME_LINK = "error404HomeLink"
    ERROR_204_TITLE = "error204Title"
    ERROR_204_MESSAGE = "error204Message"
    ADDITIONAL_REGISTRATION_TEXT = "additionalRegistrationPageText"

    @classmethod
    def set_configuration_location(cls, app, loc):
        """Set the location of the website configuration file.

        Args:
            app (Flask app): Website main application
            loc (string): Path for the configuration file
        """
        app.config[cls.CONFIGURATION_LOCATION] = loc
        cls.configuration = None  # make sure we clear the settings from the previous location

    @classmethod
    def get_configuration_location(cls, app):
        """Get the location of the website configuration file.

        Args:
            app (Flask app): Flask application

        Returns:
            string: Path to the configuration file
        """
        if cls.CONFIGURATION_LOCATION not in app.config:
            app.logger.critical("Configuration location not set in the application yet")
            exit()

        location = app.config[cls.CONFIGURATION_LOCATION]
        location = os.path.abspath(os.path.dirname(__file__)) + "/../" + location
        return location

    @classmethod
    def configuration_has_key(cls, label, app):
        """Check if the requested label is in either the website text or behaviour sections of the configuration file.

        Args:
            label (string): Label text required
            app (Flask app): Flask application

        Returns:
            boolean: True if the label exists, False it if does not
        """
        conf = cls.get_configuration(app)
        if label in conf[cls.CONFIGURATION_WEBSITE_TEXT]:
            return True
        if label in conf[cls.CONFIGURATION_BEHAVIOUR]:
            return True
        return False

    @classmethod
    def get_configuration(cls, app, force_reload=False):
        """Get the website configuration.

        Args:
            app (Flask app): Flask application

        Returns:
            json: website configuration object
        """
        if cls.CONFIGURATION_LOCATION not in app.config:
            app.logger.critical("Configuration location not set in the application yet")
            exit()

        if cls.configuration is None or force_reload:
            app.logger.info("Loading website configuration")
            cls.configuration = cls._unmarshall(app)

        return cls.configuration

    @classmethod
    def get_text(cls, label, app):
        """Get the text to render for a specific label of the website.

        Args:
            label (string): Label text required
            app (Flask app): Flask application

        Returns:
            string: Text configuration for the specified label
        """
        conf = cls.get_configuration(app)

        # first try the project configuration
        if label in conf[cls.CONFIGURATION_WEBSITE_TEXT]:
            return conf[cls.CONFIGURATION_WEBSITE_TEXT][label]
        # now try the language configuration
        if label in app.language_config[cls.CONFIGURATION_WEBSITE_TEXT]:
            return app.language_config[cls.CONFIGURATION_WEBSITE_TEXT][label]
        # raise an error
        app.logger.critical(f"Label {label} wasn't found in the project configuration or the language configuration.")
        exit()

    @classmethod
    def get_optional_text(cls, label, app):
        """Get the text to render for a specific label of the website or None if not supplied.

        Args:
            label (string): Label text required
            app (Flask app): Flask application

        Returns:
            string: Text configuration for the specified label or None is not supplied in config
        """
        conf = cls.get_configuration(app)
        if label not in conf[cls.CONFIGURATION_WEBSITE_TEXT]:
            return None

        return conf[cls.CONFIGURATION_WEBSITE_TEXT][label]

    @classmethod
    def get_comparison_conf(cls, key, app):
        """Get the configuration values related to the comparison behaviour of the website.

        This could come from the config file or from the csv file.

        Args:
            key (string): configuration key required
            app (Flask app): Flask application

        Returns:
            string: Configuration value for the requested key
        """
        conf = cls.get_configuration(app)
        if "csvFile" in conf[cls.CONFIGURATION_COMPARISON]:
            # then we need to get the data from the csv file
            location = cls.get_configuration_location(app)
            filepath = os.path.join(location, conf[cls.CONFIGURATION_COMPARISON]["csvFile"])
            data = CsvProcessor().create_config_from_csv(filepath)
            return data[key]
        else:
            conf = cls.get_configuration(app)
            if key not in conf[cls.CONFIGURATION_COMPARISON]:
                app.logger.critical("Label %s wasn't found in the comparison configuration." % (key))
                exit()
        return conf[cls.CONFIGURATION_COMPARISON][key]

    @classmethod
    def get_user_conf(cls, app):
        """Get the configuration values related to the user profile.

        Args:
            key (string): configuration key required
            app (Flask app): Flask application

        Returns:
            string: Configuration value for the requested key
        """
        conf = cls.get_configuration(app)
        if cls.CONFIGURATION_USER_FIELDS not in conf:
            app.logger.critical("User configuration section not found.")
            exit()

        return conf[cls.CONFIGURATION_USER_FIELDS]

    @classmethod
    def get_behaviour_conf(cls, key, app):
        """Get the configuration values related to the behaviour of the website.

        Args:
            key (string): configuration key required
            app (Flask app): Flask application

        Returns:
            string: Configuration value related to the key
        """
        conf = cls.get_configuration(app)
        if key not in conf[cls.CONFIGURATION_BEHAVIOUR]:
            app.logger.critical(f"Label {key} wasn't found in the behaviour configuration.")
            exit()

        return conf[cls.CONFIGURATION_BEHAVIOUR][key]

    @classmethod
    def get_export_location(cls, app):
        """Get the location where the exported data file should be written.

        Args:
            app (Flask app)

        Returns:
            string: export path
        """
        path = cls.get_behaviour_conf(cls.BEHAVIOUR_EXPORT_PATH_LOCATION, app)
        return os.path.abspath(os.path.dirname(__file__)) + "/../" + path

    @classmethod
    def should_render(cls, section, app):
        """Determine if a particular section should be rendered.

        Args:
            section (string): configuration key required
            app (Flask app): Flask application

        Returns:
            boolean: True when the section should be rendered, False if not.
        """
        render = cls.get_behaviour_conf(section, app)
        return render == "true" or render == "True" or render == "1" or render is True

    @classmethod
    def _unmarshall(cls, app):
        """Load the configuration file into a JSON object.

        Args:
            app (Flask app): Flask application

        Returns:
            JSON: Website configuration object
        """
        location = cls.get_configuration_location(app)
        if os.path.isdir(location):
            for file in os.listdir(location):
                if file.lower()[-5:] == ".json":
                    location = os.path.join(location, file)
        config_data = None
        try:
            with open(location, 'r') as config_file:
                config_data = json.load(config_file)
        except IOError:
            app.logger.critical("Website configuration file %s not found" % (location))
            exit()
        except ValueError:
            app.logger.critical("Website configuration file %s invalid json format" % (location))
            exit()
        except Exception as e:
            app.logger.critical(e)
            exit()
        return config_data
