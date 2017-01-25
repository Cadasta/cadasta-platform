from django.conf import settings
from django.template.loader import render_to_string


tmpl = 'search/search_result_item.html'


def get_mock_async_search_results():
    return (
        [
            [
                "Location",
                "Community boundary",
                render_to_string(tmpl, context={'result': {
                    'entity_type': "Location",
                    'url': 'http://www.example.com',
                    'main_label': "Community boundary",
                    'attributes': [
                        ("Village name", "Abbey Road"),
                    ],
                }}),
            ],
            [
                "Party",
                "John Lennon",
                render_to_string(tmpl, context={'result': {
                    'entity_type': "Party",
                    'url': 'http://www.example.com',
                    'main_label': "John Lennon",
                    'attributes': [
                        ("Type", "Individual"),
                    ],
                }}),
            ],
            [
                "Relationship",
                "Concessionary Rights",
                render_to_string(tmpl, context={'result': {
                    'entity_type': "Relationship",
                    'url': 'http://www.example.com',
                    'main_label': "Concessionary Rights",
                    'attributes': [
                        ("Party", "John Lennon"),
                        ("Location type", "Community boundary"),
                    ],
                }}),
            ],
            [
                "Resource",
                "“Imagine” recording",
                render_to_string(tmpl, context={'result': {
                    'entity_type': "Resource",
                    'url': 'http://www.example.com',
                    'main_label': "“Imagine” recording",
                    'attributes': [
                        ("Original file", "imagine.mp3"),
                        ("Description", "Recording of John Lennon’s song"),
                    ],
                    'image': settings.ICON_URL.format('mp3'),
                }}),
            ],
        ],
        '1999-12-31T12:34:56.789Z',
    )
