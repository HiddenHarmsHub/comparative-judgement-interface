"""Setup the website database."""

import os

from sqlalchemy import text

from ..configuration.website import Settings as WS
from .connection import db, persist
from .models import CustomItemPair, Group, Item, ItemGroup, WebsiteControl


class Setup:
    """Set up functions to create the application from the configuration."""

    def __init__(self, app) -> None:
        """Initialise the Setup with the Flask app."""
        self.app = app

    def exec(self):
        """Initialise the website database.

        Args:
            app (Flask): Flask application.
        """
        with self.app.app_context():
            db.drop_all()
            db.create_all()

            # Remove previous exported database content
            export_location = WS.get_export_location(self.app)
            if os.path.exists(export_location):
                for file in os.listdir(export_location):
                    try:
                        os.remove(os.path.join(export_location, file))
                    except IsADirectoryError:
                        pass

            # The session needs be committed after the creation of the groups.
            self._setup_group(db)
            self._setup_website_control_history(db)
            db.session.commit()

            # The setup of the user configuration doesn't use SQLAlchemy ORM. The transaction
            # needs to be committed before inserting the user fields values. The user
            # columns values are dynamically defined so a different process needs to be followed.
            self._setup_user(db)

    def _setup_group(self, db):
        """Save the group configuration in the database.

        Args:
            db (SQLAlchemy): Database connection
        """
        for g in WS.get_comparison_conf(WS.GROUPS, self.app):
            group = Group(name=g[WS.GROUP_NAME], display_name=g[WS.GROUP_DISPLAY_NAME])
            group = persist(db, group)
            # Setup the items and their weights
            items = self._setup_item(db, group, g)
            self._setup_custom_item_pair(db, items, group, g)

    def _setup_custom_item_pair(self, db, items, group, g):
        """Save the custom item's weight configuration when defined manually using the Website configuration file.

        If the web configuration type was "equal", this section will be ignored.

        Args:
            db (SQLAlchemy): Database connection
            items (array(Item)): Group items store in the database.
            group (Group): Group store in the database.
            g (json): Group configuration being saved.
        """
        weight_conf = WS.get_comparison_conf(WS.GROUP_WEIGHT_CONFIGURATION, self.app)
        # Ignore this section when defining equally weighted items
        if weight_conf == WebsiteControl.EQUAL_WEIGHT:
            return

        # Save the custom weights configuration
        if weight_conf == WebsiteControl.CUSTOM_WEIGHT:
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

            # Insert the item in the database if it doesn't exists
            if item is None:
                if WS.ITEM_ID in i:
                    item = Item(
                        item_id=i[WS.ITEM_ID],
                        name=i[WS.ITEM_NAME],
                        display_name=i[WS.ITEM_DISPLAY_NAME],
                        image_path=i[WS.ITEM_IMAGE_NAME],
                    )
                else:
                    # this uses the implicit auto increment
                    item = Item(
                        name=i[WS.ITEM_NAME], display_name=i[WS.ITEM_DISPLAY_NAME], image_path=i[WS.ITEM_IMAGE_NAME]
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

    def _setup_user(self, db):
        """Save the user configuration in the database.

        User fields are dynamically configured using the website configuration file.

        Args:
            db (SQLAlchemy): Database connection
        """
        user_conf = WS.get_user_conf(self.app)
        # Create each of the new user columns
        for f in user_conf:
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
                basecommand = f'alter table user add column {name} {col_type} {nullable} DEFAULT "{default_value}"'
            else:
                basecommand = f'alter table user add column {name} {col_type} {nullable}'
            db.session.execute(text(basecommand))

        # Add a field to specify if the user accepted the ethics agreement
        # if this section was configured to be rendered
        render_ethics = WS.should_render(WS.BEHAVIOUR_RENDER_ETHICS_AGREEMENT_PAGE, self.app)
        if render_ethics:
            db.session.execute(text('alter table user add column accepted_ethics_agreement INT NOT NULL DEFAULT "0"'))

    def _setup_website_control_history(self, db):
        """Setup the control history to monitor for changes to the website configuration file.

        Once the project has been setup no changes are allowed to the website configuraiton file.
        if the file is changed the web interface will no longer respond to requests. A reset will be necessary and all
        information in the current database will be deleted as part of that process.

        Args:
            db (SQLAlchemy): Database connection,
        """
        hist = WebsiteControl()
        hist.weight_configuration = WS.get_comparison_conf(WS.GROUP_WEIGHT_CONFIGURATION, self.app)
        hist.configuration_file = self.app.config[WS.CONFIGURATION_LOCATION]
        db.session.add(hist)
