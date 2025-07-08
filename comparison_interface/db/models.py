from datetime import datetime

from sqlalchemy.schema import UniqueConstraint

from .connection import db


class BaseModel:
    """Base class for schema models."""

    def as_dict(self):
        """Turn the schema object into a dictionary.

        Returns:
            dict: The object serialised to a dictionary
        """
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}

    def __repr__(self):
        """Return the representation of an object as a dictionary."""
        return self.as_dict()


class Group(db.Model, BaseModel):
    """Entity clustering for the items being compared.

    This table allows specify this item's clustering. Some items cluster naturally.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'group'

    group_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255), nullable=False)
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.now)

    __table_args__ = (UniqueConstraint('name', name='_group_name_uidx'),)


class Item(db.Model, BaseModel):
    """The item model represent each of the object being compared.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'item'

    item_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(1000), nullable=False)
    image_description = db.Column(db.String(1000), nullable=True)
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.now)

    __table_args__ = (
        UniqueConstraint('name', 'display_name', 'image_path', name='_item_name_display_name_image_path_uidx'),
    )


class ItemGroup(db.Model, BaseModel):
    """The item model represent each of the object being compared.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'item_group'

    item_group_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.item_id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.group_id'), nullable=False)
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.now)

    __table_args__ = (UniqueConstraint('item_id', 'group_id', name='_item_group_uidx'),)


class User(db.Model, BaseModel):
    """Represents the user making the comparison.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Other user files are added automatically by using the Website configuration file
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.now)
    completed_cycles = db.Column(db.Integer, server_default='0')


class UserGroup(db.Model, BaseModel):
    """Holds the group preferences of the user.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'user_group'

    user_group_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.group_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.now)

    __table_args__ = (UniqueConstraint('group_id', 'user_id', name='_user_group_uidx'),)


class Comparison(db.Model, BaseModel):
    """The actual comparison made between the items by the user.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'comparison'
    # Available comparison states
    SELECTED = 'selected'
    SKIPPED = 'skipped'
    TIED = 'tied'

    comparison_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    item_1_id = db.Column(db.Integer, db.ForeignKey('item.item_id'), nullable=False)
    item_2_id = db.Column(db.Integer, db.ForeignKey('item.item_id'), nullable=False)
    selected_item_id = db.Column(db.Integer, db.ForeignKey('item.item_id'), nullable=True)
    state = db.Column(db.String(20), nullable=False)
    created = db.Column(db.DateTime(timezone=True), default=datetime.now)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.now)


class CustomItemPair(db.Model, BaseModel):
    """Holds a pair of items with custom weight configurations.

    If this table is empty, a random item selection will be made using the user's group preferences.
    This table is only populated when the items group weight configuration is set to custom.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'custom_item_pair'
    custom_item_pair_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.group_id'), nullable=False)
    item_1_id = db.Column(db.Integer, db.ForeignKey('item.item_id'), nullable=False)
    item_2_id = db.Column(db.Integer, db.ForeignKey('item.item_id'), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    created = db.Column(db.DateTime(timezone=True), default=datetime.now)

    __table_args__ = (UniqueConstraint('group_id', 'item_1_id', 'item_2_id', name='_custom_item_pair_uidx'),)


class UserItem(db.Model, BaseModel):
    """Items that are recognizable by the user. The comparison will be made using only the items selected.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'user_item'

    user_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.item_id'), nullable=False)
    known = db.Column(db.Boolean, nullable=False)  # 0 for unknow. 1 for know.
    date = db.Column(db.DateTime(timezone=True), default=datetime.now)

    __table_args__ = (UniqueConstraint('user_id', 'item_id', name='_user_item_uidx'),)


class WebsiteControl(db.Model, BaseModel):
    """Control table to know if the application is in a healthy state.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'website_control'

    # Available weight configuration
    EQUAL_WEIGHT = 'equal'  # All items weights during the comparison are the same.
    CUSTOM_WEIGHT = 'manual'  # The weights of the items were manually assigned by the researcher.

    website_control_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    weight_configuration = db.Column(db.String(20), nullable=False)
    configuration_file = db.Column(db.String(500), nullable=False)
    setup_exec_date = db.Column(db.DateTime(timezone=True), default=datetime.now)

    def get_conf(self):
        """Get the website control configuration.

        Returns:
            WebsiteControl: Website Control configuration model object
        """
        return self.query.order_by(WebsiteControl.website_control_id.desc()).first()

    def equal_weight_configuration(self):
        """Determine if the system is running with an equal weight configuration.

        Returns:
            boolean: True if the configuration is for equal weighted items, False if not
        """
        c = self.get_conf()
        return c.weight_configuration == self.EQUAL_WEIGHT
