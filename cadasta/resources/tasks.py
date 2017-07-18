from tasks.celery import app


@app.task(name='export.hello')
def hello(name='world'):
    pass


@app.task(name='export.email_msg')
def email_msg(msg, to_address):
    pass
