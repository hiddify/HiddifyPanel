from apiflask import abort
from flask.views import MethodView
from flask_babel import lazy_gettext as _

from hiddifypanel.auth import login_required
from hiddifypanel.panel import hiddify_api


class SyncWithParentApi(MethodView):
    decorators = [login_required(child_parent_auth=True)]

    def post(self):
        if not hiddify_api.sync_child_with_parent(True):
            abort(400, _('child.sync-failed'))  # type: ignore
        return {'status': 200, 'msg': 'ok'}
