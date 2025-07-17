from flask_wtf import FlaskForm
from flask_wtf.file import FileField, MultipleFileField


class ImageUploadForm(FlaskForm):
    """Form for image upload."""
    image_files = MultipleFileField('Image files')
    # 


class ConfigUploadForm(FlaskForm):
    """Form for configuration file upload."""
    config_file = FileField('Configuration file', validators=[])
