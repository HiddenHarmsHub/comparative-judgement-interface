from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import BooleanField, HiddenField, TextAreaField, validators


class ImageUploadForm(FlaskForm):
    """Form for image upload."""


class ConfigUploadForm(FlaskForm):
    """Form for configuration file upload."""

    config_file = FileField(
        "Configuration file", validators=[FileRequired(), FileAllowed(["json"], "config must be a JSON file")]
    )


class CsvUploadForm(FlaskForm):
    """Form for configuration file upload."""

    csv_file = FileField("CSV file", validators=[FileRequired(), FileAllowed(["csv"], "config must be a CSV file")])


class StartStudyForm(FlaskForm):
    """Form to setup study."""

    deletion_confirmation = BooleanField(
        """I understand that creating a study will stop the current study and delete the data and I already have a
        copy of any data I require.""",
        validators=[validators.DataRequired()],
    )


class CreateStudyForm(FlaskForm):
    """Form to create the study after images and config uploaded."""

    uploads_complete = HiddenField()


class EditHtmlPageForm(FlaskForm):
    """Form for editing the Html pages."""

    page_type = HiddenField()
    current_text = HiddenField()
    md_text = TextAreaField("", validators=[validators.DataRequired()])
