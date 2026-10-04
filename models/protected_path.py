"""Protected path data model."""

from dataclasses import dataclass


@dataclass
class ProtectedPath:
    id: int | None
    path: str
    name: str
    reason: str
    created_at: str
    updated_at: str
