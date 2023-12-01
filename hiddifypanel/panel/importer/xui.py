import sqlite3
import json
from typing import List
import uuid as uuid_mod
from datetime import datetime
from dateutil.relativedelta import relativedelta
from hiddifypanel.models.admin import AdminUser
import hiddifypanel.utils as utils
from hiddifypanel.models.user import User
from hiddifypanel.models.domain import Domain,DomainType
from hiddifypanel.panel import hiddify

# class HUser(namedtuple):
#     uuid = 0
#     up = 0
#     down = 0
#     expiry_data = 0
#     domains = []



def __query_fetch_json(db,query, args=()):
    try:
        db.execute(query,args) if args else db.execute(query)
        r = [dict((db.description[i][0], value) \
                for i, value in enumerate(row)) for row in db.fetchall()]
        return r
    except Exception as err:
        raise err
        

def __is_relity_domain_exists(reality_domains,domain,network):
    return domain in reality_domains and network in reality_domains[domain]

def __get_client_current_usage(db, client_email):
    r = __query_fetch_json(db,'select up,down from client_traffics where email = (?)',(client_email,))

    return r[0]['up'],r[0]['down']

def __get_users_and_reality_domains(db_path):
    users = {}
    reality_domains = {}
    db = None

    try:
        conn = sqlite3.connect(db_path)
        db = conn.cursor()

        x_ui_inbounds = __query_fetch_json(db,'select * from inbounds')

        user_count = 1
        for inbound in x_ui_inbounds:
            inbound['settings'] = json.loads(inbound['settings'])
            for c in inbound['settings']['clients']:
                id = c.get('id',c.get('subId')) or 0 
                # if client(user) is enable and it isn't added already
                if c.get('enable',False) and not id in users:
                    up_current_usage,down_current_usage = __get_client_current_usage(db,c.get('email'))
                    current_usage = up_current_usage + down_current_usage
                    # add user 
                    users[id] = {
                        'name': c.get('email') or f'Imported ({user_count})',
                        'expiry_time': c.get('expiryTime') or 0,
                        'max_usage_bytes': c.get('totalGB') or 0,
                        'telegram_id': c.get('tgId') or 0,
                        # TODO: Don't know it's unit size. Change whatever unit size it is to bytes
                        'current_usage_bytes': current_usage,
                        'enable': c.get('enable') or None,
                    }
                user_count += 1
                
            inbound['stream_settings'] = json.loads(inbound['stream_settings'])
            if inbound['stream_settings']['security'] =='reality':
                    d = inbound['stream_settings']['realitySettings']['dest']
                    network = inbound['stream_settings']['network']

                    if not __is_relity_domain_exists(reality_domains,d,network):
                        reality_domains[d] = {'network':network}
    except Exception as err:
        raise err

    # now we have all users and reality domains
    # convert users to hiddify models
    hiddify_users:List[User] = []
    for id,values in users.items():
        user = User()
        user.name = values['name']
        # check id validity. If it's not valid we create a new one
        user.uuid = id if utils.is_uuid_valid(id,4) else uuid_mod.uuid4()
        if str(values['expiry_time']) == '0':
            user.expiry_time = datetime.now() + relativedelta(years=10)
        else:
            # we have epoch time in milisecoonds so we need to divide it by 1000 to get it in seconds
            user.expiry_time = datetime.fromtimestamp(values['expiry_time']/1000)

        user.usage_limit = values['max_usage_bytes']
        user.current_usage = values['current_usage_bytes']
        user.telegram_id = str(values['telegram_id'])
        user.enable = values['enable']
        user.comment = "imported from x-ui"
        hiddify_users.append(user)

    # convert domains to hiddify models
    hiddify_reality_domains:List[Domain] = []
    for d,values in reality_domains.items():
        domain = Domain()
        domain.domain = d
        domain.grpc = True if values['network'] == 'grpc' else False
        domain.mode = DomainType.reality
        hiddify_reality_domains.append(domain)

    return hiddify_users,hiddify_reality_domains


def import_data(db_path):
    try:
        hiddify_users, hiddify_reality_domains = __get_users_and_reality_domains(db_path)
        for hu in hiddify_users:
            hu.admin = AdminUser.query.first()
        
        # add to hiddify
        hiddify.bulk_register_users([u.to_dict() for u in hiddify_users])
        hiddify.bulk_register_domains([d.to_dict() for d in hiddify_reality_domains])
    except Exception as err:
        raise err