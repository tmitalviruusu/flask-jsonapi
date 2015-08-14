def get_create_request_schema(resource):
    return {
        "definitions": {
            "resource": {
                "type": "object",
                "required": ["type"],
                "properties": {
                    "type": {"type": "string"},
                    "id": {"type": "string"},
                    "attributes": {"type": "object"},
                    "relationships": {"$ref": "#/definitions/relationships"}
                }
            },
            "attributes": {
                "type": "object",
                "properties": {
                    attribute: {}
                    for attribute in resource.attributes
                }
            },
            "relationships": _get_relationships_definition(resource),
            "relationshipToOne": {
                "type": ["null", "object"],
                "required": [
                    "type",
                    "id"
                ],
                "properties": {
                    "type": {"type": "string"},
                    "id": {"type": "string"}
                }
            },
            "relationshipToMany": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": [
                        "type",
                        "id"
                    ],
                    "properties": {
                        "type": {"type": "string"},
                        "id": {"type": "string"}
                    }
                }
            }
        },
        "type": "object",
        "required": ["data"],
        "properties": {
            "data": {"$ref": "#/definitions/resource"}
        }
    }


def _get_relationships_definition(resource):
    return {
        "type": "object",
        "properties": {
            relationship: _get_relationship_definition(resource, relationship)
            for relationship in resource.relationships
        }
    }


def _get_relationship_definition(resource, relationship):
    if relationship in resource.to_one_relationships:
        ref = "#/definitions/relationshipToOne"
    else:
        ref = "#/definitions/relationshipToMany"
    return {
        "type": "object",
        "required": ["data"],
        "properties": {
            "data": {"$ref": ref}
        }
    }