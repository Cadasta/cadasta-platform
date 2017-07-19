import random
import os
from datetime import datetime, timezone

from accounts.models import User
from accounts.tests.factories import UserFactory
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import GEOSGeometry
from faker import Factory
from jsonattrs.models import Attribute, Schema, AttributeType
from organization import models
from organization.tests.factories import OrganizationFactory, ProjectFactory
from spatial.tests.factories import (
    SpatialUnitFactory, SpatialRelationshipFactory
)
from spatial.choices import TYPE_CHOICES
from tutelary.models import Policy, Role


class FixturesData:

    def add_test_users(self):
        users = []
        # the first two named users will have superuser access
        named_users = [
            {'username': 'superuser1', 'email': 'superuser1@cadasta.org',
             'full_name': 'Super User1', 'is_superuser': True},
            {'username': 'superuser2', 'email': 'superuser2@cadasta.org',
             'full_name': 'Super User2', 'is_superuser': True}]
        # add users with names in languages that need to be tested.
        languages = ['el_GR', 'ja_JP', 'hi_IN', 'hr_HR', 'lt_LT']
        named_users.append({
            'full_name': 'עזרא ברש'
        })
        for lang in languages:
            fake = Factory.create(lang)
            named_users.append({
                'full_name': fake.name()
            })
        for n in range(20):
            if n < len(named_users):
                users.append(UserFactory.create(
                    password='password',
                    email_verified=True,
                    last_login=datetime.now(tz=timezone.utc),
                    is_active=True,
                    **named_users[n]
                ))
            else:
                users.append(UserFactory.create(
                    password='password',
                    is_active=(n < 8),
                    full_name=fake.name(),
                ))
        print('\nSuccessfully added test users.')
        return users

    def add_test_users_and_roles(self):
        users = FixturesData.add_test_users(self)
        orgs = models.Organization.objects.all()

        pols = {}
        for pol in ['default', 'superuser', 'org-admin', 'org-member',
                    'project-manager', 'data-collector', 'project-user']:
            pols[pol] = Policy.objects.get(name=pol)

        roles = {}
        roles['superuser'] = Role.objects.get(name='superuser')
        users[0].assign_policies(roles['superuser'])
        users[1].assign_policies(roles['superuser'])

        for i in [0, 1, 3, 4, 7, 10]:
            admin = i == 3 or i == 4
            models.OrganizationRole.objects.create(
                organization=orgs[0], user=users[i], admin=admin
            )

        for i in [0, 1, 2, 4, 8, 10]:
            admin = i == 2 or i == 4
            models.OrganizationRole.objects.create(
                organization=orgs[1], user=users[i], admin=admin
            )

        print("{} and {} have superuser policies.".format(users[0], users[1]))

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

        print('\nSuccessfully added organizations:')
        for org in models.Organization.objects.all():
            print(org.name)

    def add_test_projects(self):
        projs = []
        orgs = models.Organization.objects.filter(name__contains='Test')

        projs.append(ProjectFactory.create(
            name='Kibera Test Project',
            slug='kibera',
            description="""This is a test project.  This is a test project.
            This is a test project.  This is a test project.  This is a test
            project.  This is a test project.  This is a test project.  This
            is a test project.  This is a test project.""",
            organization=orgs[1],
            country='KE',
            extent=('SRID=4326;'
                    'POLYGON ((-5.1031494140625000 8.1299292850467957, '
                    '-5.0482177734375000 7.6837733211111425, '
                    '-4.6746826171875000 7.8252894725496338, '
                    '-4.8641967773437491 8.2278005261522775, '
                    '-5.1031494140625000 8.1299292850467957))')
        ))
        projs.append(ProjectFactory.create(
            name='H4H Test Project',
            slug='h4h-test-project',
            description="""This is a test project.  This is a test project.
            This is a test project.  This is a test project.  This is a test
            project.  This is a test project.  This is a test project.  This
            is a test project.  This is a test project.""",
            organization=orgs[1],
            country='PH',
            extent=('SRID=4326;'
                    'POLYGON ((-63.6328125000000000 44.7233201889582475, '
                    '-63.3691406250000000 45.3830192789906519, '
                    '-61.6992187500000000 45.6140374113509282, '
                    '-61.1059570312500000 45.2439534226232425, '
                    '-63.6328125000000000 44.7233201889582475))')
        ))
        projs.append(ProjectFactory.create(
            name='Cadasta Indonesia Test Project',
            slug='cadasta-indonesia-test-project',
            description="""This is another test project.  This is another test
            project. This is another test project.  This is another test
            project. This is another test project.  This is a test project.
            This is another test project.  This is another test project.
            This is another test project.""",
            organization=orgs[0],
            country='ID',
            extent=('SRID=4326;'
                    'POLYGON ((-57.0520019531250000 -1.0793428942462329, '
                    '-56.7553710937499929 -0.6646579437921112, '
                    '-56.3790893554687500 -1.1562325507679554, '
                    '-56.3186645507812429 -1.4774973547127075, '
                    '-56.8405151367187500 -1.4500404973607948, '
                    '-57.0520019531250000 -1.0793428942462329))')
        ))
        projs.append(ProjectFactory.create(
            name='Cadasta Myanmar Test Project',
            slug='cadasta-myanmar-test-project',
            description=""""This is another test project.  This is another test
            project. This is another test project.  This is another test
            project. This is another test project.  This is a test project.
            This is another test project.  This is another test project.
            This is another test project.""",
            organization=orgs[0],
            country='MM'
        ))
        projs.append(ProjectFactory.create(
            name='London 1 Test Project',
            slug='london-1',
            description=""""This is another test project.  This is another test
            project. This is another test project.  This is another test
            project. This is another test project.  This is a test project.
            This is another test project.  This is another test project.
            This is another test project.""",
            organization=orgs[0],
            country='MM',
            extent=GEOSGeometry(
                '{"type": "Polygon",'
                '"coordinates": [[[-0.17329216003417966,51.51194758264939],'
                '[-0.17303466796874997,51.511092905004745],'
                '[-0.1709747314453125,51.51023821132554],'
                '[-0.17037391662597656,51.507406923983446],'
                '[-0.1746654510498047,51.50211782162702],'
                '[-0.1533794403076172,51.503239803730864],'
                '[-0.15226364135742185,51.505964502406805],'
                '[-0.15913009643554688,51.51322956905176],'
                '[-0.17329216003417966,51.51194758264939]]]}')
        ))
        projs.append(ProjectFactory.create(
            name='London 2 Test Project',
            slug='london-2',
            description=""""This is another test project.  This is another test
            project. This is another test project.  This is another test
            project. This is another test project.  This is a test project.
            This is another test project.  This is another test project.
            This is another test project.""",
            organization=orgs[0],
            country='MM',
            extent=GEOSGeometry(
                '{"type": "Polygon",'
                '"coordinates": [[[-0.1878833770751953,51.509864277798705],'
                '[-0.18393516540527344,51.50201096474784],'
                '[-0.17500877380371094,51.501690392607],'
                '[-0.17226219177246094,51.50671243040582],'
                '[-0.171661376953125,51.51152024583139],'
                '[-0.18642425537109375,51.509864277798705],'
                '[-0.1878833770751953,51.509864277798705]]]}')
        ))

        projs.append(ProjectFactory.create(
            name='Pekapuran Laut Test Project',
            slug='pekapuran-laut',
            description=""""This is another test project.  This is another test
            project. This is another test project.  This is another test
            project. This is another test project.  This is a test project.
            This is another test project.  This is another test project.
            This is another test project.""",
            organization=orgs[1],
            extent=GEOSGeometry(
                '{"type": "Polygon",'
                '"coordinates": [['
                '[-245.39695501327512, -3.328635665488632],'
                '[-245.3934359550476, -3.3269219462897452],'
                '[-245.38717031478882, -3.3309920245190616],'
                '[-245.38652658462524, -3.3319559879515452],'
                '[-245.38832902908322, -3.3329627931951515],'
                '[-245.3892731666565, -3.334226653638199],'
                '[-245.39219141006467, -3.335747568289181],'
                '[-245.3928780555725, -3.3340124401180784],'
                '[-245.39435863494873, -3.3346122378568293],'
                '[-245.39596796035767, -3.3346336591978782],'
                '[-245.3983497619629, -3.333219849687997],'
                '[-245.3981566429138, -3.331934566552203],'
                '[-245.39695501327512, -3.328635665488632]]]}')
        ))

        projs.append(ProjectFactory.create(
            name='Private Cadasta Test Project',
            slug='private-cadasta',
            description=""""This is a private test project.  This is pivate test
            project. This is pivate test project.  This is pivate test
            project. This is pivate test project.  This is a test project.
            This is another test project.  This is another test project.
            This is another test project.""",
            organization=orgs[0],
            extent=GEOSGeometry(
                '{"type": "Polygon",'
                '"coordinates": [['
                '[-21.81009292602539, 64.07722793795327],'
                '[-21.81009292602539, 64.09425757251603],'
                '[-21.76013946533203, 64.09425757251603],'
                '[-21.76013946533203, 64.07722793795327],'
                '[-21.81009292602539, 64.07722793795327]]'
                ']}'),
            access='private'
        ))

        projs.append(ProjectFactory.create(
            name='Private H4H Test Project',
            slug='private-h4h',
            description=""""This is a private test project.  This is pivate test
            project. This is pivate test project.  This is pivate test
            project. This is pivate test project.  This is a test project.
            This is another test project.  This is another test project.
            This is another test project.""",
            organization=orgs[1],
            extent=GEOSGeometry(
                '{"type": "Polygon",'
                '"coordinates": [['
                '[-166.18331909179688, 59.891003681240576],'
                '[-166.18331909179688, 60.06346983332297],'
                '[-165.596923828125, 60.06346983332297],'
                '[-165.596923828125, 59.891003681240576],'
                '[-166.18331909179688, 59.891003681240576]]]}'),
            access='private'
        ))

        print('\nSuccessfully added projects:')
        for proj in models.Project.objects.all():
            print(proj.name)

    def add_test_spatial_units(self):
        project = models.Project.objects.get(
            name__contains='Pekapuran Laut Test Project')

        # add attribute schema
        content_type = ContentType.objects.get(
            app_label='spatial', model='spatialunit')
        sch = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.pk, project.pk))
        attr_type = AttributeType.objects.get(name="text")
        Attribute.objects.create(
            schema=sch, name='name', long_name='Name',
            required=False, index=1, attr_type=attr_type
        )

        su1 = SpatialUnitFactory(
            geometry=GEOSGeometry('{"type": "Polygon",'
                                  '"coordinates": [['
                                  '[-245.3920519351959, -3.3337982265513184],'
                                  '[-245.39097905158997,  -3.333284113800722],'
                                  '[-245.39072155952454, -3.3345908165153215],'
                                  '[-245.39169788360596, -3.3351691925723728],'
                                  '[-245.3920519351959, -3.3337982265513184]]]'
                                  '}'
                                  ),
            project=project,
            type='BU',
            attributes={'name': 'Building Unit (Test)'})

        su2 = SpatialUnitFactory(
            geometry=GEOSGeometry('{"type": "Polygon",'
                                  '"coordinates": [['
                                  '[-245.39200901985168,  -3.333808937230755],'
                                  '[-245.39147257804868, -3.3335304595272377],'
                                  '[-245.391343832016, -3.3340338614721934],'
                                  '[-245.39186954498288, -3.3342480749876575],'
                                  '[-245.39200901985168,  -3.333808937230755]]'
                                  ']}'
                                  ),
            project=project,
            type='AP',
            attributes={"name": "Apartment Unit (Test)"})

        SpatialRelationshipFactory(
            su1=su1, su2=su2, type='C', project=project)

        su3 = SpatialUnitFactory(
            geometry=GEOSGeometry('{"type": "Polygon",'
                                  '"coordinates": [['
                                  '[-245.39088249206543,  -3.333262692430284],'
                                  '[-245.39021730422974, -3.3330699000753414],'
                                  '[-245.39001345634458,  -3.334312339033184],'
                                  '[-245.39063572883606,  -3.334580105844384],'
                                  '[-245.39088249206543,  -3.333262692430284]]'
                                  ']}'
                                  ),
            project=project,
            type='PA',
            attributes={
                'name': 'Parcel (Test)',
            })

        su4 = SpatialUnitFactory(
            geometry=GEOSGeometry('{"type": "Point",'
                                  '"coordinates": ['
                                  '-245.39034605026242, -3.333294824485769]}'
                                  ),
            project=project,
            type='PA')

        SpatialRelationshipFactory(
            su1=su3, su2=su4, type='C', project=project)

        SpatialUnitFactory(
            geometry=GEOSGeometry('{"type": "LineString",'
                                  '"coordinates": ['
                                  '[-245.3934037685394, -3.334258785662196],'
                                  '[-245.39109706878662, -3.3331984283161726],'
                                  '[-245.3895306587219, -3.3328342649235454]]}'
                                  ),
            project=project,
            type='RW')

        SpatialUnitFactory(
            geometry=GEOSGeometry('{"type": "Point",'
                                  '"coordinates": ['
                                  '-245.39366126060483, -3.334130257559935]}'
                                  ),
            project=project,
            type='MI',
            attributes={"name": 'Uncontained Point (Test)'})

        SpatialUnitFactory(
            geometry=GEOSGeometry('{"type": "Point",'
                                  '"coordinates": ['
                                  '-4.9383544921875,'
                                  '7.833452408875349'
                                  ']}'),
            project=models.Project.objects.get(name='Kibera Test Project'),
            type='MI',
            attributes={})

    def add_huge_project(self, max_num_records=4000):
        project = models.Project.objects.get(slug='london-2')
        content_type = ContentType.objects.get(
            app_label='spatial', model='spatialunit')
        attr_type = AttributeType.objects.get(name="text")
        sch = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.pk, project.pk))
        Attribute.objects.create(
            schema=sch, name='name', long_name='Name',
            required=False, index=1, attr_type=attr_type
        )

        spatial_units = []
        choices = [c[0] for c in TYPE_CHOICES]

        with open(os.path.join(os.path.dirname(__file__),
                               "londondata.txt"), "r") as ins:
            for geometry in ins:
                if not geometry.rstrip() or geometry.startswith('#'):
                    continue

                num_records = len(spatial_units)
                if not num_records < max_num_records:
                    break

                name = 'Spatial Unit #{}'.format(num_records)
                type = random.choice(choices)

                spatial_units.append({
                    'geometry': GEOSGeometry(geometry),
                    'type': type,
                    'project': project,
                    'attributes': {'name': name}
                })

        SpatialUnitFactory.create_from_kwargs(spatial_units)

    def delete_test_organizations(self):
        orgs = models.Organization.objects.filter(name__contains='Test')
        for org in orgs:
            org.delete()

    def delete_test_users(self):
        users = User.objects.filter(username__startswith='testuser')
        for user in users:
            models.ProjectRole.objects.filter(user=user).delete()
            models.OrganizationRole.objects.filter(user=user).delete()
            user.delete()
        # Specified named users.
        named_users = ['superuser1', 'superuser2']
        for user in named_users:
            if User.objects.filter(username=user).exists():
                u = User.objects.get(username=user)
                models.ProjectRole.objects.filter(user=u).delete()
                models.OrganizationRole.objects.filter(user=u).delete()
                u.delete()

    def delete_test_projects(self):
        projs = models.Project.objects.filter(name__contains='Test Project')
        projs.delete()
