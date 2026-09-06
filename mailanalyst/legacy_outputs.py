"""Publish explicit CLI paths after the authoritative package is validated."""

import os
import shutil
from pathlib import Path
from uuid import uuid4


def publish_copy(source: Path, target: Path) -> None:
    target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    token = uuid4().hex
    temporary = target.with_name(".pending-" + token)
    backup = target.with_name(".previous-" + token)
    try:
        if source.is_dir():
            shutil.copytree(source, temporary)
            if target.exists():
                target.rename(backup)
            try:
                temporary.rename(target)
            except OSError:
                if backup.exists():
                    backup.rename(target)
                raise
        else:
            shutil.copy2(source, temporary)
            os.replace(temporary, target)
    finally:
        if temporary.is_dir():
            shutil.rmtree(temporary)
        else:
            temporary.unlink(missing_ok=True)
