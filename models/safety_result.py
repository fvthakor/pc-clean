"""Safety Result Model."""

from dataclasses import dataclass

from app.constants import SafetyLevel


@dataclass
class SafetyResult:
    level: SafetyLevel
    reason: str
    can_delete: bool
    requires_confirmation: bool = True
    requires_admin: bool = False
    is_protected: bool = False
    is_system: bool = False
    is_user_data: bool = False
    is_developer_data: bool = False
    is_cache: bool = False
    confidence: float = 1.0  # 0.0 to 1.0
    recommendation: str = ""
