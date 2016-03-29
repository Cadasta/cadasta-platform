import os.path
import factory
from datetime import datetime, timezone
from accounts.tests.factories import UserFactory
from organization.tests.factories import OrganizationFactory, ProjectFactory
from organization.models import OrganizationRole, ProjectRole
from tutelary.models import Policy, Role


# Factories for django-tutelary models.

class PolicyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Policy

    @classmethod
    def set_directory(cls, dir):
        cls.directory = dir

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        body_file = os.path.join(cls.directory, kwargs.pop('file', None))
        kwargs['body'] = open(body_file).read()
        return kwargs


class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role


# USERS

named_users = [
    {'username': 'iross', 'email': 'iross@cadasta.org',
     'first_name': 'Ian', 'last_name': 'Ross'},
    {'username': 'oroick', 'email': 'oroick@cadasta.org',
     'first_name': 'Oliver', 'last_name': 'Roick'}
]
users = []
for i in range(20):
    if i < len(named_users):
        users.append(UserFactory.create(
            **named_users[i], password='password',
            email_verified=True, last_login=datetime.now(tz=timezone.utc),
            is_active=True
        ))
    else:
        users.append(UserFactory.create(password='password',
                                        is_active=(i < 8)))


# POLICIES

PolicyFactory.set_directory('../config/permissions')

pols = {}
for pol in ['default', 'superuser', 'org-admin', 'project-manager',
            'data-collector', 'project-user']:
    pols[pol] = PolicyFactory.create(name=pol, file=pol + '.json')


# ORGANIZATIONS

orgs = []
orgs.append(OrganizationFactory.create(
    name='Habitat for Humanity', slug='habitat-for-humanity',
    description="""Habitat for Humanity is a nonprofit, ecumenical Christian ministry
that builds with people in need regardless of race or religion. Since
1976, Habitat has helped 6.8 million people find strength, stability
and independence through safe, decent and affordable shelter.""",
    urls=['http://www.habitat.org'],
    logo='https://s3.amazonaws.com/cadasta-dev-tmp/logos/h4h.png',
    contacts=[{'email': 'info@habitat.org'}]
))
orgs.append(OrganizationFactory.create(
    name='Cadasta', slug='cadasta',
    description="""Cadasta Foundation is dedicated to the support, continued
development and growth of the Cadasta Platform – an innovative, open
source suite of tools for the collection and management of ownership,
occupancy, and spatial data that meets the unique challenges of this
process in much of the world.""",
    urls=['http://www.cadasta.org'],
    logo='https://s3.amazonaws.com/cadasta-dev-tmp/logos/cadasta.png',
    contacts=[{'email': 'info@cadasta.org'}]
))


# PROJECTS

projs = []
projs.append(ProjectFactory.create(
    name='Kibera',
    project_slug='kibera',
    description="""This is a test project.  This is a test project.  This is a test
project.  This is a test project.  This is a test project.  This is a
test project.  This is a test project.  This is a test project.  This
is a test project.""",
    organization=orgs[0],
    country='KE'
))
projs.append(ProjectFactory.create(
    name='H4H Test Project',
    project_slug='h4h-test-project',
    description="""This is a test project.  This is a test project.  This is a test
project.  This is a test project.  This is a test project.  This is a
test project.  This is a test project.  This is a test project.  This
is a test project.""",
    organization=orgs[0],
    country='PH'
))
projs.append(ProjectFactory.create(
    name='Cadasta Indonesia Test Project',
    project_slug='cadasta-indonesia-test-project',
    description="""This is another test project.  This is another test project.  This
is another test project.  This is another test project.  This is
another test project.  This is a test project.  This is another test
project.  This is another test project.  This is another test
project.""",
    organization=orgs[1],
    country='ID'
))
projs.append(ProjectFactory.create(
    name='Cadasta Myanmar Test Project',
    project_slug='cadasta-myanmar-test-project',
    description="""This is another test project.  This is another test project.  This
is another test project.  This is another test project.  This is
another test project.  This is a test project.  This is another test
project.  This is another test project.  This is another test
project.""",
    organization=orgs[1],
    country='MM'
))


# ROLES

roles = {}
roles['superuser'] = RoleFactory.create(
    name='superuser',
    policies=[pols['default'], pols['superuser']]
)
for org in ['habitat-for-humanity', 'cadasta']:
    for abbrev, pol in [('oa', 'org-admin')]:
        roles[org + '-' + abbrev] = RoleFactory.create(
            name=org + '-' + abbrev,
            policies=[pols['default'], pols[pol]],
            variables={'organization': org}
        )


# USER ROLE ASSIGNMENTS

users[0].assign_policies(roles['superuser'])
users[1].assign_policies(roles['superuser'])


# USER ORGANIZATION MEMBERSHIPS

for i in [0, 1, 3, 4, 7, 10]:
    admin = i == 3 or i == 4
    OrganizationRole.objects.create(
        organization=orgs[0], user=users[i], admin=admin
    )

for i in [0, 1, 2, 4, 8, 10]:
    admin = i == 2 or i == 4
    OrganizationRole.objects.create(
        organization=orgs[1], user=users[i], admin=admin
    )
