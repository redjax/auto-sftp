import typing as t
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, field_validator, ConfigDict
import pendulum


class File(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(default=None)
    path: t.Union[str, Path] = Field(default=None)
    ext: str = Field(default=None)
    parent: t.Union[str, Path] = Field(default=None)
    created_at: pendulum.DateTime = Field(default=None)
    modified_at: pendulum.DateTime = Field(default=None)
    size_in_bytes: int = Field(default=0)
