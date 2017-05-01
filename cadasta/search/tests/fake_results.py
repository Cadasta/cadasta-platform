def get_fake_es_api_results(proj, su, party, tenure_rel, resource):
    return {
        "took": 63,
        "timed_out": 'false',
        "_shards": {
            "total": 4,
            "successful": 4,
            "failed": 0
        },
        "hits": {
            "total": 4,
            "max_score": 'null',
            "hits": [
                {
                    "_index": "project-slug",
                    "_type": "project",
                    "_id": proj.id,
                    "_score": 'null',
                    "_source": {
                        "id": proj.id,
                        "name": "Test Project",
                        "slug": "test-project",
                        "country": "US",
                        "description": "This project is awesome!",
                        "archived": False,
                        "urls": [],
                        "contacts": {
                            "type": "jsonb",
                            "value": "[]"
                        },
                        "last_updated": "2017-01-11T09:15:29.026Z",
                        "extent": {
                            "type": "geometry",
                            "value": "SOMEVALUE",
                        },
                        "access": "public",
                        "current_questionnaire": "some-id",
                        "organization_id": "some-other-id",
                        "@version": "1",
                        "@timestamp": "2017-01-16T13:20:15.271Z",
                        "type": "project"
                    },
                },
                {
                    "_index": "project-slug",
                    "_type": "spatial",
                    "_id": su.id,
                    "_score": 'null',
                    "_source": {
                        "id": su.id,
                        "geometry": {
                            "type": "geometry",
                            "value": ("0101000020E6100000000000000000F03F"
                                      "000000000000F03F"),
                        },
                        "type": "AP",
                        "attributes": {
                            "type": "jsonb",
                            "value": (
                                '{"name": "Long Island", '
                                '"notes": "Nothing to see here.", '
                                '"acquired_when": "2016-12-16", '
                                '"quality": "text", '
                                '"acquired_how": "LH"}'
                            )
                        },
                        "project_id": proj.id,
                        "@version": "1",
                        "@timestamp": "2017-01-12T07:28:31.505Z",
                    },
                },
                {
                    "_index": "project-slug",
                    "_type": "party",
                    "_id": party.id,
                    "_score": 'null',
                    "_source": {
                        "id": party.id,
                        "name": "Party in the USA",
                        "type": 'GR',
                        "attributes": {
                            "type": "jsonb",
                            "value": '{"party_notes": "PBS is the best."}',
                        },
                        "project_id": proj.id,
                        "tenure_id": None,
                        "tenure_attributes": None,
                        "tenure_partyid": None,
                        "spatial_unit_id": None,
                        "tenure_type_id": None,
                        "tenure_projectid": None,
                        "@version": "1",
                        "@timestamp": "2017-01-12T07:28:31.505Z",
                    },
                },
                {
                    "_index": "project-slug",
                    "_type": "party",
                    "_id": tenure_rel.id,
                    "_score": 'null',
                    "_source": {
                        "id": party.id,
                        "name": "Party in the USA",
                        "type": 'IN',
                        "attributes": {
                            "type": "jsonb",
                            "value": '{"party_notes": "PBS is the best."}',
                        },
                        "project_id": proj.id,
                        "tenure_id": tenure_rel.id,
                        "tenure_attributes": {
                            "type": "jsonb",
                            "value": '{"rel_notes": "PBS is the best."}',
                        },
                        "tenure_partyid": party.id,
                        "spatial_unit_id": su.id,
                        "tenure_type_id": "CU",
                        "tenure_projectid": proj.id,
                        "@version": "1",
                        "@timestamp": "2017-01-12T07:28:31.505Z",
                    },
                },
                {
                    "_index": "project-slug",
                    "_type": "resource",
                    "_id": resource.id,
                    "_score": 'null',
                    "_source": {
                        "id": resource.id,
                        "name": "Goat",
                        "description": "Let's pretend there's a description.",
                        "file": "https://example.com/text.csv",
                        "original_file": "baby_goat.jpeg",
                        "file_versions": None,
                        "mime_type": "text/csv",
                        "archived": False,
                        "last_updated": "2016-12-20T13:16:06.264Z",
                        "contributor_id": 1,
                        "project_id": proj.id,
                        "@version": "1",
                        "@timestamp": "2017-01-12T07:28:31.505Z",
                    },
                },
            ]
        }
    }
