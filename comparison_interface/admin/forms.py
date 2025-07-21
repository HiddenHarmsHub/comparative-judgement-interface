from flask_wtf import FlaskForm
from flask_wtf.file import FileField, MultipleFileField
from wtforms import BooleanField, HiddenField, TextAreaField, validators


class ImageUploadForm(FlaskForm):
    """Form for image upload."""
    image_files = MultipleFileField('Image files')


class ConfigUploadForm(FlaskForm):
    """Form for configuration file upload."""
    config_file = FileField('Configuration file', validators=[])


class CreateStudyForm(FlaskForm):
    """Form to setup study."""
    deletion_confirmation = BooleanField(
        '''I understand that creating a study will delete the database associated with the current study and I already
        have a copy of any data I require.''',
        validators=[validators.DataRequired()]
    )

class EditHtmlPageForm(FlaskForm):
    """Form for editing the Html pages."""
    page_type = HiddenField()
    current_text = HiddenField()
    md_text = TextAreaField('', validators=[validators.DataRequired()])
