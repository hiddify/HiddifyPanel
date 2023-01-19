from flask_admin.base import AdminIndexView,expose

class Dashboard(AdminIndexView):
    @expose('/')
    def index(self):
        arg1 = 'Hello'
        return self.render('index.html', arg1=arg1)