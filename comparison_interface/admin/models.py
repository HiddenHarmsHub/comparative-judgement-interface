from flask_security.models import fsqla_v3 as fsqla

from comparison_interface.db.connection import db

# Define models
fsqla.FsModels.set_db_info(db)


class Role(db.Model, fsqla.FsRoleMixin):
    pass


class User(db.Model, fsqla.FsUserMixin):
    pass


class WebAuthn(db.Model, fsqla.FsWebAuthnMixin):
    pass
