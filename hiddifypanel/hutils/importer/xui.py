import sqlite3
import json
import os
import uuid as uuid_mod
from typing import Any, Dict, List, Tuple
from datetime import datetime
from dateutil.relativedelta import relativedelta

from hiddifypanel import hutils
from hiddifypanel.models import *
from hiddifypanel.database import db, db_execute


def __query_fetch_json(db, query: str, **kwargs) -> List[Dict[str, Any]]:
    try:

        db_execute(query, commit=True, return_val=False, **kwargs)
        r = [dict((db.description[i][0], value)
                  for i, value in enumerate(row)) for row in db.fetchall()]
        return r
    except Exception as err:
        raise err


def __is_reality_domain_exists(reality_domains: Dict[str, Dict[str, Any]], domain: str, network: str) -> bool:
    return domain in reality_domains and network in reality_domains[domain]


def __get_client_current_usage(db, client_email: str) -> Tuple[int, int]:
    r = __query_fetch_json(db, 'select up,down from client_traffics where email = (?)', (client_email,))
    if not r or not r[0] or not r[0]['up'] or not r[0]['down']:
        return 0, 0
    return int(r[0]['up']), int(r[0]['down'])


def __get_users(db, x_ui_inbounds):
    users = {}
    user_count = 1

    for inbound in x_ui_inbounds:
        inbound['settings'] = json.loads(inbound['settings'])
        for c in inbound['settings']['clients']:
            id = c.get('id', c.get('subId')) or 0

            if c.get('enable', False) and id not in users:
                up_current_usage, down_current_usage = __get_client_current_usage(db, c.get('email'))
                current_usage = up_current_usage + down_current_usage

                users[id] = {
                    'name': c.get('email') or f'Imported ({user_count})',
                    'expiry_time': c.get('expiryTime') or 0,
                    'max_usage_bytes': c.get('totalGB') or 0,
                    'telegram_id': c.get('tgId') or 0,
                    'current_usage_bytes': current_usage,
                    'enable': c.get('enable') or None,
                }
            user_count += 1

    return users


def __create_hiddify_user_from_xui_values(id: str, values: Dict[str, Any]) -> "User":
    user = User()
    user.name = values['name']
    user.uuid = id if hutils.auth.is_uuid_valid(id, 4) else uuid_mod.uuid4()

    if str(values['expiry_time']) == '0':
        user.package_days = 3650
    else:
        user.package_days = max(0, (datetime.fromtimestamp(values['expiry_time'] / 1000) - datetime.today()).days)

    user.usage_limit = values['max_usage_bytes']
    user.current_usage = values['current_usage_bytes']
    user.telegram_id = int(values['telegram_id'])
    user.enable = values['enable']
    user.comment = "Imported from X-UI"
    user.admin = AdminUser.current_admin_or_owner()

    return user


def __get_reality_domains(x_ui_inbounds):
    reality_domains = {}

    for inbound in x_ui_inbounds:
        inbound['stream_settings'] = json.loads(inbound['stream_settings'])
        if inbound['stream_settings']['security'] == 'reality':
            d = inbound['stream_settings']['realitySettings']['dest']
            network = inbound['stream_settings']['network']

            if not __is_reality_domain_exists(reality_domains, d, network):
                reality_domains[d] = {'network': network}

    return reality_domains


def __create_hiddify_domain_from_xui_values(domain: str, values: Dict[str, Any]) -> Domain:
    d = Domain()
    d.domain = domain
    d.grpc = values['network'] == 'grpc'
    d.mode = DomainType.reality
    return d


def __extract_users_and_domains_from_xui_db(db_path: str) -> Tuple[List["User"], List["Domain"]]:
    users = {}
    reality_domains = {}

    try:
        with sqlite3.connect(db_path) as conn:
            db = conn.cursor()

            x_ui_inbounds = __query_fetch_json(db, 'select * from inbounds')

            # get xui users and reality domains as a dict
            users = __get_users(db, x_ui_inbounds)
            reality_domains = __get_reality_domains(x_ui_inbounds)

        # convert xui users and reality domains to hiddify users and domains (to hiddify models)
        hiddify_users = [__create_hiddify_user_from_xui_values(id, values) for id, values in users.items()]
        # set default package days
        for u in hiddify_users:
            if not u.package_days:
                u.package_days = 90
            if not u.last_reset_time:
                u.last_reset_time = datetime.now()
            if not u.mode:
                u.mode = UserMode.monthly
        hiddify_reality_domains = [__create_hiddify_domain_from_xui_values(d, values) for d, values in reality_domains.items()]
        return hiddify_users, hiddify_reality_domains

    except Exception as err:
        raise err


def import_data(db_path: str):
    assert os.path.exists(db_path), "The db file doesn't exist"
    try:
        hiddify_users, hiddify_reality_domains = __extract_users_and_domains_from_xui_db(db_path)

        hiddify_users_dict = [u.to_dict() for u in hiddify_users]
        hiddify_domains_dict = [d.to_dict() for d in hiddify_reality_domains]

        for u in hiddify_users_dict:
            User.add_or_update(commit=False, **u)

        for d in hiddify_domains_dict:
            Domain.add_or_update(commit=False, **d)

        db.session.commit()  # type: ignore
    except Exception as err:
        raise err
