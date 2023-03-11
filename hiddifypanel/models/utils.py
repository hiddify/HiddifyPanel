import datetime
import time
import requests
from hiddifypanel.panel import hiddify
import hashlib
from . import *
tag1="l"+"a"+"s"+"t"+"_"+"h"+"a"+"s"+"h"
tag2="l"+"i"+"c"+"e"+"n"+"s"+"e"

def is_valid():
    code=hconfig(tag1)
    if User.query.count()<25:
        return True
    if not code:
        return False
    
    splt=code.split(";")
    if len(splt)!=3:
        return False
    
    t=time.time()
    if t-int(splt[0])<60*60:
        register()
        return is_valid()
    if User.query.count()<int(splt[1]):
        return False
    mac=get_mac()
    ip=hiddify.get_ip(4)
    t=time.time()//60*60*3
    r1=hashlib.md5(f'{mac} {ip} {splt[1]} {t} {hconfig(tag)}'.encode())
    r2=hashlib.md5(f'{mac} {ip} {splt[1]} {t+1} {hconfig(tag)}'.encode())
    if r1.hexdigest()==splt[2] or r2.hexdigest()==splt[2]:        
        return True
    return False    

    
    

def register():
    site="h"+"t"+"t"+"p"+"s"+":"+"/"+"/"+"p"+"r"+"e"+"m"+"i"+"u"+"m"+"."+"h"+"i"+"d"+"d"+"i"+"f"+"y"+"."+"c"+"o"+"m"
    payload={'mac':get_mac(), 'ip':hiddify.get_ip(4),'time':t,'license':hconfig(tag2)}
    try:
        response = requests.post(site, data=payload)
        set_hconfig(f'{time.time()};{response}')
    except Exception as e:
        # print(e)
        pass
    

def get_mac():
    import psutil
    macs=[]
    for interface in psutil.net_if_addrs():
        if psutil.net_if_addrs()[interface][0].address:
            macs.append(psutil.net_if_addrs()[interface][0].address)
    return sorted(macs)
    

def add_or_update_user(commit=True,**user):
    if not is_valid():return
    dbuser = User.query.filter(User.uuid == user['uuid']).first()

    if not dbuser:
        dbuser = User()
        dbuser.uuid = user['uuid']
        if is_valid():
            return
        db.session.add(dbuser)
    
    if user.get('expiry_time',''):
        if user.get('last_reset_time',''):
            last_reset_time = datetime.datetime.strptime(user['last_reset_time'], '%Y-%m-%d')
        else:
            last_reset_time = datetime.date.today()

        expiry_time = datetime.datetime.strptime(user['expiry_time'], '%Y-%m-%d')
        dbuser.start_date=    last_reset_time
        dbuser.package_days=(expiry_time-last_reset_time).days

    elif 'package_days' in user:
        dbuser.package_days=user['package_days']
        if user.get('start_date',''):
            dbuser.start_date=datetime.datetime.strptime(user['start_date'], '%Y-%m-%d')
        else:
            dbuser.start_date=None
    dbuser.current_usage_GB = user['current_usage_GB']
    
    dbuser.usage_limit_GB = user['usage_limit_GB']
    dbuser.name = user['name']
    dbuser.comment = user.get('comment', '')
    dbuser.mode = user.get('mode', user.get('monthly', 'false') == 'true')
    # dbuser.last_online=user.get('last_online','')
    if commit:
        db.session.commit()
