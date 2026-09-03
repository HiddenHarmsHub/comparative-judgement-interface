from datetime import datetime

from sqlalchemy import JSON
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
    __bind_key__ = "study_db"

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
    __bind_key__ = "study_db"

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
    __bind_key__ = "study_db"

    item_group_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.item_id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.group_id'), nullable=False)
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.now)

    __table_args__ = (UniqueConstraint('item_id', 'group_id', name='_item_group_uidx'),)


class Participant(db.Model, BaseModel):
    """Represents the user making the comparison.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'participant'
    __bind_key__ = "study_db"

    participant_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    current_study = db.Column(db.Integer, db.ForeignKey('study_control.study_id'), nullable=True)
    # Other user files are added automatically by using the Website configuration file
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.now)
    # TODO: temporary, we will be moving this to the participant study table when we do multiple studies
    completed_cycles = db.Column(db.Integer, server_default='0')


class ParticipantStudy(db.Model, BaseModel):
    """Tracks how far through the studies each user is.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'participant_study'
    __bind_key__ = "study_db"

    study_tracking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    study_id = db.Column(db.Integer, db.ForeignKey('study_control.study_id'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.participant_id'), nullable=False)
    completed_cycles = db.Column(db.Integer, server_default='0')


class ParticipantGroup(db.Model, BaseModel):
    """Holds the group preferences of the user.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'participant_group'
    __bind_key__ = "study_db"

    participant_group_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.group_id'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.participant_id'), nullable=False)
    created_date = db.Column(db.DateTime(timezone=True), default=datetime.now)

    __table_args__ = (UniqueConstraint('group_id', 'participant_id', name='_participant_group_uidx'),)


class Comparison(db.Model, BaseModel):
    """The actual comparison made between the items by the user.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'comparison'
    __bind_key__ = "study_db"

    # Available comparison states
    SELECTED = 'selected'
    SKIPPED = 'skipped'
    TIED = 'tied'

    comparison_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.participant_id'), nullable=False)
    item_1_id = db.Column(db.Integer, db.ForeignKey('item.item_id'), nullable=False)
    item_2_id = db.Column(db.Integer, db.ForeignKey('item.item_id'), nullable=False)
    selected_item_id = db.Column(db.Integer, db.ForeignKey('item.item_id'), nullable=True)
    state = db.Column(db.String(20), nullable=False)
    created = db.Column(db.DateTime(timezone=True), default=datetime.now)
    updated = db.Column(db.DateTime(timezone=True), default=datetime.now)


class CustomItemPair(db.Model, BaseModel):
    """Holds a pair of items with custom weight configurations.

    This table is only populated when the items group weight configuration is set to custom.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'custom_item_pair'
    __bind_key__ = "study_db"

    custom_item_pair_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.group_id'), nullable=False)
    item_1_id = db.Column(db.Integer, db.ForeignKey('item.item_id'), nullable=False)
    item_2_id = db.Column(db.Integer, db.ForeignKey('item.item_id'), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    created = db.Column(db.DateTime(timezone=True), default=datetime.now)

    __table_args__ = (UniqueConstraint('group_id', 'item_1_id', 'item_2_id', name='_custom_item_pair_uidx'),)


class TotalItemPair(db.Model, BaseModel):
    """Holds pairs of items duplicated based on the weight configuration and the total judgements required overall.

    This table is only populated when the items group weight configuration is set to weighted-total.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'item_pair_totals'
    __bind_key__ = "study_db"

    custom_item_pair_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.group_id'), nullable=False)
    item_1_id = db.Column(db.Integer, db.ForeignKey('item.item_id'), nullable=False)
    item_2_id = db.Column(db.Integer, db.ForeignKey('item.item_id'), nullable=False)
    judged = db.Column(db.Boolean, nullable=False)
    created = db.Column(db.DateTime(timezone=True), default=datetime.now)


class ParticipantItem(db.Model, BaseModel):
    """Items that are recognizable by the user. The comparison will be made using only the items selected.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'participant_item'
    __bind_key__ = "study_db"

    participant_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.participant_id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.item_id'), nullable=False)
    known = db.Column(db.Boolean, nullable=False)  # 0 for unknown. 1 for know.
    date = db.Column(db.DateTime(timezone=True), default=datetime.now)

    __table_args__ = (UniqueConstraint('participant_id', 'item_id', name='_participant_item_uidx'),)


class RegistrationQuestions(db.Model, BaseModel):
    """Table to store details of participant registration questions. This can only be changed on rebuild.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'registration_questions'
    __bind_key__ = "study_db"

    question_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question_name = db.Column(db.String(100), nullable=False)
    question_display = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    min_limit = db.Column(db.Integer, nullable=True)
    max_limit = db.Column(db.Integer, nullable=True)
    option = db.Column(JSON)
    required = db.Column(db.Boolean, nullable=False)


class WebsiteControl(db.Model, BaseModel):
    """Control table to store settings which can only be set for the whole website.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'website_control'
    __bind_key__ = "study_db"

    website_control_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    study_count = db.Column(db.Integer, nullable=False)
    export_path_location = db.Column(db.String(250), nullable=False)
    render_user_instruction_page = db.Column(db.Boolean, nullable=False)
    user_instruction_html = db.Column(db.String(250), nullable=True)
    render_ethics_agreement_page = db.Column(db.Boolean, nullable=False)
    ethics_agreement_html = db.Column(db.String(250), nullable=True)
    render_site_policies_page = db.Column(db.Boolean, nullable=False)
    site_policies_html = db.Column(db.String(250), nullable=True)
    render_cookie_banner = db.Column(db.Boolean, nullable=False)

    # these two will need to be removed
    configuration_file = db.Column(db.String(500), nullable=False)
    setup_exec_date = db.Column(db.DateTime(timezone=True), default=datetime.now)

    def get_conf(self):
        """Get the website control configuration.

        Returns:
            WebsiteControl: Website Control configuration model object
        """
        return self.query.order_by(WebsiteControl.website_control_id.desc()).first()


class StudyControl(db.Model, BaseModel):
    """Table to control the studies running on the website.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'study_control'
    __bind_key__ = "study_db"

    # Available weight configuration
    EQUAL_WEIGHT = 'equal'  # All items weights during the comparison are the same.
    CUSTOM_WEIGHT = 'manual'  # The weights of the items were manually assigned by the researcher.
    WEIGHTED_TOTAL = 'weighted-total'  # The weights of the items are calculated by weight and total target judgements.

    study_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    study_sequence = db.Column(db.Integer, nullable=False)
    weight_configuration = db.Column(db.String(20), nullable=False)
    allow_ties = db.Column(db.Boolean, nullable=False)
    allow_skip = db.Column(db.Boolean, nullable=False)
    allow_back = db.Column(db.Boolean, nullable=False)
    render_user_item_preference_page = db.Column(db.Boolean, nullable=False)
    offer_escape_route_between_cycles = db.Column(db.Boolean, nullable=False)
    cycle_length = db.Column(db.Integer, nullable=False)
    maximum_cycles_per_user = db.Column(db.Integer, nullable=False)

    def get_conf(self):
        """Get the study control configuration.

        NB: this will need to get the right study once we allow multiple studies

        Returns:
            StudyControl: Study Control configuration model object
        """
        return self.query.order_by(StudyControl.study_sequence.desc()).first()


class WebsiteText(db.Model, BaseModel):
    """Table to for all the text strings used on the website.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'website_text'
    __bind_key__ = "study_db"

    website_text_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    language = db.Column(db.String(3), nullable=False)
    string_key = db.Column(db.String(500), nullable=False)
    string_value = db.Column(db.String(500), nullable=False)


class StudyText(db.Model, BaseModel):
    """Table to for all the text strings used on the website.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """

    __tablename__ = 'study_text'
    __bind_key__ = "study_db"

    study_text_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    study_id = db.Column(db.Integer, db.ForeignKey('study_control.study_id'), nullable=False)
    language = db.Column(db.String(3), nullable=False)
    string_key = db.Column(db.String(500), nullable=False)
    string_value = db.Column(db.String(500), nullable=False)
