from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class FileSignature:
    source_path: str
    file_name: str
    file_ext: str
    file_size: int
    modified_at: str
    modified_at_ns: int
    file_sha256: str

    @property
    def key(self) -> str:
        return self.source_path
