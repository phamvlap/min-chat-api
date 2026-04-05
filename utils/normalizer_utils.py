from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


def normalize_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, (list, tuple)):
        return [normalize_value(item) for item in value]

    if isinstance(value, dict):
        return {key: normalize_value(val) for key, val in value.items()}

    return str(value)


def to_serializable_dict(data: dict) -> dict:
    return {key: normalize_value(value) for key, value in data.items()}
