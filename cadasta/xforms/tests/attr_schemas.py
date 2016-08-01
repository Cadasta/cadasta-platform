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
