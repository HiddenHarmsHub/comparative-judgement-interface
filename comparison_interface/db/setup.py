"""Setup the website database."""

import os
from math import ceil

from sqlalchemy import create_engine, text

from comparison_interface.configuration.csv_processor import CsvProcessor
from comparison_interface.configuration.schema import WebsiteTextConfiguration
from comparison_interface.configuration.website import Settings as WS

from .connection import db, persist
from .models import (
    CustomItemPair,
    Group,
    Item,
    ItemGroup,
    RegistrationQuestions,
    StudyControl,
    TotalItemPair,
    WebsiteControl,
    WebsiteText,
)


class Setup:
    """Set up functions to create the application from the configuration."""

    def __init__(self, app) -> None:
        """Initialise the Setup with the Flask app."""
        self.app = app
        self.json_conf = WS.get_configuration(self.app)

    def exec(self):
        """Initialise the website database.

        Args:
            app (Flask): Flask application.
        """
        with self.app.app_context():
            db.drop_all('study_db')
            db.create_all('study_db')

            # Remove previous exported database content
            export_location = self._get_config_value(WS.BEHAVIOUR_EXPORT_PATH_LOCATION)
            if os.path.exists(export_location):
                for file in os.listdir(export_location):
                    try:
                        os.remove(os.path.join(export_location, file))
                    except IsADirectoryError:
                        pass

            # The session needs be committed after the creation of the groups.
            self._setup_group(db)
            self._setup_website_control(db)
            self._setup_registration_questions(db)
            self._setup_study_control(db)
            self._setup_website_text(db)
            db.session.commit()

            # The setup of the participant configuration doesn't use SQLAlchemy ORM. The transaction
            # needs to be committed before inserting the participant fields values. The participant
            # columns values are dynamically defined so a different process needs to be followed.
            self._setup_participant(db)

    def _get_comparison_conf(self, key):
        """Get the configuration values related to the comparison behaviour of the website.

        This could come from the config file or from the csv file.

        Args:
            key (string): configuration key required
            app (Flask app): Flask application

        Returns:
            string: Configuration value for the requested key
        """
        if "csvFile" in self.json_conf[WS.CONFIGURATION_COMPARISON]:
            # then we need to get the data from the csv file
            location = WS.get_configuration_location(self.app)
            filepath = os.path.join(location, self.json_conf[WS.CONFIGURATION_COMPARISON]["csvFile"])
            data = CsvProcessor().create_config_from_csv(filepath)
            return data[key]
        else:
            if key not in self.json_conf[WS.CONFIGURATION_COMPARISON]:
                self.app.logger.critical("Label %s wasn't found in the comparison configuration." % (key))
                exit()
        return self.json_conf[WS.CONFIGURATION_COMPARISON][key]

    def _setup_group(self, db):
        """Save the group configuration in the database.

        Args:
            db (SQLAlchemy): Database connection
        """
        for g in self._get_comparison_conf(WS.GROUPS):
            group = Group(name=g[WS.GROUP_NAME], display_name=g[WS.GROUP_DISPLAY_NAME])
            group = persist(db, group)
            # Setup the items and their weights
            items = self._setup_item(db, group, g)
            weight_conf = self._get_comparison_conf(WS.GROUP_WEIGHT_CONFIGURATION)
            if weight_conf == StudyControl.CUSTOM_WEIGHT:
                self._setup_custom_item_pair(db, items, group, g)
            if weight_conf == StudyControl.WEIGHTED_TOTAL:
                total_judgements_required = self._get_comparison_conf(WS.TARGET_COMPARISONS)
                self._setup_weighted_total_pairs(db, items, group, g, total_judgements_required)

    def _setup_custom_item_pair(self, db, items, group, g):
        """Save the custom item's weight configuration when defined manually using the Website configuration file.

        If the web configuration type was "equal", this section will be ignored.

        Args:
            db (SQLAlchemy): Database connection
            items (array(Item)): Group items store in the database.
            group (Group): Group store in the database.
            g (json): Group configuration being saved.
        """
        # Save the custom weights configuration
        weights = g[WS.GROUP_ITEMS_WEIGHT]

        items_dict = {}
        for i in items:
            items_dict[i.name] = int(i.item_id)

        for w in weights:
            c = CustomItemPair()
            c.item_1_id = items_dict[w["item_1"]]
            c.item_2_id = items_dict[w["item_2"]]
            c.group_id = group.group_id
            c.weight = w["weight"]
            db.session.add(c)

        return

    def _setup_weighted_total_pairs(self, db, items, group, g, total_judgements_required):
        """Save each pair of items the number of times that pair needs to be judged.

        The total number of each pair is based on the weight and overall total number of judgements required.

        Args:
            db (SQLAlchemy): Database connection
            items (array(Item)): Group items store in the database.
            group (Group): Group store in the database.
            g (json): Group configuration being saved.
            total_judgements_required (int): The total judgements required.
        """
        pairs = g[WS.GROUP_ITEMS_WEIGHT]
        for pair in pairs:
            weight = pair["weight"]
            pair_total = ceil(weight * total_judgements_required)

            items_dict = {}
            for i in items:
                items_dict[i.name] = int(i.item_id)

            for i in range(0, pair_total):
                c = TotalItemPair()
                c.item_1_id = items_dict[pair["item_1"]]
                c.item_2_id = items_dict[pair["item_2"]]
                c.group_id = group.group_id
                c.judged = False
                db.session.add(c)

        return

    def _setup_item(self, db, group, g):
        """Save the item configuration in the database.

        Args:
            db (SQLAlchemy): Database connection
            group (SQLAlchemy): Inserted group object.
            g (Json): Group configuration object on the global website configuration.
        """
        # Insert each of the items related to the groups
        items = []
        for i in g[WS.GROUP_ITEMS]:
            # Verify if the item already exists in the database
            query = db.select(Item).where(
                Item.name == i[WS.ITEM_NAME],
                Item.display_name == i[WS.ITEM_DISPLAY_NAME],
                Item.image_path == i[WS.ITEM_IMAGE_NAME],
            )
            item = db.session.scalars(query).first()

            # Insert the item in the database if it doesn't exist
            if item is None:
                if WS.ITEM_ID in i:
                    item = Item(
                        item_id=i[WS.ITEM_ID],
                        name=i[WS.ITEM_NAME],
                        display_name=i[WS.ITEM_DISPLAY_NAME],
                        image_description=i.get(WS.ITEM_IMAGE_DESCRIPTION, None),
                        image_path=i[WS.ITEM_IMAGE_NAME],
                    )
                else:
                    # this uses the implicit auto increment
                    item = Item(
                        name=i[WS.ITEM_NAME],
                        display_name=i[WS.ITEM_DISPLAY_NAME],
                        image_description=i.get(WS.ITEM_IMAGE_DESCRIPTION, None),
                        image_path=i[WS.ITEM_IMAGE_NAME],
                    )
                persist(db, item)
            else:
                self.app.logger.info("Reusing item {} information.".format(item.name))
            self._setup_item_group(db, item, group)

            items.append(item)
        return items

    def _setup_item_group(self, db, item, group):
        """Relate the item to the correspondent group in the database.

        Args:
            db (SQLAlchemy): Database connection.
            item (SQLAlchemy): Inserted item object.
            group (SQLAlchemy): Inserted group object.
        """
        item_id = item.item_id
        group_id = group.group_id

        # Verify if the item was already related to the group
        query = db.select(ItemGroup).where(ItemGroup.item_id == item_id, ItemGroup.group_id == group_id)
        item_group = db.session.scalars(query).first()

        # Relate the item to the group if the relationship hasn't been created yet.
        if item_group is None:
            item_group = ItemGroup(item_id=item_id, group_id=group_id)
            persist(db, item_group)
        else:
            self.app.logger.info("Reusing Item {} relationship with group {}.".format(item.name, group.name))

    def _setup_participant(self, db):
        """Save the participant configuration in the database.

        User fields are dynamically configured using the website configuration file.

        Args:
            db (SQLAlchemy): Database connection
        """
        participant_conf = self.json_conf[WS.CONFIGURATION_USER_FIELDS]
        # Create each of the new participant columns
        os.chdir(self.app.instance_path)
        engine = create_engine(self.app.config["SQLALCHEMY_BINDS"]["study_db"])
        with engine.connect() as conn:
            for f in participant_conf:
                name = f[WS.USER_FIELD_NAME]
                required = f[WS.USER_FIELD_REQUIRED]
                type = f[WS.USER_FIELD_TYPE]
                max_size = None

                if type == WS.USER_FIELD_TYPE_TEXT or type == WS.USER_FIELD_TYPE_EMAIL:
                    max_size = f[WS.USER_FIELD_MAX_LIMIT]
                    col_type = f'VARCHAR({max_size})'
                    default_value = ""
                elif type == WS.USER_FIELD_TYPE_DROPDOWN or type == WS.USER_FIELD_TYPE_RADIO:
                    max_size = max([len(x) for x in f[WS.USER_FIELD_SELECT_OPTION]])
                    col_type = f'VARCHAR({max_size})'
                    default_value = ""
                elif type == WS.USER_FIELD_TYPE_INT:
                    col_type = 'INT'
                    default_value = 0
                if required is True:
                    nullable = 'NOT NULL'
                else:
                    nullable = 'NULL'

                if required is True:
                    basecommand = (
                        f'alter table participant add column {name} {col_type} {nullable} DEFAULT "{default_value}"'
                    )
                else:
                    basecommand = f'alter table participant add column {name} {col_type} {nullable}'

                conn.execute(text(basecommand))

            # Add a field to specify if the participant accepted the ethics agreement
            # if this section was configured to be rendered
            render_ethics = self._get_config_value(WS.BEHAVIOUR_RENDER_ETHICS_AGREEMENT_PAGE)
            if render_ethics:
                conn.execute(
                    text('alter table participant add column accepted_ethics_agreement INT NOT NULL DEFAULT "0"')
                )

    def _get_config_value(self, key):
        if key not in self.json_conf[WS.CONFIGURATION_BEHAVIOUR]:
            self.app.logger.critical(f"Label {key} wasn't found in the behaviour configuration.")
            exit()
        else:
            return self.json_conf[WS.CONFIGURATION_BEHAVIOUR][key]

    def _setup_registration_questions(self, db):
        """Load the configuration for the registration questions.

        Args:
            db (SQLAlchemy): Database connection,
        """
        participant_conf = self.json_conf[WS.CONFIGURATION_USER_FIELDS]
        for question in participant_conf:
            config = RegistrationQuestions()
            config.question_name = question[WS.USER_FIELD_NAME]
            config.question_display = question[WS.USER_FIELD_DISPLAY_NAME]
            config.type = question[WS.USER_FIELD_TYPE]
            try:
                config.max_limit = question[WS.USER_FIELD_MAX_LIMIT]
            except KeyError:
                config.max_limit = None
            try:
                config.min_limit = question[WS.USER_FIELD_MIN_LIMIT]
            except KeyError:
                config.min_limit = None
            try:
                config.option = question[WS.USER_FIELD_SELECT_OPTION]
            except KeyError:
                config.option = None
            config.required = question[WS.USER_FIELD_REQUIRED]
            db.session.add(config)

    def _setup_website_control(self, db):
        """Load the configuration for the website control.

        Args:
            db (SQLAlchemy): Database connection,
        """
        config = WebsiteControl()
        config.study_count = 1

        config.export_path_location = self._get_config_value(WS.BEHAVIOUR_EXPORT_PATH_LOCATION)
        config.render_user_instruction_page = self._get_config_value(WS.BEHAVIOUR_RENDER_USER_INSTRUCTION_PAGE)
        config.render_ethics_agreement_page = self._get_config_value(WS.BEHAVIOUR_RENDER_ETHICS_AGREEMENT_PAGE)
        config.render_site_policies_page = self._get_config_value(WS.BEHAVIOUR_RENDER_SITE_POLICIES)
        config.render_cookie_banner = self._get_config_value(WS.BEHAVIOUR_RENDER_COOKIE_BANNER)
        if WS.BEHAVIOUR_USER_INSTRUCTION_HTML in self.json_conf[WS.CONFIGURATION_BEHAVIOUR]:
            config.instructions_html = self._get_config_value(WS.BEHAVIOUR_USER_INSTRUCTION_HTML)
        if WS.BEHAVIOUR_ETHICS_AGREEMENT_HTML in self.json_conf[WS.CONFIGURATION_BEHAVIOUR]:
            config.ethics_html = self._get_config_value(WS.BEHAVIOUR_ETHICS_AGREEMENT_HTML)
        if WS.BEHAVIOUR_SITE_POLICIES_HTML in self.json_conf[WS.CONFIGURATION_BEHAVIOUR]:
            config.site_policies_html = self._get_config_value(WS.BEHAVIOUR_SITE_POLICIES_HTML)

        config.configuration_file = self.app.config[WS.CONFIGURATION_LOCATION]
        db.session.add(config)

    def _setup_study_control(self, db):
        """Load the configuration for the studies.

        Args:
            db (SQLAlchemy): Database connection,
        """
        config = StudyControl()
        config.study_sequence = 1
        config.weight_configuration = self._get_comparison_conf(WS.GROUP_WEIGHT_CONFIGURATION)
        config.allow_ties = self._get_config_value(WS.BEHAVIOUR_ALLOW_TIES)
        config.allow_skip = self._get_config_value(WS.BEHAVIOUR_ALLOW_SKIP)
        config.allow_back = self._get_config_value(WS.BEHAVIOUR_ALLOW_BACK)
        config.render_user_item_preference_page = self._get_config_value(WS.BEHAVIOUR_RENDER_USER_ITEM_PREFERENCE_PAGE)
        config.offer_escape_route_between_cycles = self._get_config_value(WS.BEHAVIOUR_ESCAPE_ROUTE)
        config.cycle_length = self._get_config_value(WS.BEHAVIOUR_CYCLE_LENGTH)
        config.maximum_cycles_per_user = self._get_config_value(WS.BEHAVIOUR_MAX_CYCLES)
        db.session.add(config)

    def _setup_website_text(self, db):

        keys = vars(WebsiteTextConfiguration())['declared_fields'].keys()
        for key in keys:
            config = WebsiteText()
            config.string_key = key
            config.language = "en"
            if key in self.json_conf[WS.CONFIGURATION_WEBSITE_TEXT]:
                config.string_value = self.json_conf[WS.CONFIGURATION_WEBSITE_TEXT][key]
            elif key in self.app.language_config[WS.CONFIGURATION_WEBSITE_TEXT]:
                config.string_value = self.app.language_config[WS.CONFIGURATION_WEBSITE_TEXT][key]
            else:
                config.string_value = "missing"
            if isinstance(config.string_value, list):
                config.string_value = '||'.join(config.string_value)
            db.session.add(config)
        # now add the user study data
        participant_conf = self.json_conf[WS.CONFIGURATION_USER_FIELDS]
        for question in participant_conf:
            config = WebsiteText()
            config.string_key = f"{question[WS.USER_FIELD_NAME]}_question_text"
            config.language = "en"
            config.string_value = question[WS.USER_FIELD_DISPLAY_NAME]
            db.session.add(config)
            if "option" in question:
                config = WebsiteText()
                config.string_key = f"{question[WS.USER_FIELD_NAME]}_option_text"
                config.language = "en"
                config.string_value = "||".join(question[WS.USER_FIELD_SELECT_OPTION])
                db.session.add(config)
