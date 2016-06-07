from django.test import TestCase
from core.tests.factories import PolicyFactory


class UserTestCase(TestCase):
    def setUp(self):
        PolicyFactory.load_policies()
