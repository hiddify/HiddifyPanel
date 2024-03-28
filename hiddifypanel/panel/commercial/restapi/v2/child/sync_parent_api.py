from apiflask import abort
from flask.views import MethodView
from flask_babel import lazy_gettext as _

from hiddifypanel.auth import login_required
from hiddifypanel import hutils


class SyncWithParentApi(MethodView):
    decorators = [login_required(node_auth=True)]

    def post(self):
        if not hutils.node.child.sync_with_parent():
            abort(400, _('child.sync-failed'))  # type: ignore
        return {'status': 200, 'msg': 'ok'}
