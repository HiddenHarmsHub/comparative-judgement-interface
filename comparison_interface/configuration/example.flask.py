import os
from json import loads

from dotenv import load_dotenv

load_dotenv()


class Settings(object):
    """Flask configuration."""

    def get_bool_value(key, default):
        """Get an environment value as a boolean."""
        try:
            value = os.getenv(key)
        except KeyError:
            return default
        if value in ['1', 'true', 'True', 'TRUE']:
            return True
        return False

    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///admin_database.db'
    SQLALCHEMY_BINDS = {
        'study_db': 'sqlite:///database.db',
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_MINUTES_VALIDITY = 240  # Session expires after 4 hours of inactivity
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'strict'
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024
    LANGUAGE = os.getenv('LANGUAGE', 'en')
    API_ACCESS = os.getenv('API_ACCESS', False)
    API_KEY_FILE = os.getenv('API_KEY_FILE')
    ADMIN_ACCESS = get_bool_value('ADMIN_ACCESS', False)
    IMAGE_UPLOAD_DIR = 'static/images/'
    HTML_PAGES_DIR = 'pages_html'
    CONFIG_UPLOAD_DIR = 'project_configuration'
    MAIL_BACKEND = os.getenv('MAIL_BACKEND', 'console')
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = os.getenv('MAIL_PORT')
    SECURITY_PASSWORD_SALT = os.getenv('SECURITY_PASSWORD_SALT')
    SECURITY_URL_PREFIX = '/admin'
    SECURITY_LOGIN_USER_TEMPLATE = 'user_login.html'
    SECURITY_TWO_FACTOR = get_bool_value('SECURITY_TWO_FACTOR', False)
    SECURITY_TWO_FACTOR_REQUIRED = get_bool_value('SECURITY_TWO_FACTOR_REQUIRED', False)
    SECURITY_TWO_FACTOR_ENABLED_METHODS = ['email']
    SECURITY_TWO_FACTOR_VERIFY_CODE_TEMPLATE = '2fa_verify.html'
    SECURITY_TWO_FACTOR_SETUP_TEMPLATE = '2fa_setup.html'
    SECURITY_TOTP_SECRETS = loads(os.getenv('SECURITY_TOTP_SECRETS', '{}'))
    SECURITY_TOTP_ISSUER = 'flask admin'
    SECURITY_POST_LOGIN_VIEW = '/admin/dashboard'
    SECURITY_POST_LOGOUT_VIEW = '/admin/logged-out'
