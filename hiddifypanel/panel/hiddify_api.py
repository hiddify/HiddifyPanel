from hiddifypanel.models import *
from hiddifypanel.panel import hiddify
import json
def sync_child_to_parent(parent_link=None):
    parent_link= parent_link or hconfig(ConfigEnum.parent_panel)
    if not parent_link:
        raise ConnectionError("no parent link")
    
    return send_to_panel(f"{parent_link}/api/v1/sync_child/",'PUT',hiddify.dump_db_to_dict())

def add_user_usage_to_parent(dbusers_bytes,parent_link=None):
    uuid_bytes={u.uuid:b for u,b in dbusers_bytes.items()}
    uuid_status={u.uuid:is_user_active(u) for u in dbusers_bytes}
    new_user_data=send_to_panel(parent_link+"api/v1/add_usage/",'PUT',uuid_bytes)
    hiddify.set_db_from_json(new_user_data,override_child=True,override_child_id=None,remove_users=True)
    have_change=False
    for u in User.query.all():
        if is_user_active(u) and uuid_status.get(u.uuid,False):
            xray_api.add_client(u.uuid)
        elif not is_user_active(u) and uuid_status.get(u.uuid,True):
            xray_api.remove_client(u.uuid)
    
        

    
    



def send_to_parent_panel(parent_link=None):
    send_to_panel(parent_link)

def send_to_panel(url,method="GET",data=None):
  try:
    import requests
    from requests.adapters import HTTPAdapter
    from requests.packages.urllib3.util.retry import Retry

    retry_strategy = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    
    headers = {'Content-Type': 'application/json',
                'Unique-Id': hconfig(ConfigEnum.unique_id)}
    print(headers)
    if method=="GET":
        response = http.get(url,params=data,headers=headers)
    if method == "PUT":
        response = http.put(url,json=data,headers=headers)
    
    res= response.json()
    print(res)
    return res
  except Exception as e:
    print(e)
    print(url)
    print(headers)
    print(json.dumps(data,indent=4,default=str))
