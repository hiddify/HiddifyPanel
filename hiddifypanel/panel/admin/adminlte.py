from flask_admin.contrib.sqla import ModelView
from hiddifypanel import auth
from flask_admin.form import SecureForm


class AdminLTEModelView(ModelView):
    form_base_class = SecureForm
    edit_modal = True
    create_modal = True

    list_template = 'hiddify-flask-admin/list.html'
    create_template = 'flask-admin/model/create.html'
    edit_template = 'flask-admin/model/edit.html'
    details_template = 'flask-admin/model/details.html'

    create_modal_template = 'flask-admin/model/modals/create.html'
    edit_modal_template = 'flask-admin/model/modals/edit.html'
    details_modal_template = 'flask-admin/model/modals/details.html'

    # form_base_class = SecureForm
    def inaccessible_callback(self, name, **kwargs):
        return auth.redirect_to_login()  # type: ignore
