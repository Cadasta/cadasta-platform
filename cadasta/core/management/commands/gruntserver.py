import os
import subprocess
import atexit
import signal

from django.contrib.staticfiles.management.commands import runserver

from config.settings import default


class Command(runserver.Command):

    def inner_run(self, *args, **options):
        self.start_grunt()
        return super(Command, self).inner_run(*args, **options)

    def start_grunt(self):
        self.stdout.write('>>> Starting grunt')
        self.stdout.write(default.BASE_DIR)
        self.grunt_process = subprocess.Popen(
            [('grunt runserver --gruntfile=/vagrant/Gruntfile.js')],
            shell=True,
            stdin=subprocess.PIPE,
            stdout=self.stdout,
            stderr=self.stderr,
            )

        self.stdout.write('>>> Grunt process on pid {0}'.format(
            self.grunt_process.pid))

        def kill_grunt_process(pid):
            self.stdout.write('>>> Closing grunt process')
            os.kill(pid, signal.SIGTERM)

        atexit.register(kill_grunt_process, self.grunt_process.pid)
