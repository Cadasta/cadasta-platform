
from django.test.utils import override_settings
from accounts.tests.factories import UserFactory
from django.contrib.auth.models import Group
from django.db import connection
from django.db.models import Q
from django.test import TestCase
from .factories import OrganizationFactory
from ..models import Organization, OrganizationRole

from core.tests.utils.cases import UserTestCase


@override_settings(DEBUG=True)
def filter_queryset(perms, user):
    ids = []
    user_orgs = Organization.objects.filter(organizationrole__user=user)
    if 'org.view' in perms:
        ids += [
            org.pk for org in Organization.objects.filter(access='public')]
    if 'org.view.private' in perms:
        ids += [
            org.pk for org in user_orgs.filter(access='private')]
    if 'org.view.archived' in perms:
        ids += [
            org.pk for org in user_orgs.filter(archived=True)]
    return Organization.objects.filter(id__in=set(ids))


class OrganizationFilterTest(UserTestCase, TestCase):

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.orgs = OrganizationFactory.create_batch(10)
        self.private_orgs = OrganizationFactory.create_batch(
            3, access='private', add_users=[self.user])
        self.archived_org = OrganizationFactory.create(
            archived=True, add_users=[self.user])
        unauthorized = OrganizationFactory.create(slug='unauthorized')
        self.public_orgs = self.orgs + [unauthorized]
        self.all_orgs = (self.orgs + self.private_orgs +
                         [unauthorized] + [self.archived_org])

    def test_filter_view_public(self):
        perms = ['org.view']
        orgs = filter_queryset(perms, self.user)
        assert orgs.count() == 12
        print(connection.queries)

    def test_filter_view_private(self):
        perms = ['org.view.private']
        orgs = filter_queryset(perms, self.user)
        assert orgs.count() == 3
        print('PRIVATE: ', len(connection.queries),
              ' query(s) \n', connection.queries)

    def test_filter_view_archived(self):
        perms = ['org.view.archived']
        orgs = filter_queryset(perms, self.user)
        assert orgs.count() == 1
        print('ARCHIVED: ', len(connection.queries),
              ' query(s) \n', connection.queries)

    def test_filter_view_private_archived(self):
        perms = ['org.view.private', 'org.view.archived']
        orgs = filter_queryset(perms, self.user)
        assert orgs.count() == 4
        print('PRIVATE_ARCHIVED: ', len(connection.queries),
              ' query(s) \n', connection.queries)

    def test_filter_view_public_private(self):
        perms = ['org.view', 'org.view.private']
        orgs = filter_queryset(perms, self.user)
        assert orgs.count() == 15
        print('PUBLIC_PRIVATE: ', len(connection.queries),
              ' query(s) \n', connection.queries)
