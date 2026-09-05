"""Local fonts, resource paths and Windows DPI setup."""

import sys
from pathlib import Path


def _resource_path(relative_path: str) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base_path / relative_path


def _load_private_fonts() -> None:
    """Make bundled fonts available to this process without installing them."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        for filename in ("Mulish-VariableFont_wght.ttf", "Mulish-Italic-VariableFont_wght.ttf"):
            font_path = _resource_path(f"assets/fonts/{filename}")
            if font_path.exists():
                ctypes.windll.gdi32.AddFontResourceExW(str(font_path), 0x10, 0)
    except Exception:
        pass


def _enable_windows_dpi_awareness() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
