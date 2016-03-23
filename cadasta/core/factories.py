import os.path
import factory
from faker import Faker, Factory
from datetime import datetime, timezone

from accounts.models import User
from organization.models import Organization
from tutelary.models import Policy, Role
from accounts.tests.factories import UserFactory
from organization.tests.factories import OrganizationFactory  # ProjectsFactory


class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role


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


class FixturesData():
    def add_test_users(self):
        named_users = [
            {'username': 'iross', 'email': 'iross@cadasta.org',
             'first_name': 'Ian', 'last_name': 'Ross'},
            {'username': 'oroick', 'email': 'oroick@cadasta.org',
             'first_name': 'Oliver', 'last_name': 'Roick'}
        ]
        named_users.append({
            'username': 'testuserhb',
            'email': 'hbuser@example.com',
            'first_name': 'עזרא',
            'last_name': 'ברש'
        })
        users = []
        languages = ['el_GR', 'ja_JP', 'hi_IN', 'hr_HR', 'lt_LT']
        for lang in languages:
            fake = Factory.create(lang)
            named_users.append({
                'username': 'testuser%s' % lang,
                'email': '%suser@example.com' % lang,
                'first_name': fake.first_name(),
                'last_name': fake.last_name()
            })
        for n in range(20):
            if n < len(named_users):
                users.append(UserFactory.create(
                    **named_users[n],
                    password='password',
                    email_verified=True,
                    last_login=datetime.now(tz=timezone.utc),
                    is_active=True,
                ))
            else:
                users.append(UserFactory.create(
                    password='password',
                    email_verified=True,
                    is_active=(n < 8),
                    first_name=factory.Faker('first_name'),
                    last_name=factory.Faker('last_name'),
                ))
        self.stdout.write(self.style.SUCCESS('Successfully added test users.'))
        return users

    # these are being applied but not listed in user objects.
    def add_test_users_and_roles(self):
        users = FixturesData.add_test_users(self)

        PolicyFactory.set_directory('config/permissions')

        pols = {}
        for pol in ['default', 'superuser', 'org-admin', 'project-manager',
                    'data-collector', 'project-user']:
            pols[pol] = PolicyFactory.create(name=pol, file=pol + '.json')

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

        users[0].assign_policies(roles['superuser'])
        users[1].assign_policies(roles['superuser'])
        users[2].assign_policies(roles['cadasta-oa'])
        users[3].assign_policies(roles['habitat-for-humanity-oa'])
        users[4].assign_policies(roles['habitat-for-humanity-oa'], roles['cadasta-oa'])

        self.stdout.write(self.style.SUCCESS(
            '\n%s and %s have superuser policies.\n%s and %s have cadasta-oa policies.\n%s and %s have habitat-for-humanity-oa policies.' % (users[0], users[1], users[2], users[4], users[3], users[4])))

    def add_test_organizations(self):
        orgs = []
        named_orgs = [{
            'name': 'Test: Habitat for Humanity',
            'slug': 'habitat-for-humanity',
            'description': """Habitat for Humanity is a nonprofit, ecumenical Christian ministry
                that builds with people in need regardless of race or religion. Since
                1976, Habitat has helped 6.8 million people find strength, stability
                and independence through safe, decent and affordable shelter.""",
            'urls': ['http://www.habitat.org'],
            'contacts': [{'email': 'info@habitat.org'}],
            'add_users': None
        }, {
            'name': 'Test: Cadasta',
            'slug': 'cadasta',
            'description': """Cadasta Foundation is dedicated to the support, continued
        development and growth of the Cadasta Platform – an innovative, open
        source suite of tools for the collection and management of ownership,
        occupancy, and spatial data that meets the unique challenges of this
        process in much of the world.""",
            'urls': ['http://www.cadasta.org'],
            'contacts': [{'email': 'info@cadasta.org'}],
            'add_users': User.objects.filter(username__startswith='testuser')
        }]
        for org in named_orgs:
            orgs.append(OrganizationFactory.create(
                name=org['name'],
                slug=org['slug'],
                description=org['description'],
                urls=org['urls'],
                contacts=org['contacts'],
                add_users=org['add_users']
            ))

        self.stdout.write(self.style.SUCCESS('\nSuccessfully added organizations "%s"' % Organization.objects.all()))

    # Uncomment once projects have been merged.

    # def add_test_projects(self):
    #     projs = []
    #     orgs = Organization.objects.all()
    #     projs.append(ProjectFactory.create(
    #         name='Kibera',
    #         slug='kibera',
    #         description="""This is a test project.  This is a test project.  This is a test
    #     project.  This is a test project.  This is a test project.  This is a
    #     test project.  This is a test project.  This is a test project.  This
    #     is a test project.""",
    #         organization=orgs[0],
    #         country='KE'
    #     ))
    #     projs.append(ProjectFactory.create(
    #         name='H4H Test Project',
    #         slug='h4h-test-project',
    #         description="""This is a test project.  This is a test project.  This is a test
    #     project.  This is a test project.  This is a test project.  This is a
    #     test project.  This is a test project.  This is a test project.  This
    #     is a test project.""",
    #         organization=orgs[0],
    #         country='PH'
    #     ))
    #     projs.append(ProjectFactory.create(
    #         name='Cadasta Indonesia Test Project',
    #         slug='cadasta-indonesia-test-project',
    #         description="""This is another test project.  This is another test project.  This
    #     is another test project.  This is another test project.  This is
    #     another test project.  This is a test project.  This is another test
    #     project.  This is another test project.  This is another test
    #     project.""",
    #         organization=orgs[1],
    #         country='ID'
    #     ))
    #     projs.append(ProjectFactory.create(
    #         name='Cadasta Myanmar Test Project',
    #         slug='cadasta-myanmar-test-project',
    #         description="""This is another test project.  This is another test project.  This
    #     is another test project.  This is another test project.  This is
    #     another test project.  This is a test project.  This is another test
    #     project.  This is another test project.  This is another test
    #     project.""",
    #         organization=orgs[1],
    #         country='MM'
    #     ))

    def delete_test_organizations(self):
        orgs = Organization.objects.filter(name__startswith='Test:')
        for org in orgs:
            org.delete()

        self.stdout.write(self.style.SUCCESS('Successfully deleted all test organizations. Remaining organizations: "%s"' % Organization.objects.all()))

    def delete_test_users(self):
        users = User.objects.filter(username__startswith='testuser')
        for user in users:
            user.delete()
        # Specified named users.
        named_users = ['iross', 'oroick']
        for user in named_users:
            if User.objects.filter(username=user).exists():
                User.objects.get(username=user).delete()

        self.stdout.write(self.style.SUCCESS('Successfully deleted test users. Remaining users: "%s"' % User.objects.all()))
