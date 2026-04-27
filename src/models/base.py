from __future__ import annotations

from dataclasses import asdict, fields


class BaseModel:
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        field_names = {field.name for field in fields(cls)}
        payload = {name: data.get(name) for name in field_names}
        return cls(**payload)
