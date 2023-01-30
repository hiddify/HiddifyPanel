from flask_admin.base import AdminIndexView,expose
from hiddifypanel.panel.hiddify  import admin

class Dashboard(AdminIndexView):
    @expose("/")
    
    # @admin
    def index(self):
        arg1 = 'Hello'
        print("TEST")
        # return "D"
        
        return self.render('index.html', arg1=arg1)