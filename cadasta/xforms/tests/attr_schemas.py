party_xform_group = {
    "label": "Party Attributes",
    "name": "party_attributes",
    "type": "group",
    "children": [
        {
            "label": "Gender",
            "name": "gender",
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
            "default": "f",
            "bind": {
                "relevant": "${party_type}='individual'"
            },
            "type": "select one"
        },
        {
            "label": "Homeowner",
            "name": "homeowner",
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
            "default": "no",
            "bind": {
                "relevant": "${party_type}='individual'",
            },
            "type": "select one"
        },
        {
            "label": "Date of Birth",
            "name": "dob",
            "bind": {
                "relevant": "${party_type}='individual'",
                "required": "yes"
            },
            "type": "date"
        },
        {
            "label": "Notes",
            "name": "notes",
            "type": "text",
            "hint": "Additional Notes"
        }
    ],
}

location_xform_group = {
    "type": "group",
    "name": "location_attributes",
    "label": "Location Attributes",
    "children": [
        {
            "label": "Name",
            "name": "name",
            "type": "text",
            "hint": "Name of the location"
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
            "label": "Notes",
            "name": "notes",
            "type": "text",
            "hint": "Additional Notes"
        }
    ],
    "label": "Tenure relationship attributes",
    "type": "group"
}
