STANDARD = '''<?xml version=\'1.0\' ?>
    <t_questionnaire
        id="t_questionnaire" version="20160727122110">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <party_type>IN</party_type>
        <party_name>Bilbo Baggins</party_name>
        <location_geometry>40.6890612 -73.9925067 0.0 0.0;</location_geometry>
        <location_type>MI</location_type>
        <location_resource_photo>test_image_one.png</location_resource_photo>
        <party_resource_photo>test_image_two.png</party_resource_photo>
        <party_resource_audio>test_audio_one.mp3</party_resource_audio>
        <location_photo>test_image_one.png</location_photo>
        <party_photo>test_image_two.png</party_photo>
        <tenure_resource_photo>test_image_three.png</tenure_resource_photo>
        <tenure_type>LH</tenure_type>
        <location_attributes>
            <name>Middle Earth</name>
            <infrastructure>water food electricity</infrastructure>
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
    </t_questionnaire>'''.strip()

NOT_SANE = '''<?xml version=\'1.0\' ?>
    <t_questionnaire
        id="t_questionnaire" version="20160727122110">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <party_type>IN</party_type>
        <party_name>=Bilbo Baggins</party_name>
        <location_geometry>40.6890612 -73.9925067 0.0 0.0;</location_geometry>
        <location_type>MI</location_type>
        <location_resource_photo>test_image_one.png</location_resource_photo>
        <party_resource_photo>test_image_two.png</party_resource_photo>
        <party_resource_audio>test_audio_one.mp3</party_resource_audio>
        <location_photo>test_image_one.png</location_photo>
        <party_photo>test_image_two.png</party_photo>
        <tenure_resource_photo>test_image_three.png</tenure_resource_photo>
        <tenure_type>LH</tenure_type>
        <location_attributes>
            <name>Middle Earth</name>
            <infrastructure>water food electricity</infrastructure>
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
    </t_questionnaire>'''.strip()

POLY = '''<?xml version=\'1.0\' ?>
    <t_questionnaire
        id="t_questionnaire" version="20160727122110">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <party_type>IN</party_type>
        <party_name>Peggy Carter</party_name>
        <location_geometry>52.94499198165777 -8.038442619144917 0.0 0.0;
        52.943536322452495 -8.038954921066761 0.0 0.0;52.941551455741696
        -8.037515245378017 0.0 0.0;
        52.94318457288768 -8.034790456295013 0.0 0.0;52.94509582556425
        -8.03566887974739 0.0 0.0;
        52.943536322452495 -8.038954921066761 0.0 0.0;
        </location_geometry>
        <location_type>MI</location_type>
        <tenure_type>LH</tenure_type>
        <tenure_resource_audio>test_audio_one.mp3</tenure_resource_audio>
        <location_attributes>
            <name>Polygon</name>
        </location_attributes>
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </t_questionnaire>'''.strip()

LINE = '''<?xml version=\'1.0\' ?>
    <t_questionnaire
        id="t_questionnaire" version="20160727122110">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <party_type>IN</party_type>
        <party_name>Buckey Barnes</party_name>
        <location_geometry>52.94144813 -8.03473703 0.0 0.0;52.94134545
        -8.03589956 0.0 0.0;52.94124167 -8.03624506 0.0 0.0;52.94129824
        -8.03570223 0.0 0.0;
        </location_geometry>
        <location_type>MI</location_type>
        <tenure_type>LH</tenure_type>
        <location_attributes>
            <name>Line</name>
        </location_attributes>
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </t_questionnaire>'''.strip()

MISSING_SEMI = '''<?xml version=\'1.0\' ?>
    <t_questionnaire
        id="t_questionnaire" version="20160727122110">
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
    </t_questionnaire>'''.strip()

GEOTYPE_SELECT = '''<?xml version=\'1.0\' ?>
    <t_questionnaire_geotype_select
        id="t_questionnaire_geotype_select" version="20160727122111">
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
    </t_questionnaire_geotype_select>'''.strip()


GEOTRACE_AS_POLY = '''<?xml version=\'1.0\' ?>
    <t_questionnaire_geotype_select
        id="t_questionnaire_geotype_select" version="20160727122111">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <party_type>IN</party_type>
        <party_name>Natashia Romanoff</party_name>
        <location_choice>geotrace</location_choice>
        <location_geotrace>
        52.9414478 -8.034659 0.0 0.0;
        52.94134675 -8.0354197 0.0 0.0;
        52.94129841 -8.03517551 0.0 0.0;
        52.94142406 -8.03487897 0.0 0.0;
        52.9414478 -8.034659 0.0 0.0;
        </location_geotrace>
        <location_type>MI</location_type>
        <tenure_type>LH</tenure_type>
        <location_attributes>
            <name>geotrace_poly</name>
        </location_attributes>
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </t_questionnaire_geotype_select>'''.strip()

GEOTYPE_NEITHER = '''<?xml version=\'1.0\' ?>
    <t_questionnaire_geotype_select
        id="t_questionnaire_geotype_select" version="20160727122111">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <party_type>IN</party_type>
        <party_name>Natashia Romanoff</party_name>
        <location_choice>neither</location_choice>
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
    </t_questionnaire_geotype_select>'''.strip()

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

BAD_LOCATION = '''<?xml version=\'1.0\' ?>
    <t_questionnaire
        id="t_questionnaire" version="20160727122110">
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
    </t_questionnaire>'''.strip()

BAD_PARTY = '''<?xml version=\'1.0\' ?>
    <t_questionnaire
        id="t_questionnaire" version="20160727122110">
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
    </t_questionnaire>'''.strip()

BAD_TENURE = '''<?xml version=\'1.0\' ?>
    <t_questionnaire
        id="t_questionnaire" version="20160727122110">
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
    </t_questionnaire>'''.strip()

BAD_RESOURCE = '''<?xml version=\'1.0\' ?>
    <t_questionnaire_bad
        id="t_questionnaire_bad" version="20160727122112">
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
    </t_questionnaire_bad>'''.strip()

REPEAT_PARTY = '''<?xml version=\'1.0\' ?>
    <t_questionnaire_repeat_party
        id="t_questionnaire_repeat_party" version="20160727122113">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <location_geometry>40.6890612 -73.9925067 0.0 0.0;</location_geometry>
        <location_type>MI</location_type>
        <location_resource_audio>test_audio_one.mp3</location_resource_audio>
        <location_photo>test_image_one.png</location_photo>
        <location_attributes>
            <name>Middle Earth</name>
        </location_attributes>
        <party_repeat>
            <party_type>IN</party_type>
            <party_name>Bilbo Baggins</party_name>
            <party_photo>test_image_two.png</party_photo>
            <party_resource_photo>test_image_three.png</party_resource_photo>
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
            <tenure_type>LH</tenure_type>
            <tenure_relationship_attributes>
                <notes>Tenure relationship notes.</notes>
            </tenure_relationship_attributes>
            <tenure_resource_photo>test_image_four.png</tenure_resource_photo>
        </party_repeat>
        <party_repeat>
            <party_type>IN</party_type>
            <party_name>Samwise Gamgee</party_name>
            <party_photo>test_image_five.png</party_photo>
            <party_resource_photo />
            <party_attributes_default>
                <notes>Repeated party attribute default notes.</notes>
            </party_attributes_default>
            <party_attributes_individual>
                <gender>f</gender>
                <homeowner>no</homeowner>
                <dob>2016-07-07</dob>
            </party_attributes_individual>
            <party_relationship_attributes>
                <notes>Party relationship notes.</notes>
            </party_relationship_attributes>
            <tenure_type>LH</tenure_type>
            <tenure_relationship_attributes>
                <notes>Tenure relationship notes.</notes>
            </tenure_relationship_attributes>
            <tenure_resource_photo />
        </party_repeat>
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </t_questionnaire_repeat_party>'''.strip()

REPEAT_ONE_PARTY = '''<?xml version=\'1.0\' ?>
    <t_questionnaire_repeat_party
        id="t_questionnaire_repeat_party" version="20160727122113">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <location_geometry>40.6890612 -73.9925067 0.0 0.0;</location_geometry>
        <location_type>MI</location_type>
        <location_resource_audio>test_audio_one.mp3</location_resource_audio>
        <location_photo>test_image_one.png</location_photo>
        <location_attributes>
            <name>Middle Earth</name>
        </location_attributes>
        <party_repeat>
            <party_type>IN</party_type>
            <party_name>Bilbo Baggins</party_name>
            <party_photo>test_image_two.png</party_photo>
            <party_resource_photo>test_image_three.png</party_resource_photo>
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
            <tenure_type>LH</tenure_type>
            <tenure_relationship_attributes>
                <notes>Tenure relationship notes.</notes>
            </tenure_relationship_attributes>
            <tenure_resource_photo>test_image_four.png</tenure_resource_photo>
        </party_repeat>
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </t_questionnaire_repeat_party>'''.strip()

REPEAT_LOCATION = '''<?xml version=\'1.0\' ?>
    <t_questionnaire_repeat_location
        id="t_questionnaire_repeat_location"
        version="20160727122114">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <location_repeat>
            <location_geometry>40.6890612 -73.9925067 0.0 0.0;
            </location_geometry>
            <location_type>MI</location_type>
            <location_resource_audio>test_audio_one.mp3</location_resource_audio>
            <location_photo>test_image_one.png</location_photo>
            <location_attributes>
                <name>Middle Earth</name>
            </location_attributes>
            <tenure_type>CR</tenure_type>
            <tenure_relationship_attributes>
                <notes>Tenure relationship notes.</notes>
            </tenure_relationship_attributes>
            <tenure_resource_photo>test_image_two.png</tenure_resource_photo>
        </location_repeat>
        <location_repeat>
            <location_geometry>40.6890612 -73.9925067 0.0 0.0;
            </location_geometry>
            <location_type>CB</location_type>
            <location_resource_audio />
            <location_photo>test_image_three.png</location_photo>
            <location_attributes>
                <name>Middle Earth</name>
            </location_attributes>
            <tenure_type>LH</tenure_type>
            <tenure_relationship_attributes>
                <notes>Tenure relationship notes.</notes>
            </tenure_relationship_attributes>
            <tenure_resource_photo />
        </location_repeat>
        <party_type>IN</party_type>
        <party_name>Bilbo Baggins</party_name>
        <party_photo>test_image_four.png</party_photo>
        <party_resource_photo>test_image_five.png</party_resource_photo>
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
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </t_questionnaire_repeat_location>'''.strip()

REPEAT_ONE_LOCATION = '''<?xml version=\'1.0\' ?>
    <t_questionnaire_repeat_location
        id="t_questionnaire_repeat_location"
        version="20160727122114">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <location_repeat>
            <location_geometry>40.6890612 -73.9925067 0.0 0.0;
            </location_geometry>
            <location_type>MI</location_type>
            <location_resource_audio>test_audio_one.mp3</location_resource_audio>
            <location_photo>test_image_one.png</location_photo>
            <location_attributes>
                <name>Middle Earth</name>
            </location_attributes>
            <tenure_type>CR</tenure_type>
            <tenure_relationship_attributes>
                <notes>Tenure relationship notes.</notes>
            </tenure_relationship_attributes>
            <tenure_resource_photo>test_image_two.png</tenure_resource_photo>
        </location_repeat>
        <party_type>IN</party_type>
        <party_name>Bilbo Baggins</party_name>
        <party_photo>test_image_four.png</party_photo>
        <party_resource_photo>test_image_five.png</party_resource_photo>
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
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </t_questionnaire_repeat_location>'''.strip()

REPEAT_MINUS_TENURE = '''<?xml version=\'1.0\' ?>
    <t_questionnaire_repeat_minus_tenure
        id="t_questionnaire_repeat_minus_tenure"
        version="20160727122115">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <location_repeat>
            <location_geometry>40.6890612 -73.9925067 0.0 0.0;
            </location_geometry>
            <location_type>MI</location_type>
            <location_resource_audio>test_audio_one.mp3</location_resource_audio>
            <location_photo>test_image_one.png</location_photo>
            <location_attributes>
                <name>Middle Earth</name>
            </location_attributes>
        </location_repeat>
        <location_repeat>
            <location_geometry>40.6890612 -73.9925067 0.0 0.0;
            </location_geometry>
            <location_type>CB</location_type>
            <location_resource_audio />
            <location_photo>test_image_three.png</location_photo>
            <location_attributes>
                <name>Middle Earth</name>
            </location_attributes>
        </location_repeat>
        <tenure_type>CR</tenure_type>
        <tenure_relationship_attributes>
            <notes>Tenure relationship notes.</notes>
        </tenure_relationship_attributes>
        <tenure_resource_photo>test_image_two.png</tenure_resource_photo>
        <party_type>IN</party_type>
        <party_name>Bilbo Baggins</party_name>
        <party_photo>test_image_four.png</party_photo>
        <party_resource_photo>test_image_five.png</party_resource_photo>
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
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </t_questionnaire_repeat_minus_tenure>'''.strip()

REPEAT_PARTY_MINUS_TENURE = '''<?xml version=\'1.0\' ?>
    <t_questionnaire_repeat_party_minus_tenure
        id="t_questionnaire_repeat_party_minus_tenure"
        version="20160727122116">
        <start>2016-07-07T16:38:20.310-04</start>
        <end>2016-07-07T16:39:23.673-04</end>
        <today>2016-07-07</today>
        <deviceid>00:bb:3a:44:d0:fb</deviceid>
        <title />
        <location_geometry>40.6890612 -73.9925067 0.0 0.0;
        </location_geometry>
        <location_type>MI</location_type>
        <location_resource_audio>test_audio_one.mp3</location_resource_audio>
        <location_photo>test_image_one.png</location_photo>
        <location_attributes>
            <name>Middle Earth</name>
        </location_attributes>
        <tenure_type>CR</tenure_type>
        <tenure_relationship_attributes>
            <notes>Tenure relationship notes.</notes>
        </tenure_relationship_attributes>
        <tenure_resource_photo>test_image_two.png</tenure_resource_photo>
        <party_repeat>
            <party_type>IN</party_type>
            <party_name>Bilbo Baggins</party_name>
            <party_photo>test_image_three.png</party_photo>
            <party_resource_photo>test_image_four.png</party_resource_photo>
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
        </party_repeat>
        <party_repeat>
            <party_type>IN</party_type>
            <party_name>Samwise Gamgee</party_name>
            <party_photo>test_image_five.png</party_photo>
            <party_resource_photo />
            <party_attributes_default>
                <notes>Repeated party attribute default notes.</notes>
            </party_attributes_default>
            <party_attributes_individual>
                <gender>f</gender>
                <homeowner>no</homeowner>
                <dob>2016-07-07</dob>
            </party_attributes_individual>
            <party_relationship_attributes>
                <notes>Party relationship notes.</notes>
            </party_relationship_attributes>
            <tenure_type>LH</tenure_type>
            <tenure_relationship_attributes>
                <notes>Tenure relationship notes.</notes>
            </tenure_relationship_attributes>
            <tenure_resource_photo />
        </party_repeat>
        <meta>
            <instanceID>uuid:b3f225d3-0fac-4a0b-80c7-60e6db4cc0ad</instanceID>
        </meta>
    </t_questionnaire_repeat_party_minus_tenure>'''.strip()

responses = {
    'submission': STANDARD,
    'submission_not_sane': NOT_SANE,
    'submission_line': LINE,
    'submission_poly': POLY,
    'submission_geotrace_as_poly': GEOTRACE_AS_POLY,
    'submission_missing_semi': MISSING_SEMI,
    'submission_geotype_select': GEOTYPE_SELECT,
    'submission_geotype_neither': GEOTYPE_NEITHER,
    'submission_bad_questionnaire': BAD_QUESTIONNAIRE,
    'submission_bad_location': BAD_LOCATION,
    'submission_bad_party': BAD_PARTY,
    'submission_bad_tenure': BAD_TENURE,
    'submission_bad_resource': BAD_RESOURCE,
    'submission_party_repeat': REPEAT_PARTY,
    'submission_party_one_repeat': REPEAT_ONE_PARTY,
    'submission_location_repeat': REPEAT_LOCATION,
    'submission_location_one_repeat': REPEAT_ONE_LOCATION,
    'submission_repeat_minus_tenure': REPEAT_MINUS_TENURE,
    'submission_repeat_party_minus_tenure': REPEAT_PARTY_MINUS_TENURE,
}
