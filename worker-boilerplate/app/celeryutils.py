from celery import Task as _Task


class Task(_Task):
    def log(self, msg):
        """ Helper to compose log messages """
        return self.update_state(meta={'log': msg})
