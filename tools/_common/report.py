"""Shared finding dataclass and severity enum used by lint, render, and other tools."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class Finding:
    severity: Severity
    file: str          # relative path, or "" for base-level findings
    message: str
    line: int | None = None

    def to_dict(self) -> dict:
        return {
            "severity": self.severity.value,
            "file": self.file,
            "message": self.message,
            "line": self.line,
        }
