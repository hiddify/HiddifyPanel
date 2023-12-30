import uuid as uuid_mod
from hiddifypanel.models.role import Role
from sqlalchemy import Column, String
from hiddifypanel.panel.database import db


class BaseAccount(db.Model):
    __abstract__ = True
    # id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), default=lambda: str(uuid_mod.uuid4()), nullable=False, unique=True)
    name = Column(String(512), nullable=False, default='')
    username = Column(String(16), nullable=True, default='')
    password = Column(String(16), nullable=True, default='')
    comment = Column(String(512), nullable=True, default='')
    telegram_id = Column(String(512), nullable=True, default='')

    def is_username_unique(self) -> bool:
        from hiddifypanel.models.user import User
        from hiddifypanel.models.admin import AdminUser

        if isinstance(self, AdminUser):
            if model := AdminUser.query.filter_by(username=self.username).first():
                if model.id != self.id:
                    return False
            return True
        else:
            if model := User.query.filter_by(username=self.username).first():
                if model.id != self.id:
                    return False
            return True

    def is_password_unique(self) -> bool:
        from hiddifypanel.models.user import User
        from hiddifypanel.models.admin import AdminUser
        if isinstance(self, AdminUser):
            if model := AdminUser.query.filter_by(password=self.password).first():
                if model.id != self.id:
                    return False
            return True
        else:
            if model := User.query.filter_by(password=self.password).first():
                if model.id != self.id:
                    return False
            return True

    def get_id(self) -> str | None:
        from hiddifypanel.models.user import User
        from hiddifypanel.models.admin import AdminUser
        if isinstance(self, AdminUser):
            return f'admin_{self.id}'
        if isinstance(self, User):
            return f'user_{self.id}'

    @property
    def role(self) -> Role | None:
        from hiddifypanel.models.user import User
        from hiddifypanel.models.admin import AdminUser, AdminMode
        if isinstance(self, AdminUser):
            match self.mode:
                case AdminMode.super_admin:
                    return Role.super_admin
                case AdminMode.admin:
                    return Role.admin
                case AdminMode.agent:
                    return Role.agent
        if isinstance(self, User):
            return Role.user
