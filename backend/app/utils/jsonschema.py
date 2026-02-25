from jsonschema import ValidationError, validate


def validate_json_schema(payload: dict, schema: dict) -> tuple[bool, str | None]:
    try:
        validate(instance=payload, schema=schema)
        return True, None
    except ValidationError as exc:
        return False, str(exc)
