#! /usr/bin/env python
from __future__ import print_function

import pytest
import sys
import os
import subprocess


BASE_PYTEST_ARGS = ['cadasta', '--cov=cadasta', '--cov-report=term-missing']
PYTEST_ARGS = {
    'default': BASE_PYTEST_ARGS,
    'fast': BASE_PYTEST_ARGS + ['-q']
}

BASE_PYTEST_ARGS_FUNCTIONAL = []
PYTEST_ARGS_FUNCTIONAL = {
    'default': BASE_PYTEST_ARGS_FUNCTIONAL,
    'fast': BASE_PYTEST_ARGS_FUNCTIONAL + ['-q'],
}

FLAKE8_ARGS = ['cadasta', '--exclude=migrations']


sys.path.append(os.path.dirname(__file__))


def exit_on_failure(ret, message=None):
    if ret:
        sys.exit(ret)


class tee:
    def __init__(self, _fd1, _fd2):
        self.fd1 = _fd1
        self.fd2 = _fd2

    def __del__(self):
        if self.fd1 != sys.stdout and self.fd1 != sys.stderr:
            self.fd1.close()
        if self.fd2 != sys.stdout and self.fd2 != sys.stderr:
            self.fd2.close()

    def write(self, text):
        self.fd1.write(text)
        self.fd2.write(text)

    def flush(self):
        self.fd1.flush()
        self.fd2.flush()

    def isatty(self):
        return True


def flake8_main(args):
    print('Running flake8 code linting')
    ret = subprocess.run(['flake8'] + args).returncode
    print('flake8 failed' if ret else 'flake8 passed')
    return ret


def functional_main(args):
    print('Running functional tests')
    ret = subprocess.run(['./run.py'] + args,
                         cwd='./functional_tests').returncode
    print('Functional tests failed' if ret else 'Functional tests passed')
    return ret


def split_class_and_function(string):
    class_string, function_string = string.split('.', 1)
    return "%s and %s" % (class_string, function_string)


def is_function(string):
    # `True` if it looks like a test function is included in the string.
    return string.startswith('test_') or '.test_' in string


def is_class(string):
    # `True` if first character is uppercase - assume it's a class name.
    return string[0] == string[0].upper()


if __name__ == "__main__":
    run_flake8 = False
    run_tests = True
    run_functional = False

    try:
        sys.argv.remove('--lint')
    except ValueError:
        pass
    else:
        run_flake8 = True
        run_tests = False

    try:
        sys.argv.remove('--fast')
    except ValueError:
        style = 'default'
    else:
        style = 'fast'

    try:
        sys.argv.remove('--functional')
    except ValueError:
        pass
    else:
        run_flake8 = False
        run_tests = False
        run_functional = True

    if len(sys.argv) > 1:
        pytest_args = sys.argv[1:]
        first_arg = pytest_args[0]
        if first_arg.startswith('-'):
            # `runtests.py [flags]`
            pytest_args = ['tests'] + pytest_args
        elif is_class(first_arg) and is_function(first_arg):
            # `runtests.py TestCase.test_function [flags]`
            expression = split_class_and_function(first_arg)
            pytest_args = ['tests', '-k', expression] + pytest_args[1:]
        elif is_class(first_arg) or is_function(first_arg):
            # `runtests.py TestCase [flags]`
            # `runtests.py test_function [flags]`
            pytest_args = ['tests', '-k', pytest_args[0]] + pytest_args[1:]
        pytest_args_functional = pytest_args
    else:
        pytest_args = PYTEST_ARGS[style]

        if os.environ['DJANGO_SETTINGS_MODULE'] == 'config.settings.travis':
            pytest_args = pytest_args + ['--ds=config.settings.travis']

        pytest_args_functional = PYTEST_ARGS_FUNCTIONAL[style]

    if run_tests:
        stdoutsav = sys.stdout
        outputlog = open('pytest.txt', "w")
        sys.stdout = tee(stdoutsav, outputlog)
        exit_on_failure(pytest.main(pytest_args))
        sys.stdout = stdoutsav
        for l in open('pytest.txt'):
            if l.startswith('TOTAL') and not l.endswith("100%\n"):
                print('Test coverage < 100%')
                exit(1)
    if run_flake8:
        exit_on_failure(flake8_main(FLAKE8_ARGS))
    if run_functional:
        exit_on_failure(functional_main(pytest_args_functional))
