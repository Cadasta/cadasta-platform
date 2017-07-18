from cadasta.workertoolbox.tests import build_functional_tests

from tasks.celery import app

FunctionalTests = build_functional_tests(app, is_worker=False)
