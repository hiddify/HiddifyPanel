from enum import auto
import ipaddress
import re
from typing import Dict, List
from flask import request
from flask_babel import lazy_gettext as _
from sqlalchemy.orm import backref
from strenum import StrEnum
from sqlalchemy_serializer import SerializerMixin


from hiddifypanel.database import db
from hiddifypanel.models.config import hconfig
from .child import Child
from hiddifypanel.models.config_enum import ConfigEnum


class DomainType(StrEnum):
    direct = auto()
    sub_link_only = auto()
    cdn = auto()
    auto_cdn_ip = auto()
    relay = auto()
    reality = auto()
    old_xtls_direct = auto()
    worker = auto()
    fake = auto()

    # fake_cdn = "fake_cdn"
    # telegram_faketls = "telegram_faketls"
    # ss_faketls = "ss_faketls"


ShowDomain = db.Table('show_domain',
                      db.Column('domain_id', db.Integer, db.ForeignKey('domain.id'), primary_key=True),
                      db.Column('related_id', db.Integer, db.ForeignKey('domain.id'), primary_key=True)
                      )


class Domain(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), default=0)
    domain = db.Column(db.String(200), nullable=True, unique=False)
    alias = db.Column(db.String(200))
    sub_link_only = db.Column(db.Boolean, nullable=False, default=False)
    mode = db.Column(db.Enum(DomainType), nullable=False, default=DomainType.direct)
    cdn_ip = db.Column(db.Text(2000), nullable=True, default='')
    # port_index=db.Column(db.Integer, nullable=True, default=0)
    grpc = db.Column(db.Boolean, nullable=True, default=False)
    servernames = db.Column(db.String(1000), nullable=True, default='')
    # show_all=db.Column(db.Boolean, nullable=True)
    show_domains = db.relationship('Domain', secondary=ShowDomain,
                                   primaryjoin=id == ShowDomain.c.domain_id,
                                   secondaryjoin=id == ShowDomain.c.related_id,
                                   backref=backref('showed_by_domains', lazy='dynamic')
                                   )
    extra_params = db.Column(db.String(200), nullable=True, default='')

    def __repr__(self):
        return f'{self.domain}'

    def get_cdn_ips_parsed(self):
        ips = re.split('[ \t\r\n;,]+', self.cdn_ip.strip())
        res = set()
        for ip in ips:
            try:
                res.add(ipaddress.ip_address(ip))
            except:
                pass
        return res

    def to_dict(self, dump_ports=False, dump_child_id=False):
        data = {
            'domain': self.domain.lower(),
            'mode': self.mode,
            'alias': self.alias,
            'sub_link_only': self.sub_link_only,
            'child_unique_id': self.child.unique_id if self.child else '',  # type: ignore
            'cdn_ip': self.cdn_ip,
            'servernames': self.servernames,
            'grpc': self.grpc,
            'show_domains': [dd.domain for dd in self.show_domains],  # type: ignore
        }
        if dump_child_id:
            data['child_id'] = self.child_id
        if dump_ports:
            data["internal_port_hysteria2"] = self.internal_port_hysteria2
            data["internal_port_tuic"] = self.internal_port_tuic
            data["internal_port_reality"] = self.internal_port_reality
            data["need_valid_ssl"] = self.need_valid_ssl

        return data

    @staticmethod
    def from_schema(schema):
        return schema.dump(Domain())

    def to_schema(self):
        domain_dict = self.to_dict()
        from hiddifypanel.panel.commercial.restapi.v2.parent.schema import DomainSchema
        return DomainSchema().load(domain_dict)

    @property
    def need_valid_ssl(self):
        return self.mode in [DomainType.direct, DomainType.cdn, DomainType.worker, DomainType.relay, DomainType.auto_cdn_ip, DomainType.old_xtls_direct, DomainType.sub_link_only]

    @property
    def port_index(self):
        return self.id

    @property
    def internal_port_hysteria2(self):
        if self.mode not in [DomainType.direct, DomainType.relay, DomainType.fake]:
            return 0
        # TODO: check validity of the range of the port
        # print("child_id",self.child_id)
        return int(hconfig(ConfigEnum.hysteria_port, self.child_id)) + self.port_index

    @property
    def internal_port_tuic(self):
        if self.mode not in [DomainType.direct, DomainType.relay, DomainType.fake]:
            return 0
        # TODO: check validity of the range of the port
        return int(hconfig(ConfigEnum.tuic_port, self.child_id)) + self.port_index

    @property
    def internal_port_reality(self):
        if self.mode != DomainType.reality:
            return 0
        # TODO: check validity of the range of the port
        return int(hconfig(ConfigEnum.reality_port, self.child_id)) + self.port_index

    @classmethod
    def by_mode(cls, mode: DomainType) -> List['Domain']:
        domains = Domain.query.filter(Domain.mode == mode).all()
        if domains:
            return [d.domain for d in domains]
        return []

    @classmethod
    def modes_and_domains(cls) -> Dict[DomainType, List['Domain']]:
        return {mode: cls.by_mode(mode) for mode in DomainType}

    @classmethod
    def by_domain(cls, domain: str) -> 'Domain | None':
        return Domain.query.filter(Domain.domain == domain).first()

    @classmethod
    def get_panel_link(cls, child_id: int | None = None) -> str | None:
        if child_id is None:
            child_id = Child.current().id  # type: ignore
        domains = Domain.query.filter(Domain.mode.in_(
            [DomainType.direct, DomainType.cdn, DomainType.worker, DomainType.relay, DomainType.auto_cdn_ip, DomainType.old_xtls_direct, DomainType.sub_link_only]),
            Domain.child_id == child_id
        ).all()
        if not domains:
            return None
        return domains[0].domain

    @classmethod
    def get_domains(cls, always_add_ip=False, always_add_all_domains=False) -> List['Domain']:
        from hiddifypanel import hutils
        domains = []
        domains = Domain.query.filter(Domain.mode == DomainType.sub_link_only, Domain.child_id == Child.current().id).all()
        if not len(domains) or always_add_all_domains:
            domains = Domain.query.filter(Domain.mode.notin_([DomainType.fake, DomainType.reality])).all()

        if len(domains) == 0 and request:
            domains = [Domain(domain=request.host)]  # type: ignore
        if len(domains) == 0 or always_add_ip:
            domains += [Domain(domain=hutils.network.get_ip_str(4))]  # type: ignore
        return domains

    @classmethod
    def add_or_update(cls, commit=True, child_id=0, **domain):
        dbdomain = Domain.query.filter(Domain.domain == domain['domain']).first()
        if not dbdomain:
            dbdomain = Domain(domain=domain['domain'])  # type: ignore
            db.session.add(dbdomain)
        dbdomain.child_id = child_id

        dbdomain.mode = domain['mode']
        if (str(domain.get('sub_link_only', False)).lower() == 'true'):
            dbdomain.mode = DomainType.sub_link_only
        dbdomain.cdn_ip = domain.get('cdn_ip', '')
        dbdomain.alias = domain.get('alias', '')
        dbdomain.grpc = domain.get('grpc', False)
        dbdomain.servernames = domain.get('servernames', '')
        show_domains = domain.get('show_domains', [])
        dbdomain.show_domains = Domain.query.filter(Domain.domain.in_(show_domains)).all()
        if commit:
            db.session.commit()

    @classmethod
    def bulk_register(cls, domains, commit=True, remove=False, force_child_unique_id: str | None = None):
        from hiddifypanel.panel import hiddify
        child_ids = {}
        for domain in domains:
            child_id = hiddify.get_child(unique_id=force_child_unique_id)
            child_ids[child_id] = 1
            cls.add_or_update(commit=False, child_id=child_id, **domain)
        if remove and len(child_ids):
            dd = {d['domain']: 1 for d in domains}
            for d in Domain.query.filter(Domain.child_id.in_(child_ids)):
                if d.domain not in dd:
                    db.session.delete(d)

        if commit:
            db.session.commit()
