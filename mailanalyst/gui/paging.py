"""Small page controls shared by source and result tables."""

import tkinter as tk
from tkinter import ttk

PAGE_SIZE = 500


class Pager:
    def __init__(self, parent, row, filters, load, render):
        self.offset = 0
        self.total = 0
        self.load, self.render = load, render
        self.filters = filters
        bar = ttk.Frame(parent, style="Surface.TFrame")
        bar.grid(row=row, column=0, sticky="ew", pady=6)
        self.filter = tk.StringVar(value=next(iter(filters)))
        combo = ttk.Combobox(bar, textvariable=self.filter, values=tuple(filters), state="readonly", width=20)
        combo.pack(side="left")
        combo.bind("<<ComboboxSelected>>", lambda _: self.refresh(reset=True))
        self.previous = ttk.Button(bar, text="Zurück", command=lambda: self.move(-1))
        self.previous.pack(side="left", padx=6)
        self.next = ttk.Button(bar, text="Weiter", command=lambda: self.move(1))
        self.next.pack(side="left")
        self.label = tk.StringVar(value="Keine Einträge")
        ttk.Label(bar, textvariable=self.label).pack(side="left", padx=12)

    def move(self, direction):
        self.offset = max(0, self.offset + direction * PAGE_SIZE)
        self.refresh()

    def refresh(self, reset=False):
        if reset:
            self.offset = 0
        rows, self.total = self.load(self.offset, self.filters[self.filter.get()])
        if self.offset and self.offset >= self.total:
            self.offset = max(0, ((self.total - 1) // PAGE_SIZE) * PAGE_SIZE)
            rows, self.total = self.load(self.offset, self.filters[self.filter.get()])
        self.render(rows)
        start = self.offset + 1 if rows else 0
        self.label.set(f"{start}–{self.offset + len(rows)} von {self.total} Einträgen")
        self.previous.state(["!disabled"] if self.offset else ["disabled"])
        self.next.state(["!disabled"] if self.offset + len(rows) < self.total else ["disabled"])


def scrollable_table(parent, columns, row=4):
    frame = ttk.Frame(parent)
    frame.grid(row=row, column=0, sticky="nsew")
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)
    table = ttk.Treeview(frame, columns=columns, show="headings")
    table.grid(row=0, column=0, sticky="nsew")
    vertical = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
    horizontal = ttk.Scrollbar(frame, orient="horizontal", command=table.xview)
    vertical.grid(row=0, column=1, sticky="ns")
    horizontal.grid(row=1, column=0, sticky="ew")
    table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    return table
