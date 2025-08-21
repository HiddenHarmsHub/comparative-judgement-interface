from dotenv import load_dotenv
from os import environ

load_dotenv()

class Settings(object):
    """Flask configuration."""

    SQLALCHEMY_DATABASE_URI = 'sqlite:///admin_database.db'
    SQLALCHEMY_BINDS = {
        'study_db': 'sqlite:///database.db',
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_MINUTES_VALIDITY = 240  # Session expires after 4 hours of inactivity
    IMAGE_UPLOAD_DIR = 'static/images/'
    HTML_PAGES_DIR = 'pages_html'
    CONFIG_UPLOAD_DIR = 'project_configuration'
    SECURITY_URL_PREFIX = '/admin'
    SECURITY_LOGIN_USER_TEMPLATE = 'user_login.html'
    SECURITY_TWO_FACTOR_ENABLED_METHODS = ['email']
    SECURITY_TWO_FACTOR_VERIFY_CODE_TEMPLATE = '2fa_verify.html'
    SECURITY_TWO_FACTOR_SETUP_TEMPLATE = '2fa_setup.html'
    SECURITY_POST_LOGIN_VIEW = '/admin/dashboard'
    SECURITY_POST_LOGOUT_VIEW = '/admin/logged-out'

    SECURITY_TWO_FACTOR = True
    SECURITY_TWO_FACTOR_REQUIRED = True
    SECURITY_TOTP_SECRETS = {"1": "retfdgdgfdsfk"}
    MAIL_BACKEND = 'console'
    SECURITY_TOTP_ISSUER = 'flask admin'
    # MAIL_SERVER = 'our path'
    # MAIL_PORT = 25
    SECURITY_PASSWORD_SALT = 'ttr5redsijokj'
    LANGUAGE = 'en'
    API_ACCESS = False
    API_KEY_FILE = '.apikey'
    SECRET_KEY = 'srd6sj5sjfMS12HD'  # Change to your own secret key

