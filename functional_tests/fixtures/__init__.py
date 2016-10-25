from tutelary.models import Role
from accounts.tests.factories import UserFactory
from organization.tests.factories import OrganizationFactory, ProjectFactory
from organization.models import OrganizationRole


def assign_superuser_role(user):
    user.assign_policies(Role.objects.get(name='superuser'))


def load_test_data(data):
    retval = {}

    # Load users
    if 'users' in data:
        user_objs = []  # For assigning members to orgs later
        for user in data['users']:
            # Drop all keys starting with an underscore for user creation
            args = {k: v for k, v in user.items() if not k.startswith('_')}
            user_objs.append(UserFactory.create(**args))
            if user.get('_is_superuser'):
                assign_superuser_role(user_objs[-1])
    retval['users'] = user_objs

    # Load orgs
    org_objs = []  # For anchoring projects to orgs later
    if 'orgs' in data:
        for org in data['orgs']:
            kwargs = org.copy()
            for key in ('_members', '_admins'):
                if key in org:
                    del kwargs[key]
            org_obj = OrganizationFactory.create(**kwargs)
            org_objs.append(org_obj)
            if '_members' in org:
                admin_idxs = []
                if '_admins' in org:
                    admin_idxs = org['_admins']
                for member_idx in org['_members']:
                    OrganizationRole.objects.create(
                        organization=org_obj,
                        user=user_objs[member_idx],
                        admin=member_idx in admin_idxs,
                    )
    retval['organizations'] = org_objs

    # Load projects
    proj_objs = []
    if 'projects' in data:
        for project in data['projects']:
            assert '_org' in project
            kwargs = project.copy()
            kwargs['organization'] = org_objs[kwargs['_org']]
            del kwargs['_org']
            if '_managers' in project:
                org_idx = project['_org']
                org_member_idxs = data['orgs'][org_idx]['_members']
                for idx in project['_managers']:
                    assert idx in org_member_idxs
                del kwargs['_managers']
            proj_obj = ProjectFactory.create(**kwargs)
            proj_objs.append(proj_obj)
    retval['projects'] = proj_objs

    return retval
