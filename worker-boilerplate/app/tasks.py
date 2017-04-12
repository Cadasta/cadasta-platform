from .celery import app


@app.task(name='export.hello', bind=True)
def hello(self, name='world'):
    self.log("About to download some huge file")
    import time
    time.sleep(.5)
    self.log("Finished downloading.")
    return 'hello {}'.format(name)


@app.task(name='export.email_msg')
def email_msg(msg, to_address):
    # Let's pretend this sends an email
    send_email = print
    send_email("Successfully completed task. Output: {!r}".format(msg))
    return "Email successfully sent"
