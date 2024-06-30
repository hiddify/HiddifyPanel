from typing import Optional
from hiddifypanel.models.config_enum import ConfigEnum, LogLevel, PanelMode, Lang
from flask import g

from hiddifypanel import Events
from hiddifypanel.database import db
from hiddifypanel.cache import cache
from hiddifypanel.models.child import Child, ChildMode
from sqlalchemy import Column, String, Boolean, Enum, ForeignKey, Integer
from strenum import StrEnum
from sqlalchemy_serializer import SerializerMixin
from loguru import logger


class BoolConfig(db.Model, SerializerMixin):
    child_id = Column(Integer, ForeignKey('child.id'), primary_key=True, default=0)
    # category = db.Column(db.String(128), primary_key=True)
    key = Column(Enum(ConfigEnum), primary_key=True)
    value = Column(Boolean)

    def to_dict(d):
        return {
            'key': str(d.key),
            'value': d.value,
            'child_unique_id': d.child.unique_id if d.child else ''
        }

    @staticmethod
    def from_schema(schema):
        return schema.dump(BoolConfig())

    def to_schema(self):
        conf_dict = self.to_dict()
        from hiddifypanel.panel.commercial.restapi.v2.parent.schema import HConfigSchema
        return HConfigSchema().load(conf_dict)


class StrConfig(db.Model, SerializerMixin):
    child_id = Column(Integer, ForeignKey('child.id'), primary_key=True, default=0)
    # category = db.Column(db.String(128), primary_key=True)
    key = Column(Enum(ConfigEnum), primary_key=True, default=ConfigEnum.admin_secret)
    value = Column(String(2048))

    def to_dict(self: "StrConfig"):
        return {
            'key': str(self.key),
            'value': self.value,
            'child_unique_id': self.child.unique_id if self.child else ''
        }

    @staticmethod
    def from_schema(schema):
        return schema.dump(StrConfig())

    def to_schema(self):
        conf_dict = self.to_dict()
        from hiddifypanel.panel.commercial.restapi.v2.parent.schema import HConfigSchema
        return HConfigSchema().load(conf_dict)


@cache.cache(ttl=500)
def hconfig(key: ConfigEnum, child_id: Optional[int] = None):  # -> str | int | StrEnum | None:
    if child_id is None:
        child_id = Child.current().id

    value = None
    try:
        if key.type == bool:
            bool_conf = BoolConfig.query.filter(BoolConfig.key == key, BoolConfig.child_id == child_id).first()
            if bool_conf:
                value = bool_conf.value
            else:
                logger.warning(f'bool {key} not found ')
        else:
            str_conf = StrConfig.query.filter(StrConfig.key == key, StrConfig.child_id == child_id).first()
            if str_conf:
                value = str_conf.value
            else:
                logger.warning(f'str {key} not found ')
    except BaseException:
        logger.exception(f'{key} error!')
        raise
    if value != None:
        if key.type == int:
            return int(value)
        elif hasattr(key.type, 'from_str'):
            return key.type.from_str(value)

    return value


def set_hconfig(key: ConfigEnum, value: str | int | bool, child_id: int | None = None, commit: bool = True):
    if child_id is None:
        child_id = Child.current().id

    if key.type == int and value != None:
        int(value)  # for testing int

    # hconfig.invalidate(key, child_id)
    # get_hconfigs.invalidate(child_id)
    hconfig.invalidate(key, child_id)
    hconfig.invalidate(key, child_id=child_id)
    hconfig.invalidate(key=key, child_id=child_id)
    if child_id == Child.current().id:
        hconfig.invalidate(key)
    # hconfig.invalidate_all()
    get_hconfigs.invalidate_all()
    old_v = None
    if key.type == bool:
        dbconf = BoolConfig.query.filter(BoolConfig.key == key, BoolConfig.child_id == child_id).first()
        if not dbconf:
            dbconf = BoolConfig(key=key, value=value, child_id=child_id)
            db.session.add(dbconf)
        else:
            old_v = dbconf.value
    else:
        value = str(value)
        dbconf = StrConfig.query.filter(StrConfig.key == key, StrConfig.child_id == child_id).first()
        if not dbconf:
            dbconf = StrConfig(key=key, value=value, child_id=child_id)
            db.session.add(dbconf)
        else:
            old_v = dbconf.value
    dbconf.value = value
    logger.trace(f"changing {key} from {old_v} to {value}")
    Events.config_changed.notify(conf=dbconf, old_value=old_v)

    if child_id == 0 and key.hide_in_virtual_child:
        for child in Child.query.filter(Child.mode == ChildMode.virtual, Child.id != 0).all():
            set_hconfig(key, value, child.id)

    if commit:
        db.session.commit()


@cache.cache(ttl=500,)
def get_hconfigs(child_id: int | None = None, json=False) -> dict:
    if child_id is None:
        child_id = Child.current().id

    return {**{f'{u.key}' if json else u.key: u.value for u in BoolConfig.query.filter(BoolConfig.child_id == child_id).all() if u.key.type == bool},
            **{f'{u.key}' if json else u.key: int(u.value) if u.key.type == int and u.value != None else u.value for u in StrConfig.query.filter(StrConfig.child_id == child_id).all() if u.key.type != bool},
            }


def get_hconfigs_childs(child_ids: list[int], json=False):
    if len(child_ids) == 0:
        child_ids = [c.id for c in Child.query.all()]
    return {c: get_hconfigs(c, json) for c in child_ids}


def add_or_update_config(commit: bool = True, child_id: int | None = None, override_unique_id: bool = True, **config):
    if child_id is None:
        child_id = Child.current().id
    c = config['key']
    ckey = ConfigEnum(c)
    if c == ConfigEnum.unique_id and not override_unique_id:
        return

    v = str(config['value']).lower() == "true" if ckey.type == bool else config['value']
    if ckey in [ConfigEnum.db_version]:
        return
    set_hconfig(ckey, v, child_id, commit=commit)


def bulk_register_configs(hconfigs, commit: bool = True, froce_child_unique_id: str | None = None, override_unique_id: bool = True):
    from hiddifypanel.panel import hiddify
    for conf in hconfigs:
        if conf['key'] == ConfigEnum.unique_id and not override_unique_id:
            continue
        child_id = hiddify.get_child(unique_id=froce_child_unique_id)
        add_or_update_config(commit=False, child_id=child_id, **conf)
    if commit:
        db.session.commit()
