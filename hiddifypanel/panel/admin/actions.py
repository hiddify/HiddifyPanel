#!/usr/bin/env python3

import pathlib
from hiddifypanel.models import  User,Domain,DomainType,StrConfig,ConfigEnum,hconfig

from datetime import datetime,timedelta,date
import os,sys
import json
import urllib.request
import subprocess
import re

from flask import current_app,render_template
from flask_admin.base import AdminIndexView,expose

class Actions(AdminIndexView):

    def reverselog(self,logfile):
        with open(f'{config_dir}/log/system/{logfile}') as f:
            lines=[line for line in f]
            response.content_type = 'text/plain';
            return "".join(lines[::-1])

    @expose('/apply_configs')
    def apply_configs(self):
        return self.reinstall(False)


    def reinstall(self,complete_install=True):
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
        admin_links="<h1>Admin Links</h1>"
        admin_links+=f"<a href='http://{server_ip}/{admin_secret}/'>http://{server_ip}/{admin_secret}/</a><br>"
        for d in Domain.query.filter(Domain.mode in [DomainType.cdn,DomainType.direct]):
                admin_links+="<a href='https://{d.domain}/{admin_secret}/'>https://{d.domain}/{admin_secret}/</a><br>"

        return self.render("result.html",data={
                            "out-type":"success",
                            "out-msg":f"Success! Please wait around {6 if complete_install else 2} minutes to make sure everything is updated. Then, please save your proxy links which are <br>"+
                                    admin_links,
                            "log-path":f"https://{server_ip}.sslip.io/{admin_secret}/reverselog/0-install.log"
                            
        })



    def status(self):
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
        return template("result",data={
                            "out-type":"success",
                            "out-msg":f"see the log in the bellow screen",
                            "log-path":f"reverselog/status.log"
        })



    def update(self):
        config=current_app.config
        cwd = os.getcwd()
        
        # os.chdir(config_dir)
        # rc = subprocess.call(f"./install.sh &",shell=True)
        # rc = subprocess.call(f"cd {config_dir};./update.sh & disown",shell=True)
        # os.system(f'cd {config_dir};./update.sh &')

        subprocess.Popen(f"{config.HIDDIFY_CONFIG_PATH}/update.sh",cwd=f"{config.HIDDIFY_CONFIG_PATH}",start_new_session=True)
        return template("result",data={
                            "out-type":"success",
                            "out-msg":"Success! Please wait around 5 minutes to make sure everything is updated.<br>",
                            "log-path":"reverselog/update.log"
        })

        





