from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, auth_required, hash_password
from flask_security.models import fsqla_v3 as fsqla

from comparison_interface.db.connection import db


# Define models
fsqla.FsModels.set_db_info(db)

class Role(db.Model, fsqla.FsRoleMixin):
    #__bind_key__ = 'admin_db'
    pass

class User(db.Model, fsqla.FsUserMixin):
    #__bind_key__ = 'admin_db'
    pass

class WebAuthn(db.Model, fsqla.FsWebAuthnMixin):
    #__bind_key__ = 'admin_db'
    pass
