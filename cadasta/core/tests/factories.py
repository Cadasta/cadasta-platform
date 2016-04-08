import os.path
import factory
from faker import Factory
from django.contrib.gis.geos import GEOSGeometry
from datetime import datetime, timezone

from accounts.models import User
from organization.models import Organization, Project, OrganizationRole
from tutelary.models import Policy, Role, PolicyInstance, RolePolicyAssign

from accounts.tests.factories import UserFactory
from organization.tests.factories import OrganizationFactory, ProjectFactory


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


class FixturesData():
    def add_test_users(self):
        users = []
        # the first two named users will have superuser access
        named_users = [
            {'username': 'iross', 'email': 'iross@cadasta.org',
             'first_name': 'Ian', 'last_name': 'Ross'},
            {'username': 'oroick', 'email': 'oroick@cadasta.org',
             'first_name': 'Oliver', 'last_name': 'Roick'}]
        # add user's with names in languages that need to be tested.
        languages = ['el_GR', 'ja_JP', 'hi_IN', 'hr_HR', 'lt_LT']
        named_users.append({
            'first_name': 'עזרא',
            'last_name': 'ברש'
        })
        for lang in languages:
            fake = Factory.create(lang)
            named_users.append({
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
                    is_active=(n < 8),
                    first_name=factory.Faker('first_name'),
                    last_name=factory.Faker('last_name'),
                ))
        self.stdout.write(self.style.SUCCESS('Successfully added test users.'))
        return users

    def add_test_users_and_roles(self):
        users = FixturesData.add_test_users(self)
        orgs = Organization.objects.all()

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
                    variables={'organization': org})

        users[0].assign_policies(roles['superuser'])
        users[1].assign_policies(roles['superuser'])

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

        self.stdout.write(self.style.SUCCESS(
            "{} and {} have superuser policies."
            .format(users[0], users[1])))

    def add_test_organizations(self):
        orgs = []
        orgs.append(OrganizationFactory.create(
            name='Habitat for Humanity (Test)', slug='habitat-for-humanity',
            description="""Habitat for Humanity is a nonprofit, ecumenical Christian ministry
        that builds with people in need regardless of race or religion. Since
        1976, Habitat has helped 6.8 million people find strength, stability
        and independence through safe, decent and affordable shelter.""",
            urls=['http://www.habitat.org'],
            logo='https://s3.amazonaws.com/cadasta-dev-tmp/logos/h4h.png',
            contacts=[{'email': 'info@habitat.org'}]
        ))
        orgs.append(OrganizationFactory.create(
            name='Cadasta (Test)', slug='cadasta',
            description="""Cadasta Foundation is dedicated to the support, continued
        development and growth of the Cadasta Platform – an innovative, open
        source suite of tools for the collection and management of ownership,
        occupancy, and spatial data that meets the unique challenges of this
        process in much of the world.""",
            urls=['http://www.cadasta.org'],
            logo='https://s3.amazonaws.com/cadasta-dev-tmp/logos/cadasta.png',
            contacts=[{'email': 'info@cadasta.org'}]
        ))

        self.stdout.write(self.style.SUCCESS(
            '\nSuccessfully added organizations {}'
            .format(Organization.objects.all())))

    def add_test_projects(self):
        projs = []
        orgs = Organization.objects.filter(name__contains='Test')

        projs.append(ProjectFactory.create(
            name='Kibera Test Project',
            project_slug='kibera',
            description="""This is a test project.  This is a test project.
            This is a test project.  This is a test project.  This is a test
            project.  This is a test project.  This is a test project.  This
            is a test project.  This is a test project.""",
            organization=orgs[0],
            country='KE',
            extent='SRID=4326;POLYGON ((-5.1031494140625000 8.1299292850467957, -5.0482177734375000 7.6837733211111425, -4.6746826171875000 7.8252894725496338, -4.8641967773437491 8.2278005261522775, -5.1031494140625000 8.1299292850467957))'
        ))
        projs.append(ProjectFactory.create(
            name='H4H Test Project',
            project_slug='h4h-test-project',
            description="""This is a test project.  This is a test project.
            This is a test project.  This is a test project.  This is a test
            project.  This is a test project.  This is a test project.  This
            is a test project.  This is a test project.""",
            organization=orgs[0],
            country='PH',
            extent='SRID=4326;POLYGON ((-63.6328125000000000 44.7233201889582475, -63.3691406250000000 45.3830192789906519, -61.6992187500000000 45.6140374113509282, -61.1059570312500000 45.2439534226232425, -63.6328125000000000 44.7233201889582475))'
        ))
        projs.append(ProjectFactory.create(
            name='Cadasta Indonesia Test Project',
            project_slug='cadasta-indonesia-test-project',
            description="""This is another test project.  This is another test
            project. This is another test project.  This is another test
            project. This is another test project.  This is a test project.
            This is another test project.  This is another test project.
            This is another test project.""",
            organization=orgs[1],
            country='ID',
            extent='SRID=4326;POLYGON ((-57.0520019531250000 -1.0793428942462329, -56.7553710937499929 -0.6646579437921112, -56.3790893554687500 -1.1562325507679554, -56.3186645507812429 -1.4774973547127075, -56.8405151367187500 -1.4500404973607948, -57.0520019531250000 -1.0793428942462329))'
        ))
        projs.append(ProjectFactory.create(
            name='Cadasta Myanmar Test Project',
            project_slug='cadasta-myanmar-test-project',
            description=""""This is another test project.  This is another test
            project. This is another test project.  This is another test
            project. This is another test project.  This is a test project.
            This is another test project.  This is another test project.
            This is another test project.""",
            organization=orgs[1],
            country='MM'
        ))
        projs.append(ProjectFactory.create(
            name='London 1',
            project_slug='london-1',
            description=""""This is another test project.  This is another test
            project. This is another test project.  This is another test
            project. This is another test project.  This is a test project.
            This is another test project.  This is another test project.
            This is another test project.""",
            organization=orgs[1],
            country='MM',
            extent=GEOSGeometry('{"type": "Polygon","coordinates": [[[-0.17329216003417966,51.51194758264939],[-0.17303466796874997,51.511092905004745],[-0.1709747314453125,51.51023821132554],[-0.17037391662597656,51.507406923983446],[-0.1746654510498047,51.50211782162702],[-0.1533794403076172,51.503239803730864],[-0.15226364135742185,51.505964502406805],[-0.15913009643554688,51.51322956905176],[-0.17329216003417966,51.51194758264939]]]}')
        ))
        projs.append(ProjectFactory.create(
            name='London 2',
            project_slug='london-2',
            description=""""This is another test project.  This is another test
            project. This is another test project.  This is another test
            project. This is another test project.  This is a test project.
            This is another test project.  This is another test project.
            This is another test project.""",
            organization=orgs[1],
            country='MM',
            extent=GEOSGeometry('{"type": "Polygon","coordinates": [[[-0.1878833770751953,51.509864277798705],[-0.18393516540527344,51.50201096474784],[-0.17500877380371094,51.501690392607],[-0.17226219177246094,51.50671243040582],[-0.171661376953125,51.51152024583139],[-0.18642425537109375,51.509864277798705],[-0.1878833770751953,51.509864277798705]]]}')
        ))
        self.stdout.write(self.style.SUCCESS(
            '\nSuccessfully added organizations {}'
            .format(Project.objects.all())))

    def delete_test_organizations(self):
        orgs = Organization.objects.filter(name__contains='Test')
        for org in orgs:
            org.delete()

        PolicyInstance.objects.all().delete()
        RolePolicyAssign.objects.all().delete()
        Policy.objects.all().delete()
        Role.objects.all().delete()

    def delete_test_users(self):
        users = User.objects.filter(username__startswith='testuser')
        for user in users:
            user.delete()
        # Specified named users.
        named_users = ['iross', 'oroick']
        for user in named_users:
            if User.objects.filter(username=user).exists():
                User.objects.get(username=user).delete()

    def delete_test_projects(self):
        projs = Project.objects.filter(name__contains='Test Project')
        projs.delete()
