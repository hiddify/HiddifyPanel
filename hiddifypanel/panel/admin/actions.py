#!/usr/bin/env python3

import pathlib
from hiddifypanel.models import  User,Domain,DomainType,StrConfig,ConfigEnum,hconfig

from datetime import datetime,timedelta,date
import os,sys
import json
import urllib.request
import subprocess
import re

from flask import current_app,render_template,request,Response,Markup,url_for
from flask_admin.base import AdminIndexView,expose,BaseView


@expose('/')
def index():
    return render_template('index.html')
@expose('/reverselog/<logfile>')
def reverselog(logfile):
    config_dir=current_app.config.HIDDIFY_CONFIG_PATH
    with open(f'{config_dir}/log/system/{logfile}') as f:
        lines=[line for line in f]
        resp= Response("".join(lines[::-1]))
        resp.mimetype="text/plain"
        return resp
        
         

@expose('/viewlogs')
def viewlogs():
    config_dir=current_app.config.HIDDIFY_CONFIG_PATH
    res=[]
    for filename in os.listdir(f'{config_dir}/log/system/'):
       res.append(f"<a href='{url_for('admin.actions.reverselog',logfile=filename)}'>{filename}</a>") 
    return Markup("<br>".join(res))
@expose('/apply_configs')
def apply_configs():
    return reinstall(False)

@expose('/reset')
def reset():
    # subprocess.Popen(f"reboot",start_new_session=True)
    return status()
@expose('/reinstall')
def reinstall(complete_install=True):
    config=current_app.config
    file="install.sh" if complete_install else "apply_configs.sh"
    try:
        server_ip=urllib.request.urlopen('https://v4.ident.me/').read().decode('utf8')
    except:
        server_ip="server_ip"

    # subprocess.Popen(f"{config_dir}/update.sh",env=my_env,cwd=f"{config_dir}")
    # os.system(f'cd {config_dir};{env} ./install.sh &')
    # rc = subprocess.call(f"cd {config_dir};./{file} & disown",shell=True)
    subprocess.Popen(f"{config.HIDDIFY_CONFIG_PATH}/{file}",cwd=f"{config.HIDDIFY_CONFIG_PATH}",start_new_session=True)
    admin_secret=hconfig(ConfigEnum.admin_secret)
    proxy_path=hconfig(ConfigEnum.proxy_path)
    admin_links="<h1>Admin Links</h1>"
    admin_links+=f"Not Secure: <a href='http://{server_ip}/{proxy_path}/{admin_secret}/'>http://{server_ip}/{proxy_path}/{admin_secret}/</a><br>"
    domains=[d.domain for d in Domain.query.all()]
    domains=[*domains,f'{server_ip}.sslip.io']
    for d in domains:
            admin_links+=f"<a href='https://{d}/{proxy_path}/{admin_secret}/'>https://{d}/{proxy_path}/{admin_secret}/</a><br>"

    return render_template("result.html",data={
                        "out-type":"success",
                        "out-msg":f"Success! Please wait around {6 if complete_install else 2} minutes to make sure everything is updated. Then, please save your proxy links which are <br>"+
                                admin_links,
                        "log-path":f"https://{server_ip}.sslip.io/{admin_secret}/reverselog/0-install.log"
                        
    })


@expose('/status')
def status():
    config=current_app.config
    # configs=read_configs()
    # subprocess.Popen(f"{config_dir}/update.sh",env=my_env,cwd=f"{config_dir}")
    # os.system(f'cd {config_dir};{env} ./install.sh &')
    # rc = subprocess.call(f"cd {config_dir};./{file} & disown",shell=True)
    from urllib.parse import urlparse
    admin_secret=hconfig(ConfigEnum.admin_secret)
    o = urlparse(request.base_url)
    domain=o.hostname
    subprocess.Popen(f"{config.HIDDIFY_CONFIG_PATH}/status.sh",cwd=f"{config.HIDDIFY_CONFIG_PATH}",start_new_session=True)
    return render_template("result.html",data={
                        "out-type":"success",
                        "out-msg":f"see the log in the bellow screen",
                        "log-path":f"reverselog/status.log"
    })



@expose('/update')
def update():
    config=current_app.config
    cwd = os.getcwd()
    
    # os.chdir(config_dir)
    # rc = subprocess.call(f"./install.sh &",shell=True)
    # rc = subprocess.call(f"cd {config_dir};./update.sh & disown",shell=True)
    # os.system(f'cd {config_dir};./update.sh &')

    subprocess.Popen(f"{config.HIDDIFY_CONFIG_PATH}/update.sh",cwd=f"{config.HIDDIFY_CONFIG_PATH}",start_new_session=True)
    return render_template("result.html",data={
                        "out-type":"success",
                        "out-msg":"Success! Please wait around 5 minutes to make sure everything is updated.<br>",
                        "log-path":"reverselog/update.log"
    })

    






def register_routes(bp):
    bp.add_url_rule("/reverselog/<logfile>", view_func=reverselog)
    bp.add_url_rule("/apply_configs", view_func=apply_configs)
    # bp.add_url_rule("/change", view_func=change)
    bp.add_url_rule("/reinstall", view_func=reinstall)
    bp.add_url_rule("/reset", view_func=reset)
    bp.add_url_rule("/status", view_func=status)
    bp.add_url_rule("/update", view_func=update)
    bp.add_url_rule("/viewlogs", view_func=viewlogs)