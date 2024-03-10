class Event:
    def __init__(self, name):
        self.name = name
        self.callbacks = []

    def subscribe(self, callback):
        self.callbacks.append(callback)

    def unsubscribe(self, callback):
        self.callbacks.remove(callback)

    def notify(self, **data):
        for callback in self.callbacks:
            if isinstance(data, dict):
                callback(**data)
            else:
                callback(data)


config_changed = Event('config_changed')
user_changed = Event('user_changed')
domain_changed = Event('domain_changed')
parentdomain_changed = Event('parentdomain_changed')
admin_prehook = Event('admin_prehook')
db_prehook = Event('db_prehook')


db_init_event = Event('db_init')
