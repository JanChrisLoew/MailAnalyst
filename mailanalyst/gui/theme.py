"""Corporate colors and ttk styles."""

import tkinter.font as tkfont
from tkinter import ttk

COLORS = {
    "background": "#F5F4F2",
    "surface": "#FFFFFF",
    "sidebar": "#414343",
    "sidebar_hover": "#555858",
    "primary": "#D63C24",
    "primary_hover": "#B8321F",
    "accent_secondary": "#EF7D00",
    "accent_tertiary": "#0090B6",
    "accent_tertiary_hover": "#007894",
    "accent_soft": "#FBE9E6",
    "text": "#414343",
    "muted": "#707474",
    "border": "#D9DADA",
    "success": "#007E9F",
    "success_soft": "#E3F4F8",
    "warning": "#A85A00",
    "warning_soft": "#FFF0DF",
    "error": "#D63C24",
    "error_soft": "#FBE9E6",
}


def configure_style(app) -> None:
    family = app.font_family
    app.option_add("*Font", (family, 10))
    app.option_add("*TCombobox*Listbox.font", (family, 10))
    default_font = tkfont.nametofont("TkDefaultFont")
    default_font.configure(family=family, size=10)
    text_font = tkfont.nametofont("TkTextFont")
    text_font.configure(family=family, size=10)

    style = ttk.Style(app)
    style.theme_use("clam")
    c = app.COLORS
    style.configure("TFrame", background=c["background"])
    style.configure("Surface.TFrame", background=c["surface"])
    style.configure("Sidebar.TFrame", background=c["sidebar"])
    style.configure("Header.TFrame", background=c["surface"])
    style.configure("TLabel", background=c["background"], foreground=c["text"])
    style.configure("Surface.TLabel", background=c["surface"], foreground=c["text"])
    style.configure("Title.TLabel", background=c["surface"], foreground=c["text"], font=(family, 20, "bold"))
    style.configure("PageTitle.TLabel", background=c["surface"], foreground=c["text"], font=(family, 17, "bold"))
    style.configure("Subtitle.TLabel", background=c["surface"], foreground=c["muted"], font=(family, 10))
    style.configure("SidebarTitle.TLabel", background=c["sidebar"], foreground="#D5DADA", font=(family, 9, "bold"))
    style.configure("Offline.TLabel", background=c["success_soft"], foreground=c["success"], font=(family, 9, "bold"), padding=(10, 5))

    style.configure("TButton", font=(family, 10, "bold"), padding=(14, 8), borderwidth=1,
                    background=c["surface"], foreground=c["text"], bordercolor=c["border"])
    style.map("TButton", background=[("active", "#EAF0F3")], bordercolor=[("active", "#B9C8D0")])
    style.configure("Primary.TButton", background=c["primary"], foreground="#FFFFFF", bordercolor=c["primary"], padding=(18, 10))
    style.map("Primary.TButton", background=[("active", c["primary_hover"]), ("disabled", "#A9BCC5")],
              foreground=[("disabled", "#EEF2F4")])
    style.configure("Nav.TButton", background=c["sidebar"], foreground="#C6D5DE", borderwidth=0,
                    anchor="w", padding=(18, 13), font=(family, 10, "bold"))
    style.map("Nav.TButton", background=[("active", c["sidebar_hover"]), ("disabled", c["sidebar"])],
              foreground=[("disabled", "#688496")])
    style.configure("ActiveNav.TButton", background=c["accent_tertiary"], foreground="#FFFFFF", borderwidth=0,
                    anchor="w", padding=(18, 13), font=(family, 10, "bold"))
    style.map("ActiveNav.TButton", background=[("active", c["accent_tertiary_hover"])])

    style.configure("TLabelframe", background=c["surface"], bordercolor=c["border"], relief="solid", borderwidth=1)
    style.configure("TLabelframe.Label", background=c["surface"], foreground=c["text"], font=(family, 10, "bold"))
    style.configure("TEntry", fieldbackground="#FBFCFD", foreground=c["text"], bordercolor=c["border"], padding=7)
    style.configure("TCombobox", fieldbackground="#FBFCFD", foreground=c["text"], bordercolor=c["border"], padding=6)
    style.map("TCombobox", fieldbackground=[("readonly", "#FBFCFD")], selectbackground=[("readonly", "#FBFCFD")],
              selectforeground=[("readonly", c["text"])])
    style.configure("TCheckbutton", background=c["surface"], foreground=c["text"])
    style.map("TCheckbutton", background=[("active", c["surface"])])
    style.configure("Horizontal.TProgressbar", background=c["accent_tertiary"], troughcolor="#E3E6E6", borderwidth=0, thickness=9)
    style.configure("Treeview", background=c["surface"], fieldbackground=c["surface"], foreground=c["text"],
                    rowheight=30, bordercolor=c["border"], lightcolor=c["border"], darkcolor=c["border"])
    style.configure("Treeview.Heading", background="#ECEEEE", foreground=c["text"], font=(family, 9, "bold"),
                    padding=(8, 8), relief="flat")
    style.map("Treeview", background=[("selected", c["accent_tertiary"])], foreground=[("selected", "#FFFFFF")])
    style.layout("Content.TNotebook.Tab", [])
    style.configure("Content.TNotebook", background=c["background"], borderwidth=0)
    style.configure("Content.TNotebook.Client", background=c["surface"], borderwidth=0)
