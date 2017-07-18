from cadasta.workertoolbox.tests import build_functional_tests

from app.celery import app

FunctionalTests = build_functional_tests(app)
