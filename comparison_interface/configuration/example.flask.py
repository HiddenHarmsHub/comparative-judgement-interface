class Settings(object):
    """Flask configuration."""

    SECRET_KEY = 'srd6sj5sjfMS12HD'  # Change to your own secret key
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_MINUTES_VALIDITY = 240  # Session expires after 4 hours of inactivity
    API_ACCESS = False
    API_KEY_FILE = '.apikey'
    LANGUAGE = 'en'
