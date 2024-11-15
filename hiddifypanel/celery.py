from celery import Celery, Task
from celery.schedules import crontab

def init_app(app):
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    
    celery_app.config_from_object(dict(
        broker_url=app.config['REDIS_URI_MAIN'],
        result_backend=app.config['REDIS_URI_MAIN'],
        # task_ignore_result=True,
    ))
    app.extensions["celery"] = celery_app


        # Calls test('hello') every 10 seconds.
    from hiddifypanel.panel import usage
    celery_app.add_periodic_task(60.0, usage.update_local_usage.s(), name='update usage')
    # celery_app.conf.beat_schedule = {
    # 'update_usage': {
    #     'task': 'hiddifypanel.panel.usage.update_local_usage',
    #     'schedule': 30.0, 

    # },
# }
    from hiddifypanel.panel.cli import backup_task
    celery_app.autodiscover_tasks()
    # celery_app.add_periodic_task(30.0, backup_task.s(), name='backup task')
    # celery_app.add_periodic_task(
    #     crontab(hour="*/6", minute=30),
    #     backup_task.delay(),
    # )

    celery_app.add_periodic_task(
        crontab(hour="*/6", minute="0"),
        backup_task.s(),
        name="backup_task "
    )
    
    celery_app.set_default()
    return celery_app