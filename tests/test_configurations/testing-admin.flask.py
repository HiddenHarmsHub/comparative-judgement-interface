class Settings(object):
    """Base Flask configuration for the accessibility admin tests.

    These need a special config file that has admin access set to true because without it the commands needed to setup
    the admin database and add a user before the app is run are not available.
    """

    TESTING = True
    SECRET_KEY = 'ydf7ash*sdFdy'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_admin_database.db'
    SQLALCHEMY_BINDS = {
        'study_db': 'sqlite:///test_database.db',
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_MINUTES_VALIDITY = 30
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = False
    SESSION_COOKIE_SAMESITE = 'strict'
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024
    LANGUAGE = 'en'
    API_ACCESS = False
    ADMIN_ACCESS = True
    IMAGE_UPLOAD_DIR = 'static/images/'
    HTML_PAGES_DIR = 'pages_html'
    CONFIG_UPLOAD_DIR = 'project_configuration'
    WTF_CSRF_ENABLED = False
    SECURITY_PASSWORD_SALT = 'hdys^d54$djf8fkas*'
    SECURITY_PASSWORD_HASH = 'plaintext'
    SECURITY_URL_PREFIX = '/admin'
    SECURITY_LOGIN_USER_TEMPLATE = 'user_login.html'
    SECURITY_TWO_FACTOR = False
    SECURITY_TWO_FACTOR_REQUIRED = False
    SECURITY_POST_LOGIN_VIEW = '/admin/dashboard'
    SECURITY_POST_LOGOUT_VIEW = '/admin/logged-out'
