import urllib.parse
import base64


def url_encode(strr):
    return urllib.parse.quote(strr)


def do_base_64(str):
    resp = base64.b64encode(f'{str}'.encode("utf-8"))
    return resp.decode()
