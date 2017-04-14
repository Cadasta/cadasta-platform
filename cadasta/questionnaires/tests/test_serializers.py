import pytest
from django.db import transaction
from django.test import TestCase
from rest_framework.serializers import ValidationError
from jsonattrs.models import Attribute
from organization.tests.factories import ProjectFactory
from questionnaires.exceptions import InvalidQuestionnaire
from core.tests.utils.files import make_dirs  # noqa
from core.tests.utils.cases import FileStorageTestCase, UserTestCase

from . import factories
from .. import serializers
from ..models import Questionnaire, QuestionOption, QuestionGroup


@pytest.mark.usefixtures('make_dirs')
class QuestionnaireSerializerTest(UserTestCase, FileStorageTestCase, TestCase):
    def test_deserialize(self):
        form = self.get_form('xls-form')

        project = ProjectFactory.create()

        serializer = serializers.QuestionnaireSerializer(
            data={'xls_form': form},
            context={'project': project}
        )
        assert serializer.is_valid(raise_exception=True) is True
        serializer.save()

        assert Questionnaire.objects.count() == 1
        questionnaire = Questionnaire.objects.first()

        assert questionnaire.id_string == 'question_types'
        assert questionnaire.filename == 'xls-form'
        assert questionnaire.title == 'Question types'

        assert serializer.data['id'] == questionnaire.id
        assert serializer.data['filename'] == questionnaire.filename
        assert serializer.data['title'] == questionnaire.title
        assert serializer.data['id_string'] == questionnaire.id_string
        assert serializer.data['xls_form'] == questionnaire.xls_form.url
        assert serializer.data['version'] == questionnaire.version
        assert len(serializer.data['questions']) == 1

    def test_deserialize_invalid_form(self):
        form = self.get_form('xls-form-invalid')

        project = ProjectFactory.create()

        serializer = serializers.QuestionnaireSerializer(
            data={'xls_form': form},
            context={'project': project}
        )
        assert serializer.is_valid(raise_exception=True) is True
        with pytest.raises(InvalidQuestionnaire):
            serializer.save()
        assert Questionnaire.objects.count() == 0

    def test_deserialize_json(self):
        data = {
            'title': 'yx8sqx6488wbc4yysnkrbnfq',
            'id_string': 'yx8sqx6488wbc4yysnkrbnfq',
            'default_language': 'en',
            'questions': [{
                'name': "start",
                'label': 'Label',
                'type': "ST",
                'required': False,
                'constraint': None,
                'index': 0
            }, {
                'name': "end",
                'label': 'Label',
                'type': "EN",
                'index': 1
            }]
        }
        project = ProjectFactory.create()

        serializer = serializers.QuestionnaireSerializer(
            data=data,
            context={'project': project}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        assert Questionnaire.objects.count() == 1
        questionnaire = Questionnaire.objects.first()
        assert project.current_questionnaire == questionnaire.id
        assert questionnaire.questions.count() == 2

    def test_invalid_deserialize_json(self):
        data = {
            'id_string': 'yx8sqx6488wbc4yysnkrbnfq',
            'default_language': 'en',
            'questions': [{
                'name': "start",
                'label': 'Label',
                'type': "ST",
                'required': False,
                'constraint': None,
                'index': 0
            }, {
                'name': "end",
                'label': 'Label',
                'type': "EN",
                'index': 1
            }]
        }
        project = ProjectFactory.create()

        serializer = serializers.QuestionnaireSerializer(
            data=data,
            context={'project': project}
        )
        assert serializer.is_valid() is False
        assert serializer.errors == {'title': ['This field is required.']}

        with pytest.raises(ValidationError):
            assert serializer.is_valid(raise_exception=True)

    def test_serialize(self):
        questionnaire = factories.QuestionnaireFactory()

        factories.QuestionFactory.create(questionnaire=questionnaire,
                                         question_group=None)
        group = factories.QuestionGroupFactory.create(
            questionnaire=questionnaire,
            question_group=None)
        factories.QuestionGroupFactory.create(questionnaire=questionnaire,
                                              question_group=group)
        factories.QuestionFactory.create(questionnaire=questionnaire,
                                         question_group=group)

        serializer = serializers.QuestionnaireSerializer(questionnaire)

        assert serializer.data['id'] == questionnaire.id
        assert serializer.data['filename'] == questionnaire.filename
        assert serializer.data['title'] == questionnaire.title
        assert serializer.data['id_string'] == questionnaire.id_string
        assert serializer.data['xls_form'] == questionnaire.xls_form.url
        assert serializer.data['version'] == questionnaire.version
        assert 'project' not in serializer.data

        assert len(serializer.data['questions']) == 1
        assert len(serializer.data['question_groups']) == 1
        assert len(serializer.data['question_groups'][0]['questions']) == 1
        assert (
            len(serializer.data['question_groups'][0]['question_groups']) == 1)

    def test_rollback_on_duplicate_group_without_relevant(self):
        data = {
            'id_string': 'yx8sqx6488wbc4yysnkrbnfq',
            'title': 'wa6hrqr4e4vcf49q6kxjc443',
            'default_language': 'en',
            'question_groups': [{
                'label': 'A group',
                'name': 'party_attributes_individual',
                'index': 0,
                'type': 'group',
                'questions': [{
                    'name': "start",
                    'label': 'Start',
                    'type': "TX",
                    'index': 0
                }]
            }, {
                'label': 'Another group',
                'name': 'party_attributes_default',
                'index': 1,
                'type': 'group',
                'questions': [{
                    'name': "end",
                    'label': 'End',
                    'type': "TX",
                    'index': 1
                }]
            }]
        }
        project = ProjectFactory.create()

        serializer = serializers.QuestionnaireSerializer(
            data=data,
            context={'project': project}
        )
        assert serializer.is_valid(raise_exception=True) is True
        with pytest.raises(InvalidQuestionnaire):
            serializer.save()

        assert Questionnaire.objects.count() == 0
        assert QuestionGroup.objects.count() == 0
        assert Attribute.objects.count() == 0

    def test_huge(self):
        data = {
            "filename": "wa6hrqr4e4vcf49q6kxjc443",
            "title": "wa6hrqr4e4vcf49q6kxjc443",
            "id_string": "wa6hrqr4e4vcf49q6kxjc443",
            "default_language": "en",
            "questions": [
                {
                    "id": "f44zrz6ch4mj8xcvhb55343c",
                    "name": "start",
                    "label": "Label",
                    "type": "ST",
                    "required": False,
                    "constraint": None,
                    "default": None,
                    "hint": None,
                    "relevant": None,
                    "index": 0
                },
                {
                    "id": "uigb9zd9zgmhjewvaf92awru",
                    "name": "end",
                    "label": "Label",
                    "type": "EN",
                    "required": False,
                    "constraint": None,
                    "default": None,
                    "hint": None,
                    "relevant": None,
                    "index": 1
                },
                {
                    "id": "rw7mt32858cu2w5urbf9z3a4",
                    "name": "today",
                    "label": "Label",
                    "type": "TD",
                    "required": False,
                    "constraint": None,
                    "default": None,
                    "hint": None,
                    "relevant": None,
                    "index": 2
                },
                {
                    "id": "sgz4peaw5buq7pyjv87fuv6u",
                    "name": "deviceid",
                    "label": "Label",
                    "type": "DI",
                    "required": False,
                    "constraint": None,
                    "default": None,
                    "hint": None,
                    "relevant": None,
                    "index": 3
                },
                {
                    "id": "h9r973qgscumzh6emkx9jnba",
                    "name": "title",
                    "label": "Cadasta Platform - UAT Survey",
                    "type": "NO",
                    "required": False,
                    "constraint": None,
                    "default": None,
                    "hint": None,
                    "relevant": None,
                    "index": 4
                },
                {
                    "id": "hq5tvivqwnqttaiudk7zz2fu",
                    "name": "party_type",
                    "label": "Party Classification",
                    "type": "S1",
                    "required": True,
                    "constraint": None,
                    "default": None,
                    "hint": None,
                    "relevant": None,
                    "index": 5,
                    "options": [
                        {
                            "id": "tr8gc2xanrqzq3idfrysk2cn",
                            "name": "GR",
                            "label": "Group",
                            "index": 1
                        },
                        {
                            "id": "h5px4fgbzh92bx7mbxjcqwpp",
                            "name": "IN",
                            "label": "Individual",
                            "index": 2
                        },
                        {
                            "id": "ddhfbhex77fdmgdnqbuqytvy",
                            "name": "CO",
                            "label": "Corporation",
                            "index": 3
                        }
                    ]
                },
                {
                    "id": "7snc5dvma8a42xzkhnsgjpvq",
                    "name": "party_name",
                    "label": "Party Name",
                    "type": "TX",
                    "required": True,
                    "constraint": None,
                    "default": None,
                    "hint": None,
                    "relevant": None,
                    "index": 6
                },
                {
                    "id": "w4eb66p8c2ctshdkachc26zd",
                    "name": "location_geometry",
                    "label": "Location of Parcel",
                    "type": "GT",
                    "required": False,
                    "constraint": None,
                    "default": None,
                    "hint": None,
                    "relevant": None,
                    "index": 7
                },
                {
                    "id": "vks2dqjktf2t2in76jv38rdj",
                    "name": "location_type",
                    "label": "What is the land feature?",
                    "type": "S1",
                    "required": True,
                    "constraint": None,
                    "default": None,
                    "hint": None,
                    "relevant": None,
                    "index": 8,
                    "options": [
                        {
                            "id": "xq9eumfmxe2h3mk4cibx6az2",
                            "name": "PA",
                            "label": "Parcel",
                            "index": 1
                        },
                        {
                            "id": "39wpggcaw8bhknj6uden4y52",
                            "name": "CB",
                            "label": "Community Boundary",
                            "index": 2
                        },
                        {
                            "id": "vtag4awngt8qqkfuy6r2tm55",
                            "name": "BU",
                            "label": "Building",
                            "index": 3
                        },
                        {
                            "id": "8s59tvh4qzvuphwuq7h63thf",
                            "name": "AP",
                            "label": "Apartment",
                            "index": 4
                        },
                        {
                            "id": "5rvig9t4mpbzgkuwtiegzf82",
                            "name": "PX",
                            "label": "Project Extent",
                            "index": 5
                        },
                        {
                            "id": "srzjrbmfwqk7s45mh83mj6tf",
                            "name": "RW",
                            "label": "Right-of-way",
                            "index": 6
                        },
                        {
                            "id": "39afz6h95zs4mn8pup85gzsb",
                            "name": "NP",
                            "label": "National Park Boundary",
                            "index": 7
                        },
                        {
                            "id": "bpnahr4a57yqvrzn4kjeygei",
                            "name": "MI",
                            "label": "Miscellaneous",
                            "index": 8
                        }
                    ]
                },
                {
                    "id": "kzen2egxny4jhrcwcngdxuku",
                    "name": "location_photo",
                    "label": "Photo of Parcel?",
                    "type": "PH",
                    "required": False,
                    "constraint": None,
                    "default": None,
                    "hint": None,
                    "relevant": None,
                    "index": 9
                },
                {
                    "id": "v4ydy2ihvd2xfdhiqhwhgfed",
                    "name": "party_photo",
                    "label": "Photo of Party?",
                    "type": "PH",
                    "required": False,
                    "constraint": None,
                    "default": None,
                    "hint": None,
                    "relevant": None,
                    "index": 10
                },
                {
                    "id": "x5x4ts8ujbhpkk92s53icrx7",
                    "name": "tenure_resource_photo",
                    "label": "Photo of Tenure?",
                    "type": "PH",
                    "required": False,
                    "constraint": None,
                    "default": None,
                    "hint": None,
                    "relevant": None,
                    "index": 11
                },
                {
                    "id": "merrppduxyk6y3fja74pym7p",
                    "name": "tenure_type",
                    "label": "What is the social tenure type?",
                    "type": "S1",
                    "required": True,
                    "constraint": None,
                    "default": None,
                    "hint": None,
                    "relevant": None,
                    "index": 12,
                    "options": [
                        {
                            "id": "ua22mni8hszcxjjr6brnw25k",
                            "name": "AL",
                            "label": "All Types",
                            "index": 1
                        },
                        {
                            "id": "tff64xg9mvrhq9gsgzqvt28i",
                            "name": "CR",
                            "label": "Carbon Rights",
                            "index": 2
                        },
                        {
                            "id": "w8u9a2szv5enwsj6d7rx8cgf",
                            "name": "CO",
                            "label": "Concessionary Rights",
                            "index": 3
                        },
                        {
                            "id": "qjjzerwc64mhfxnq2izuh6tc",
                            "name": "CU",
                            "label": "Customary Rights",
                            "index": 4
                        },
                        {
                            "id": "5igsk5i2ratwcnxsfqjv6k9r",
                            "name": "EA",
                            "label": "Easement",
                            "index": 5
                        },
                        {
                            "id": "q5pt35uw3cngnqb9hn5arzuv",
                            "name": "ES",
                            "label": "Equitable Servitude",
                            "index": 6
                        },
                        {
                            "id": "ugisaw4bzxvtibubuaqv7agw",
                            "name": "FH",
                            "label": "Freehold",
                            "index": 7
                        },
                        {
                            "id": "jmz9uk96d3nxjm9m9bhmi3uk",
                            "name": "GR",
                            "label": "Grazing Rights",
                            "index": 8
                        },
                        {
                            "id": "63784su22n8g5mapuxtk22m2",
                            "name": "HR",
                            "label": "Hunting/Fishing/Harvest Rights",
                            "index": 9
                        },
                        {
                            "id": "g3qneyqttiyfp8n2e5pmyu4f",
                            "name": "IN",
                            "label": "Indigenous Land Rights",
                            "index": 10
                        },
                        {
                            "id": "7gentkaf9ns2x5xmcx29y8h2",
                            "name": "JT",
                            "label": "Joint Tenancy",
                            "index": 11
                        },
                        {
                            "id": "xtuzg83nscxkugxb6tmtc3hi",
                            "name": "LH",
                            "label": "Leasehold",
                            "index": 12
                        },
                        {
                            "id": "gd8ev83ha4y8v7sin5umrcc8",
                            "name": "LL",
                            "label": "Longterm leasehold",
                            "index": 13
                        },
                        {
                            "id": "qfs3kuajvadp5kwsuwayfb7m",
                            "name": "MR",
                            "label": "Mineral Rights",
                            "index": 14
                        },
                        {
                            "id": "nev97vg7t3uqrxhvcj7pkhws",
                            "name": "OC",
                            "label": "Occupancy (No Documented Rights)",
                            "index": 15
                        },
                        {
                            "id": "vjuz3hygccugyqmiijrkxygd",
                            "name": "TN",
                            "label": "Tenancy (Documented Sub-lease)",
                            "index": 16
                        },
                        {
                            "id": "qpkgwr6pxg3v57ibc5q39hgy",
                            "name": "TC",
                            "label": "Tenancy in Common",
                            "index": 17
                        },
                        {
                            "id": "kcurf4gv86rn9c3m24wzvwma",
                            "name": "UC",
                            "label": "Undivided Co-ownership",
                            "index": 18
                        },
                        {
                            "id": "36x2m7j94gc3j6pc6rvz7cuu",
                            "name": "WR",
                            "label": "Water Rights",
                            "index": 19
                        }
                    ]
                }
            ],
            "question_groups": [
                {
                    "id": "xnbj4kdr66w8k478f6cdta3n",
                    "name": "meta",
                    "label": "Label",
                    "type": 'group',
                    "index": 13,
                    "questions": [
                        {
                            "id": "8v5znbuyvtyinsdd96ytyrui",
                            "name": "instanceID",
                            "label": "Label",
                            "type": "CA",
                            "required": False,
                            "constraint": None,
                            "default": None,
                            "hint": None,
                            "relevant": None,
                            "index": 0
                        }
                    ]
                },
                {
                    "id": "9z6k336q7t8ws6qvf39akvym",
                    "name": "tenure_relationship_attributes",
                    "label": "Tenure relationship attributes",
                    "type": 'group',
                    "index": 14,
                    "questions": [
                        {
                            "id": "mprrfpk5cyg69f9tr7jvv742",
                            "name": "notes",
                            "label": "Notes",
                            "type": "TX",
                            "required": False,
                            "constraint": None,
                            "default": None,
                            "hint": None,
                            "relevant": None,
                            "index": 0
                        }
                    ]
                },
                {
                    "id": "48gdce8vrqfsw6ikpr77p5u5",
                    "name": "party_relationship_attributes",
                    "label": "Party relationship attributes",
                    "type": 'group',
                    "index": 15,
                    "questions": [
                        {
                            "id": "njemw8e6n2squqghiqgx8a7b",
                            "name": "notes",
                            "label": "Notes",
                            "type": "TX",
                            "required": False,
                            "constraint": None,
                            "default": None,
                            "hint": None,
                            "relevant": None,
                            "index": 0
                        }
                    ]
                },
                {
                    "id": "n2eg65xw5mtby8peae38mcb6",
                    "name": "party_attributes_group",
                    "label": "Group Party Attributes",
                    "type": 'group',
                    "relevant": "${party_type}='GR'",
                    "index": 16,
                    "questions": [
                        {
                            "id": "xta42t6ye53ujetniebknytw",
                            "name": "number_of_members",
                            "label": "Number of Members",
                            "type": "IN",
                            "required": False,
                            "constraint": None,
                            "default": None,
                            "hint": None,
                            "relevant": None,
                            "index": 0
                        },
                        {
                            "id": "jzy45gy539k7yfffz8h4vs7g",
                            "name": "date_formed",
                            "label": "Date Group Formed",
                            "type": "DA",
                            "required": False,
                            "constraint": None,
                            "default": None,
                            "hint": None,
                            "relevant": None,
                            "index": 1
                        }
                    ]
                },
                {
                    "id": "fwfbg2tc4ffbw4qnnmb46bzz",
                    "name": "party_attributes_individual",
                    "label": "Individual Party Attributes",
                    "type": 'group',
                    "relevant": "${party_type}='IN'",
                    "index": 17,
                    "questions": [
                        {
                            "id": "ph3xrdtxkcwacqavg8k8rj3v",
                            "name": "gender",
                            "label": "Gender",
                            "type": "S1",
                            "required": False,
                            "constraint": None,
                            "default": "f",
                            "hint": None,
                            "relevant": None,
                            "index": 0,
                            "options": [
                                {
                                    "id": "d465rbsz27bdvk9qtsrpivva",
                                    "name": "m",
                                    "label": "Male",
                                    "index": 1
                                },
                                {
                                    "id": "trhdqh9jzszw75ybtgsiej7y",
                                    "name": "f",
                                    "label": "Female",
                                    "index": 2
                                }
                            ]
                        },
                        {
                            "id": "jwugjuavpc9teep64bzk97s8",
                            "name": "homeowner",
                            "label": "Homeowner",
                            "type": "S1",
                            "required": False,
                            "constraint": None,
                            "default": "no",
                            "hint": "Is homeowner",
                            "relevant": None,
                            "index": 1,
                            "options": [
                                {
                                    "id": "i9mveb9cyiq5e2iszadgvx3p",
                                    "name": "yes",
                                    "label": "Yes",
                                    "index": 1
                                },
                                {
                                    "id": "ubkvrbdfc4zavgkg7my4stbc",
                                    "name": "no",
                                    "label": "No",
                                    "index": 2
                                }
                            ]
                        },
                        {
                            "id": "br2uuzpfty43dp92z5wj4dyk",
                            "name": "dob",
                            "label": "Date of Birth",
                            "type": "DA",
                            "required": False,
                            "constraint": None,
                            "default": None,
                            "hint": None,
                            "relevant": None,
                            "index": 2
                        }
                    ]
                },
                {
                    "id": "7678k4ixg2idpptda46fh5f8",
                    "name": "party_attributes_default",
                    "label": "Default Party Attributes",
                    "type": 'group',
                    "index": 18,
                    "questions": [
                        {
                            "id": "kw8t69w57aaw2jbuy72ky8bs",
                            "name": "notes",
                            "label": "Notes",
                            "type": "TX",
                            "required": False,
                            "constraint": None,
                            "default": None,
                            "hint": None,
                            "relevant": None,
                            "index": 0
                        }
                    ]
                },
                {
                    "id": "iapqx3jrcx8vmzp73r465d3a",
                    "name": "location_attributes",
                    "label": "Location Attributes",
                    "type": 'group',
                    "index": 19,
                    "questions": [
                        {
                            "id": "bj7z2hz3jnz8c76pcwks4v2y",
                            "name": "name",
                            "label": "Name of Location",
                            "type": "TX",
                            "required": False,
                            "constraint": None,
                            "default": None,
                            "hint": None,
                            "relevant": None,
                            "index": 0
                        },
                        {
                            "id": "36s3imu4h47cps2m64ddcf8h",
                            "name": "quality",
                            "label": "Spatial Unit Quality",
                            "type": "S1",
                            "required": False,
                            "constraint": None,
                            "default": "none",
                            "hint": "Quality of parcel geometry",
                            "relevant": None,
                            "index": 1,
                            "options": [
                                {
                                    "id": "sa8wd8hx8ipz9r8v6qznh6d9",
                                    "name": "none",
                                    "label": "No data",
                                    "index": 1
                                },
                                {
                                    "id": "525szguxtzqnamg8zh9dcw3m",
                                    "name": "text",
                                    "label": "Textual",
                                    "index": 2
                                },
                                {
                                    "id": "fhjrs9igzvp8fbqgbh76hq8i",
                                    "name": "point",
                                    "label": "Point data",
                                    "index": 3
                                },
                                {
                                    "id": "rea3pvsrmzwrifbu4b6meekw",
                                    "name": "polygon_low",
                                    "label": "Low quality polygon",
                                    "index": 4
                                },
                                {
                                    "id": "yfc9qwrgkfcv5kabq83iyz2r",
                                    "name": "polygon_high",
                                    "label": "High quality polygon",
                                    "index": 5
                                }
                            ]
                        },
                        {
                            "id": "mnstx4zzfz4dxyjyxhuqskam",
                            "name": "acquired_how",
                            "label": "How was this location acquired?",
                            "type": "SM",
                            "required": False,
                            "constraint": None,
                            "default": "OT",
                            "hint": None,
                            "relevant": None,
                            "index": 2,
                            "options": [
                                {
                                    "id": "efcuuw578hu2d922sgwvwvmg",
                                    "name": "CS",
                                    "label": "Contractual Share Crop",
                                    "index": 1
                                },
                                {
                                    "id": "rv7xrxq5tsfhpqyesbsju5xr",
                                    "name": "CA",
                                    "label": "Customary Arrangement",
                                    "index": 2
                                },
                                {
                                    "id": "qatxiebhrf27544i2cp4cs92",
                                    "name": "GF",
                                    "label": "Gift",
                                    "index": 3
                                },
                                {
                                    "id": "7hpqfrnyujjt54kca7u5bn4h",
                                    "name": "HS",
                                    "label": "Homestead",
                                    "index": 4
                                },
                                {
                                    "id": "fm64jhr5ywgvadi96t9pmb3x",
                                    "name": "IO",
                                    "label": "Informal Occupant",
                                    "index": 5
                                },
                                {
                                    "id": "ec3jvzg9fri9i6pz953y4vzx",
                                    "name": "IN",
                                    "label": "Inheritance",
                                    "index": 6
                                },
                                {
                                    "id": "4emhecd6zyneykp9xhfcbft9",
                                    "name": "LH",
                                    "label": "Leasehold",
                                    "index": 7
                                },
                                {
                                    "id": "725eq8p9z6axvi9nxr54dk9h",
                                    "name": "PF",
                                    "label": "Purchased Freehold",
                                    "index": 8
                                },
                                {
                                    "id": "sfpdbu7p7qz84ph9hpkaatc5",
                                    "name": "RN",
                                    "label": "Rental",
                                    "index": 9
                                },
                                {
                                    "id": "txay4h5ps2gt76xkb3higwme",
                                    "name": "OT",
                                    "label": "Other",
                                    "index": 10
                                }
                            ]
                        },
                        {
                            "id": "rzyfu9k84avfuvvh9afr87ry",
                            "name": "acquired_when",
                            "label": "When was this location acquired?",
                            "type": "DA",
                            "required": False,
                            "constraint": None,
                            "default": "none",
                            "hint": None,
                            "relevant": None,
                            "index": 3
                        },
                        {
                            "id": "ppckgucjmvt8xtg8tykifvm6",
                            "name": "notes",
                            "label": "Notes",
                            "type": "TX",
                            "required": False,
                            "constraint": None,
                            "default": None,
                            "hint": "Additional Notes",
                            "relevant": None,
                            "index": 4
                        }
                    ]
                }
            ]
        }
        project = ProjectFactory.create()

        serializer = serializers.QuestionnaireSerializer(
            data=data,
            context={'project': project}
        )
        assert serializer.is_valid(raise_exception=True) is True
        serializer.save()

        assert Questionnaire.objects.count() == 1
        questionnaire = Questionnaire.objects.first()
        assert questionnaire.questions.count() == 27
        assert questionnaire.question_groups.count() == 7
        assert Attribute.objects.count() == 13


class QuestionGroupSerializerTest(UserTestCase, TestCase):
    def test_serialize(self):
        questionnaire = factories.QuestionnaireFactory()
        question_group = factories.QuestionGroupFactory.create(
            questionnaire=questionnaire)
        factories.QuestionFactory.create_batch(
            2,
            questionnaire=questionnaire,
            question_group=question_group
        )
        not_in = factories.QuestionFactory.create(
            questionnaire=questionnaire
        )
        factories.QuestionGroupFactory.create_batch(
            2,
            questionnaire=questionnaire,
            question_group=question_group
        )

        question_group.refresh_from_db()
        serializer = serializers.QuestionGroupSerializer(question_group)
        assert serializer.data['id'] == question_group.id
        assert serializer.data['name'] == question_group.name
        assert serializer.data['label'] == question_group.label
        assert serializer.data['type'] == question_group.type
        assert len(serializer.data['questions']) == 2
        assert len(serializer.data['question_groups']) == 2
        assert all(g['name'] for g in serializer.data['question_groups'])
        assert not_in.id not in [q['id'] for q in serializer.data['questions']]
        assert 'questionnaire' not in serializer.data

    def test_serialize_mulitple_lang(self):
        questionnaire = factories.QuestionnaireFactory()
        question_group = factories.QuestionGroupFactory.create(
            questionnaire=questionnaire,
            label={'en': 'Group', 'de': 'Gruppe'})
        factories.QuestionFactory.create_batch(
            2,
            questionnaire=questionnaire,
            question_group=question_group
        )
        not_in = factories.QuestionFactory.create(
            questionnaire=questionnaire
        )
        factories.QuestionGroupFactory.create_batch(
            2,
            questionnaire=questionnaire,
            question_group=question_group
        )

        question_group.refresh_from_db()
        serializer = serializers.QuestionGroupSerializer(question_group)
        assert serializer.data['id'] == question_group.id
        assert serializer.data['name'] == question_group.name
        assert serializer.data['label'] == {'en': 'Group', 'de': 'Gruppe'}
        assert serializer.data['type'] == question_group.type
        assert len(serializer.data['questions']) == 2
        assert len(serializer.data['question_groups']) == 2
        assert all(g['name'] for g in serializer.data['question_groups'])
        assert not_in.id not in [q['id'] for q in serializer.data['questions']]
        assert 'questionnaire' not in serializer.data

    def test_create_group(self):
        questionnaire = factories.QuestionnaireFactory.create()
        data = {
            'label': 'A question',
            'name': 'question'
        }
        serializer = serializers.QuestionGroupSerializer(
            data=data,
            context={'questionnaire_id': questionnaire.id,
                     'project': questionnaire.project})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        assert questionnaire.question_groups.count() == 1
        question = questionnaire.question_groups.first()
        assert question.name == data['name']
        assert question.label == data['label']

    def test_create_nested_group(self):
        questionnaire = factories.QuestionnaireFactory.create()
        data = {
            'label': 'A question group',
            'name': 'question_group',
            'question_groups': [{
                'label': 'Another question group',
                'name': 'group_2',
            }]
        }
        serializer = serializers.QuestionGroupSerializer(
            data=data,
            context={'questionnaire_id': questionnaire.id,
                     'project': questionnaire.project})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        assert questionnaire.question_groups.count() == 2
        question_group = questionnaire.question_groups.get(
            name='question_group')
        assert question_group.name == data['name']
        assert question_group.label == data['label']
        assert question_group.question_groups.count() == 1
        nested_group = question_group.question_groups.first()
        assert nested_group.question_groups.count() == 0

    def test_duplicate_group_with_relevant(self):
        questionnaire = factories.QuestionnaireFactory.create()
        data = [{
                    'label': 'A group',
                    'name': 'party_attributes_individual',
                    "relevant": "${party_type}='IN'",
                    'questions': [{
                        'name': "start",
                        'label': 'Start',
                        'type': "TX",
                        'index': 0
                    }]
                }, {
                    'label': 'Another group',
                    'name': 'party_attributes_default',
                    'questions': [{
                        'name': "end",
                        'label': 'End',
                        'type': "TX",
                        'index': 1
                    }]
                }]
        serializer = serializers.QuestionGroupSerializer(
            data=data,
            many=True,
            context={'questionnaire_id': questionnaire.id,
                     'project': questionnaire.project,
                     'default_language': 'en'})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        assert questionnaire.question_groups.count() == 2

    def test_duplicate_group_without_relevant(self):
        questionnaire = factories.QuestionnaireFactory.create()
        data = [{
                    'label': 'A group',
                    'name': 'party_attributes_individual',
                    'questions': [{
                        'name': "start",
                        'label': 'Start',
                        'type': "TX",
                        'index': 0
                    }]
                }, {
                    'label': 'Another group',
                    'name': 'party_attributes_default',
                    'questions': [{
                        'name': "end",
                        'label': 'End',
                        'type': "TX",
                        'index': 1
                    }]
                }]
        serializer = serializers.QuestionGroupSerializer(
            data=data,
            many=True,
            context={'questionnaire_id': questionnaire.id,
                     'project': questionnaire.project,
                     'default_language': 'en'})
        serializer.is_valid(raise_exception=True)
        with pytest.raises(InvalidQuestionnaire):
            with transaction.atomic():
                serializer.save()
        assert questionnaire.question_groups.count() == 0

    def test_bulk_create_group(self):
        questionnaire = factories.QuestionnaireFactory.create()
        data = [{
                    'label': 'A group',
                    'name': 'group',
                    'questions': [{
                        'name': "start",
                        'label': 'Start',
                        'type': "ST",
                    }]
                }, {
                    'label': 'Another group',
                    'name': 'another_group',
                    'questions': [{
                        'name': "end",
                        'label': 'End',
                        'type': "EN",
                    }]
                }]
        serializer = serializers.QuestionGroupSerializer(
            data=data,
            many=True,
            context={'questionnaire_id': questionnaire.id,
                     'project': questionnaire.project})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        assert questionnaire.question_groups.count() == 2

        for group in questionnaire.question_groups.all():
            assert group.questions.count()
            if group.name == 'group':
                assert group.questions.first().name == 'start'
            elif group.name == 'another_group':
                assert group.questions.first().name == 'end'

    def test_create_numeric_attribute_with_default_0(self):
        questionnaire = factories.QuestionnaireFactory.create()
        data = {
            'label': 'Location Attributes',
            'name': 'location_attributes',
            'questions': [{
                'name': "number",
                'label': 'Number',
                'type': "IN",
                'default': 0,
                'index': 0
            }]
        }
        serializer = serializers.QuestionGroupSerializer(
            data=data,
            context={'questionnaire_id': questionnaire.id,
                     'project': questionnaire.project,
                     'default_language': 'en'})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        assert questionnaire.question_groups.count() == 1
        assert Attribute.objects.get(name='number').default == '0'


class QuestionSerializerTest(TestCase):
    def test_serialize(self):
        question = factories.QuestionFactory.create(
            default='some default',
            hint='An informative hint',
            relevant='${party_id}="abc123"'
        )
        serializer = serializers.QuestionSerializer(question)

        assert serializer.data['id'] == question.id
        assert serializer.data['name'] == question.name
        assert serializer.data['label'] == question.label
        assert serializer.data['type'] == question.type
        assert serializer.data['required'] == question.required
        assert serializer.data['constraint'] == question.constraint
        assert serializer.data['default'] == question.default
        assert serializer.data['hint'] == question.hint
        assert serializer.data['relevant'] == question.relevant
        assert 'options' not in serializer.data
        assert 'questionnaire' not in serializer.data
        assert 'question_group' not in serializer.data

    def test_serialize_multiple_lang(self):
        question = factories.QuestionFactory.create(
            default='some default',
            hint='An informative hint',
            relevant='${party_id}="abc123"',
            label={'en': 'Question', 'de': 'Frage'}
        )
        serializer = serializers.QuestionSerializer(question)

        assert serializer.data['id'] == question.id
        assert serializer.data['name'] == question.name
        assert serializer.data['label'] == {'en': 'Question', 'de': 'Frage'}
        assert serializer.data['type'] == question.type
        assert serializer.data['required'] == question.required
        assert serializer.data['constraint'] == question.constraint
        assert serializer.data['default'] == question.default
        assert serializer.data['hint'] == question.hint
        assert serializer.data['relevant'] == question.relevant
        assert 'options' not in serializer.data
        assert 'questionnaire' not in serializer.data
        assert 'question_group' not in serializer.data

    def test_serialize_with_options(self):
        question = factories.QuestionFactory.create(type='S1')
        factories.QuestionOptionFactory.create_batch(2, question=question)
        serializer = serializers.QuestionSerializer(question)

        assert serializer.data['id'] == question.id
        assert serializer.data['name'] == question.name
        assert serializer.data['label'] == question.label
        assert serializer.data['type'] == question.type
        assert serializer.data['required'] == question.required
        assert serializer.data['constraint'] == question.constraint
        assert len(serializer.data['options']) == 2
        assert 'questionnaire' not in serializer.data
        assert 'question_group' not in serializer.data

    def test_create_question(self):
        questionnaire = factories.QuestionnaireFactory.create()
        data = {
            'label': 'A question',
            'name': 'question',
            'type': 'TX'
        }
        serializer = serializers.QuestionSerializer(
            data=data,
            context={'questionnaire_id': questionnaire.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        assert questionnaire.questions.count() == 1
        question = questionnaire.questions.first()
        assert question.label == data['label']
        assert question.type == data['type']
        assert question.name == data['name']

    def test_with_options(self):
        questionnaire = factories.QuestionnaireFactory.create()
        data = {
            'label': 'A question',
            'name': 'question',
            'type': 'S1',
            'options': [{
                'label': 'An option',
                'name': 'option',
                'index': 0
            }]
        }
        serializer = serializers.QuestionSerializer(
            data=data,
            context={'questionnaire_id': questionnaire.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        assert questionnaire.questions.count() == 1
        question = questionnaire.questions.first()
        assert question.label == data['label']
        assert question.type == data['type']
        assert question.name == data['name']
        assert QuestionOption.objects.count() == 1
        assert question.options.count() == 1

    def test_bulk_create(self):
        questionnaire = factories.QuestionnaireFactory.create()
        data = [{
            'label': 'A question',
            'name': 'question',
            'type': 'TX'
        }, {
            'label': 'Another question',
            'name': 'another_question',
            'type': 'S1',
            'options': [{
                'label': 'An option',
                'name': 'option',
                'index': 0
            }]
        }]
        serializer = serializers.QuestionSerializer(
            data=data,
            many=True,
            context={'questionnaire_id': questionnaire.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        questions = questionnaire.questions.all()
        assert questions.count() == 2

        for q in questions:
            if q.name == 'question':
                assert q.label == 'A question'
                assert q.type == 'TX'
                assert q.options.count() == 0
            if q.name == 'another_question':
                assert q.label == 'Another question'
                assert q.type == 'S1'
                assert q.options.count() == 1


class QuestionOptionSerializerTest(TestCase):
    def test_serialize(self):
        question_option = factories.QuestionOptionFactory.create()
        serializer = serializers.QuestionOptionSerializer(question_option)

        assert serializer.data['id'] == question_option.id
        assert serializer.data['name'] == question_option.name
        assert serializer.data['label'] == question_option.label
        assert 'question' not in serializer.data

    def test_serialize_with_multiple_langs(self):
        question_option = factories.QuestionOptionFactory.create(
            label={'en': 'An option', 'de': 'Eine Option'})
        serializer = serializers.QuestionOptionSerializer(question_option)

        assert serializer.data['id'] == question_option.id
        assert serializer.data['name'] == question_option.name
        assert serializer.data['label'] == {'en': 'An option',
                                            'de': 'Eine Option'}
        assert 'question' not in serializer.data

    def test_create_option(self):
        question = factories.QuestionFactory.create()
        data = {
            'name': 'option',
            'label': 'An option',
            'index': 0
        }
        serializer = serializers.QuestionOptionSerializer(
            data=data,
            context={'question_id': question.id})
        serializer.is_valid()
        serializer.save()

        assert QuestionOption.objects.count() == 1
        option = QuestionOption.objects.first()
        assert option.name == data['name']
        assert option.label == data['label']
        assert option.label_xlat == data['label']
        assert option.question_id == question.id

    def test_bulk_create(self):
        question = factories.QuestionFactory.create()
        data = [{
            'name': 'option',
            'label': 'An option',
            'index': 0
        }, {
            'name': 'option_2',
            'label': 'Another',
            'index': 1
        }]
        serializer = serializers.QuestionOptionSerializer(
            data=data,
            many=True,
            context={'question_id': question.id})
        serializer.is_valid()
        serializer.save()
        assert question.options.count() == 2
