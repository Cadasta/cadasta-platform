default_party_xform_group = {
    "label": "Default Party Attributes",
    "children": [
        {
            "label": "Notes",
            "type": "text",
            "name": "notes"
        }
    ],
    "type": "group",
    "name": "party_attributes_default"
}

individual_party_xform_group = {
    "label": "Individual Party Attributes",
    "children": [
        {
            "label": "Gender",
            "default": "f",
            "choices": [
                {
                    "label": "Male",
                    "name": "m"
                },
                {
                    "label": "Female",
                    "name": "f"
                }
            ],
            "type": "select one",
            "name": "gender"
        },
        {
            "default": "no",
            "label": "Homeowner",
            "hint": "Is homeowner",
            "choices": [
                {
                    "label": "Yes",
                    "name": "yes"
                },
                {
                    "label": "No",
                    "name": "no"
                }
            ],
            "type": "select one",
            "name": "homeowner"
        },
        {
            "label": "Date of Birth",
            "type": "date",
            "name": "dob",
            "bind": {
                "required": "yes"
            },
        }
    ],
    "name": "party_attributes_individual",
    "bind": {
        "relevant": "${party_type}='IN'"
    },
    "type": "group"
}

group_party_attributes = {
    "label": "Group Party Attributes",
    "children": [
        {
            "label": "Number of Members",
            "type": "integer",
            "name": "number_of_members"
        },
        {
            "label": "Date Group Formed",
            "type": "date",
            "name": "date_formed"
        }
    ],
    "name": "party_attributes_group",
    "bind": {
        "relevant": "${party_type}='GR'"
    },
    "type": "group"
}

location_xform_group = {
    "type": "group",
    "name": "location_attributes",
    "label": "Location Attributes",
    "children": [
        {
            "default": "none",
            "choices": [
                {
                    "name": "none",
                    "label": "No data"
                },
                {
                    "name": "text",
                    "label": "Textual"
                },
                {
                    "name": "point",
                    "label": "Point data"
                },
                {
                    "name": "polygon_low",
                    "label": "Low quality polygon"
                },
                {
                    "name": "polygon_high",
                    "label": "High quality polygon"
                }
            ],
            "hint": "Quality of parcel geometry",
            "name": "quality",
            "type": "select one",
            "label": "Spatial Unit Quality"
        },
        {
            "label": "Notes",
            "name": "notes",
            "type": "text",
            "omit": "yes",
            "hint": "Additional Notes"
        },
        {
            "label": "Infrastructure",
            "name": "infrastructure",
            "type": "select all that apply",
            "choices": [
                {
                    "name": "water",
                    "label": "Water",
                },
                {
                    "name": "food",
                    "label": "Food",
                },
                {
                    "name": "electricity",
                    "label": "Electricity",
                },
            ]
        }
    ]
}

location_relationship_xform_group = {
    "name": "location_relationship_attributes",
    "children": [
        {
            "name": "notes",
            "label": "Notes",
            "type": "text"
        }
    ],
    "label": "Location relationship attributes",
    "type": "group"
}

party_relationship_xform_group = {
    "name": "party_relationship_attributes",
    "children": [
        {
            "name": "notes",
            "label": "Notes",
            "type": "text"
        }
    ],
    "label": "Party relationship attributes",
    "type": "group"
}

tenure_relationship_xform_group = {
    "name": "tenure_relationship_attributes",
    "children": [
        {
            "name": "notes",
            "label": "Notes",
            "type": "text"
        }
    ],
    "label": "Tenure relationship attributes",
    "type": "group"
}
