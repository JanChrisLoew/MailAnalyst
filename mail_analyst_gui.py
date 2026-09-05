"""Start the desktop application; implementation lives in mailanalyst.gui."""

from mailanalyst.gui.app import MailAnalystApp
from mailanalyst.gui.resources import _enable_windows_dpi_awareness


if __name__ == "__main__":
    _enable_windows_dpi_awareness()
    MailAnalystApp().mainloop()
