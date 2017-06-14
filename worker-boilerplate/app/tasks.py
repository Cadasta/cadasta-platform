from celery import group

from .celery import app


@app.task(name='export.hello', bind=True)
def hello(self, name='world'):
    self.log("About to download some huge file")
    self.log("Finished downloading.")
    return 'hello {}'.format(name)


@app.task(name='export.email_msg')
def email_msg(msg, to_address):
    # Let's pretend this sends an email
    print(msg, to_address)
    send_email = print
    send_email("Successfully completed task. Output: {!r}".format(msg))
    return "Email successfully sent"


@app.task(name='export.separate', bind=True)
def _separate(self):
    hello.apply_async(args=['bob'], queue='export')
    hello.apply_async(args=['suzy'], queue='export')
    return True


@app.task(name='export.chain')
def _chain():
    (
        hello.si('bob').set(queue='export') |
        hello.si('suzy').set(queue='export')
    )()
    return True


@app.task(name='export.group')
def _group():
    group(
        hello.si('bob').set(queue='export'),
        hello.si('suzy').set(queue='export')
    )()
    return True


@app.task(name='export.chord')
def _chord():
    (
        group(
            hello.si('bob').set(
                queue='export',
                task_id='ID_hello_bob'),
            hello.si('suzy').set(
                queue='export',
                task_id='ID_hello_suzy')
        ) | email_msg.s(to_address='foo@bar.com').set(
            queue='export',
            task_id='ID_email_msg_followup',
        )
    )()

    return True


# @app.task('export.export_data')
# def export_data(projects_url):
#     response_json = requests.get(projects_url).json()
#     if response_json['next']:
#         followup_urls = generate_followup_urls(response_json['next'])
#         tasks = [fetch_url.s(url) for url in followup_urls]
#         tasks.append(noop.s(response_json))

#         # Schedule all requests and followup merge+create tasks
#         return chord(*tasks)(create_zip.s())
#     else:
#         return create_zip(response['results'])


# @app.task()
# def fetch_url(url):
#     return requests.get(url).json()


# @app.task()
# def noop(data):
#     return data


# @app.task()
# def create_zip(data_array):
#     return create_zip(
#         [item for response in data_array for item in response['results']])
