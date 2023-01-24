from flask import g,send_from_directory,url_for
def send_static(path):
    return send_from_directory('static/assets', path)

def init_app(app):    
    @app.url_defaults
    def add_asset(endpoint, values):
        def get_asset(path):
            return url_for('asset',proxy_path=g.proxy_path, path=path)
        g.asset_url=get_asset

    app.add_url_rule('/<proxy_path>/asset/<path:path>','asset',view_func=send_static)
    pass
