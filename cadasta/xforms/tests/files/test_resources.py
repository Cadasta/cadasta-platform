FORM = '''<?xml version=\'1.0\' ?>
    <test_standard_questionnaire
        id="test_standard_questionnaire" version="20160727122110">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <party_type>IN</party_type>
        <party_name>Bilbo Baggins</party_name>
        <location_geometry>40.6890612 -73.9925067 0.0 0.0;</location_geometry>
        <location_type>MI</location_type>
        <location_photo>test_image_one.png</location_photo>
        <party_photo>test_image_two.png</party_photo>
        <tenure_type>LH</tenure_type>
        <location_attributes>
            <name>Middle Earth</name>
        </location_attributes>
        <party_attributes_default>
            <notes>Party attribute default notes.</notes>
        </party_attributes_default>
        <party_attributes_individual>
            <gender>f</gender>
            <homeowner>no</homeowner>
            <dob>2016-07-07</dob>
        </party_attributes_individual>
        <party_relationship_attributes>
            <notes>Party relationship notes.</notes>
        </party_relationship_attributes>
        <tenure_relationship_attributes>
            <notes>Tenure relationship notes.</notes>
        </tenure_relationship_attributes>
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </test_standard_questionnaire>'''.strip()

FORM_2_RESOURCES = '''<?xml version=\'1.0\' ?>
    <test_standard_questionnaire
        id="test_standard_questionnaire" version="20160727122110">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <party_type>IN</party_type>
        <party_name>Bilbo Baggins</party_name>
        <location_geometry />
        <location_type>MI</location_type>
        <location_photo>test_image_one.png</location_photo>
        <party_photo>test_image_two.png</party_photo>
        <tenure_type>LH</tenure_type>
        <location_attributes>
            <name>Middle Earth</name>
        </location_attributes>
        <party_attributes_default>
            <notes>Party attribute default notes.</notes>
        </party_attributes_default>
        <party_attributes_individual>
            <gender>f</gender>
            <homeowner>no</homeowner>
            <dob>2016-07-07</dob>
        </party_attributes_individual>
        <party_relationship_attributes>
            <notes>Party relationship notes.</notes>
        </party_relationship_attributes>
        <tenure_relationship_attributes>
            <notes>Tenure relationship notes.</notes>
        </tenure_relationship_attributes>
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </test_standard_questionnaire>'''.strip()

INVALID_FORM = '''<?xml version=\'1.0\' ?>
    <test_standard_questionnaire
        id="test_standard_questionnaire" version="20160727122110">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <party_type>IN</party_type>
        <party_name></party_name>
        <location_geometry>40.6890612 -73.9925067 0.0 0.0;</location_geometry>
        <location_type>MI</location_type>
        <location_photo>test_image.png</location_photo>
        <party_photo />
        <tenure_type>LH</tenure_type>
        <location_attributes>
            <name>Null Island</name>
        </location_attributes>
        <party_attributes_default>
            <notes>Party attribute default notes.</notes>
        </party_attributes_default>
        <party_attributes_individual>
            <gender>f</gender>
            <homeowner>no</homeowner>
            <dob>2016-07-07</dob>
        </party_attributes_individual>
        <party_relationship_attributes>
            <notes>Party relationship notes.</notes>
        </party_relationship_attributes>
        <tenure_relationship_attributes>
            <notes>Tenure relationship notes.</notes>
        </tenure_relationship_attributes>
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </test_standard_questionnaire>'''.strip()

POLY_FORM = '''<?xml version=\'1.0\' ?>
    <test_standard_questionnaire
        id="test_standard_questionnaire" version="20160727122110">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <party_type>IN</party_type>
        <party_name>Peggy Carter</party_name>
        <location_geometry>40.6890612 -73.9925067 0.0 0.0;
        41.6890612 -73.9925067 0.0 0.0;41.6890612 -72.9925067 0.0 0.0;
        40.6890612 -72.9925067 0.0 0.0;40.6890612 -73.9925067 0.0 0.0;
        </location_geometry>
        <location_type>MI</location_type>
        <tenure_type>LH</tenure_type>
        <location_attributes>
            <name>Polygon</name>
        </location_attributes>
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </test_standard_questionnaire>'''.strip()

LINE_FORM = '''<?xml version=\'1.0\' ?>
    <test_standard_questionnaire
        id="test_standard_questionnaire" version="20160727122110">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <party_type>IN</party_type>
        <party_name>Buckey Barnes</party_name>
        <location_geometry>45.56342779158167 -122.67650283873081 0.0 0.0;
        45.56176327330353 -122.67669159919024 0.0 0.0;
        45.56151562182025 -122.67490658909082 0.0 0.0;
        45.563479432877415 -122.67494414001703 0.0 0.0;
        45.56176327330353 -122.67669159919024 0.0 0.0
        </location_geometry>
        <location_type>MI</location_type>
        <tenure_type>LH</tenure_type>
        <location_attributes>
            <name>Line</name>
        </location_attributes>
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </test_standard_questionnaire>'''.strip()

MISSING_SEMI_FORM = '''<?xml version=\'1.0\' ?>
    <test_standard_questionnaire
        id="test_standard_questionnaire" version="20160727122110">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <party_type>IN</party_type>
        <party_name>Stever Rogers</party_name>
        <location_choice>geotrace</location_choice>
        <location_geotrace>340.6890612 -373.9925067 0.0 0.0
        </location_geotrace>
        <location_type>MI</location_type>
        <tenure_type>LH</tenure_type>
        <location_attributes>
            <name>Missing Semi</name>
        </location_attributes>
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </test_standard_questionnaire>'''.strip()

GEOSHAPE_FORM = '''<?xml version=\'1.0\' ?>
    <test_standard_questionnaire_2
        id="test_standard_questionnaire_2" version="20160727122111">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <party_type>IN</party_type>
        <party_name>Natashia Romanoff</party_name>
        <location_choice>geoshape</location_choice>
        <location_geoshape>45.56342779158167 -122.67650283873081 0.0 0.0;
        45.56176327330353 -122.67669159919024 0.0 0.0;
        45.56151562182025 -122.67490658909082 0.0 0.0;
        45.563479432877415 -122.67494414001703 0.0 0.0;
        45.56176327330353 -122.67669159919024 0.0 0.0
        </location_geoshape>
        <location_type>MI</location_type>
        <tenure_type>LH</tenure_type>
        <location_attributes>
            <name>Geoshape</name>
        </location_attributes>
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </test_standard_questionnaire_2>'''.strip()

BAD_QUESTIONNAIRE = '''<?xml version=\'1.0\' ?>
    <tax_return id="tax_return" version="20160727122110">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <party_type>IN</party_type>
        <party_name>Scrooge McDuck</party_name>
        <location_geometry />
        <location_type>MI</location_type>
        <location_photo>test_image.png</location_photo>
        <party_photo />
        <tenure_type>LH</tenure_type>
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </tax_return>'''.strip()

BAD_LOCATION_FORM = '''<?xml version=\'1.0\' ?>
    <test_standard_questionnaire
        id="test_standard_questionnaire" version="20160727122110">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <party_type>IN</party_type>
        <party_name>Peggy Carter</party_name>
        <location_geometry />
        <location_thing>MI</location_thing>
        <tenure_type>LH</tenure_type>
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </test_standard_questionnaire>'''.strip()

BAD_PARTY_FORM = '''<?xml version=\'1.0\' ?>
    <test_standard_questionnaire
        id="test_standard_questionnaire" version="20160727122110">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <party_type>IN</party_type>
        <party_people>Peggy Carter</party_people>
        <location_geometry />
        <location_type>MI</location_type>
        <tenure_type>LH</tenure_type>
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </test_standard_questionnaire>'''.strip()

BAD_TENURE_FORM = '''<?xml version=\'1.0\' ?>
    <test_standard_questionnaire
        id="test_standard_questionnaire" version="20160727122110">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <party_type>IN</party_type>
        <party_name>Peggy Carter</party_name>
        <location_geometry />
        <location_type>MI</location_type>
        <tenure_thing>LH</tenure_thing>
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </test_standard_questionnaire>'''.strip()

BAD_RESOURCE_FORM = '''<?xml version=\'1.0\' ?>
    <test_standard_questionnaire_bad
        id="test_standard_questionnaire_bad" version="20160727122112">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <party_type>IN</party_type>
        <party_name>Peggy Carter</party_name>
        <bad_html>test_bad_resource.html</bad_html>
        <location_geometry />
        <location_type>MI</location_type>
        <tenure_type>LH</tenure_type>
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </test_standard_questionnaire_bad>'''.strip()

responses = {
    'form': FORM,
    'invalid_form': INVALID_FORM,
    'line_form': LINE_FORM,
    'poly_form': POLY_FORM,
    'missing_semi_form': MISSING_SEMI_FORM,
    'geoshape_form': GEOSHAPE_FORM,
    'bad_questionnaire': BAD_QUESTIONNAIRE,
    'bad_location_form': BAD_LOCATION_FORM,
    'bad_party_form': BAD_PARTY_FORM,
    'bad_tenure_form': BAD_TENURE_FORM,
    'bad_resource_form': BAD_RESOURCE_FORM,
}
