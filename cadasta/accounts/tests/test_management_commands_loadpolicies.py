from django.core.management import call_command
from django.test import TestCase

import accounts.load


class FakeAccountsLoadRun:
    args = None
    kwargs = None
    call_count = 0

    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.call_count += 1


class LoadPoliciesTest(TestCase):
    def setUp(self):
        self.load_run = accounts.load.run
        accounts.load.run = FakeAccountsLoadRun()
        self.addCleanup(setattr, accounts.load, 'run', self.load_run)

    def test_command_no_args(self):
        call_command('loadpolicies')
        assert accounts.load.run.call_count == 1
        assert accounts.load.run.args == ()
        assert accounts.load.run.kwargs == {'force': False, 'update': False}

    def test_command_with_args(self):
        call_command('loadpolicies', force=True, update=True)
        assert accounts.load.run.call_count == 1
        assert accounts.load.run.args == ()
        assert accounts.load.run.kwargs == {'force': True, 'update': True}
