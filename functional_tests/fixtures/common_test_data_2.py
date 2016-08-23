def get_test_data():

    test_data = {}

    # Define superuser and 1 other user
    users = [
        {'username': 'testsuperuser', 'password': 'password',
         '_is_superuser': True},
        {'username': 'testuser', 'password': 'password',
         'email': 'testuser@example.com', 'full_name': 'Test User'},
        {'username': 'testadmin', 'password': 'password',
         'email': 'testadmin@example.com', 'full_name': 'Test Admin'}
    ]
    test_data['users'] = users
    test_data['superuser'] = users[0]

    # Define 2 orgs and their members
    test_data['orgs'] = [
        {'name': "Organization #0", 'description': "This is a test.",
         '_members': (1, 2)},
        {'name': "Organization #1", 'description': "This is a test.",
         '_members': (1,), '_admins': (1,)},
        {'name': "Archived Organization", 'description': "This is archived.",
         "archived": True, '_members': (1, 2), '_admins': (2,)},
    ]

    # Define 1 project.
    test_data['projects'] = [
        {
            'name': 'Test Project',
            'slug': 'test-project',
            'description': """This is a test project.  This is a test project.
            This is a test project.  This is a test project.  This is a test
            project.  This is a test project.  This is a test project.  This
            is a test project.  This is a test project.""",
            '_org': 0,
            'archived': False,
            'country': 'KE',
            'extent': ('SRID=4326;'
                       'POLYGON ((-5.1031494140625000 8.1299292850467957, '
                       '-5.0482177734375000 7.6837733211111425, '
                       '-4.6746826171875000 7.8252894725496338, '
                       '-4.8641967773437491 8.2278005261522775, '
                       '-5.1031494140625000 8.1299292850467957))')
        },
        {
            'name': 'Archived Project',
            'slug': 'archived-project',
            'description': """This is a test project.  This is a test project.
            This is a test project.  This is a test project.  This is a test
            project.  This is a test project.  This is a test project.  This
            is a test project.  This is a test project.""",
            '_org': 0,
            'archived': True,
            'country': 'KE',
            'extent': ('SRID=4326;'
                       'POLYGON ((-5.1031494140625000 8.1299292850467957, '
                       '-5.0482177734375000 7.6837733211111425, '
                       '-4.6746826171875000 7.8252894725496338, '
                       '-4.8641967773437491 8.2278005261522775, '
                       '-5.1031494140625000 8.1299292850467957))')
        }
    ]

    return test_data
