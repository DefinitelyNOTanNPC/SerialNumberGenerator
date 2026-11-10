"""Serial Number Generator - a small, modern Tkinter app.

Serials have the form <PREFIX><NNN>, e.g. ABC001 ... ABC999.
Each prefix has its own sheet in serials.xlsx, and a serial is
never generated again.
"""

import os
import re
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

XLSX_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "serials.xlsx")
HEADER = ["serial", "prefix", "number", "part_number", "created"]
DIGITS = 3
MAX_NUMBER = 10**DIGITS - 1

# Palette
BG = "#14161c"
CARD = "#1e212b"
FIELD = "#272b38"
TEXT = "#e8eaf0"
MUTED = "#8a90a2"
ACCENT = "#6c8cff"
ACCENT_HOVER = "#8aa3ff"


def normalize_prefix(raw: str) -> str:
    """Strip non-alphanumerics and upper-case letters."""
    return re.sub(r"[^A-Za-z0-9]", "", raw).upper()


def clean_part_number(raw: str) -> str:
    """Part numbers may hold anything except commas/newlines; trimmed."""
    return raw.strip()


class SerialStore:
    """All serials live in one Excel workbook with a sheet per prefix."""

    def __init__(self, path: str = XLSX_FILE):
        self.path = path
        self.used: dict[str, set[int]] = {}
        if os.path.exists(path):
            self.wb = load_workbook(path)
            for ws in self.wb.worksheets:
                self.used[ws.title] = {
                    int(row[2]) for row in ws.iter_rows(min_row=2, values_only=True)
                    if row and row[2] is not None
                }
        else:
            self.wb = Workbook()
            self.wb.remove(self.wb.active)  # start with no empty default sheet

    def prefixes(self) -> list[str]:
        return sorted(self.used)

    def remaining(self, prefix: str) -> int:
        return MAX_NUMBER - len(self.used.get(prefix, ()))

    def _sheet(self, prefix: str):
        if prefix in self.wb.sheetnames:
            return self.wb[prefix]
        ws = self.wb.create_sheet(prefix)
        ws.append(HEADER)
        for cell in ws[1]:
            cell.font = Font(bold=True)
        for col, width in zip("ABCDE", (14, 10, 9, 24, 20)):
            ws.column_dimensions[col].width = width
        ws.freeze_panes = "A2"
        return ws

    def generate(self, prefix: str, count: int, part_number: str) -> list[str]:
        """Create `count` new serials (lowest unused numbers) and save them."""
        prefix = normalize_prefix(prefix)
        part_number = clean_part_number(part_number)
        if not prefix:
            raise ValueError("Prefix must contain at least one letter or digit.")
        if len(prefix) > 31:
            raise ValueError("Prefix can be at most 31 characters (Excel sheet name limit).")
        if not part_number:
            raise ValueError("Please enter a part number.")
        used = self.used.get(prefix, set())
        free = [n for n in range(1, MAX_NUMBER + 1) if n not in used][:count]
        if len(free) < count:
            raise ValueError(f"Only {len(free)} serial(s) left for prefix '{prefix}'.")
        ws = self._sheet(prefix)
        now = datetime.now().replace(microsecond=0)
        serials = [f"{prefix}{n:0{DIGITS}d}" for n in free]
        for serial, n in zip(serials, free):
            ws.append([serial, prefix, f"{n:0{DIGITS}d}", part_number, now])
            ws.cell(ws.max_row, 5).number_format = "yyyy-mm-dd hh:mm:ss"
        try:
            self.wb.save(self.path)
        except PermissionError:
            # Roll back in memory so nothing is handed out that wasn't saved.
            ws.delete_rows(ws.max_row - len(free) + 1, len(free))
            if ws.max_row == 1 and prefix not in self.used:
                self.wb.remove(ws)
            raise ValueError(f"Could not save {os.path.basename(self.path)}. "
                             "Close it in Excel and try again.")
        self.used.setdefault(prefix, set()).update(free)
        return serials


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.store = SerialStore()
        self.title("Serial Number Generator")
        self.geometry("540x660")
        self.minsize(420, 480)
        self.configure(bg=BG)
        self._style()
        self._build()

    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        font = ("Segoe UI", 11)
        s.configure(".", background=BG, foreground=TEXT, font=font)
        s.configure("Card.TFrame", background=CARD)
        s.configure("Card.TLabel", background=CARD, foreground=TEXT)
        s.configure("Muted.TLabel", background=CARD, foreground=MUTED, font=("Segoe UI", 9))
        s.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 20, "bold"))
        s.configure("Sub.TLabel", background=BG, foreground=MUTED)
        s.configure("TEntry", fieldbackground=FIELD, foreground=TEXT, insertcolor=TEXT,
                    bordercolor=FIELD, lightcolor=FIELD, darkcolor=FIELD, padding=8)
        s.map("TEntry", bordercolor=[("focus", ACCENT)], lightcolor=[("focus", ACCENT)])
        s.configure("TCombobox", fieldbackground=FIELD, foreground=TEXT, background=FIELD,
                    arrowcolor=TEXT, bordercolor=FIELD, lightcolor=FIELD, darkcolor=FIELD,
                    selectbackground=FIELD, selectforeground=TEXT, padding=8)
        s.map("TCombobox", fieldbackground=[("readonly", FIELD)],
              bordercolor=[("focus", ACCENT)], lightcolor=[("focus", ACCENT)])
        self.option_add("*TCombobox*Listbox.background", FIELD)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        s.configure("TSpinbox", fieldbackground=FIELD, foreground=TEXT, background=FIELD,
                    arrowcolor=TEXT, bordercolor=FIELD, lightcolor=FIELD, darkcolor=FIELD,
                    padding=8)
        s.configure("Accent.TButton", background=ACCENT, foreground="#ffffff", borderwidth=0,
                    focusthickness=0, padding=(16, 10), font=("Segoe UI", 11, "bold"))
        s.map("Accent.TButton", background=[("active", ACCENT_HOVER)])
        s.configure("Ghost.TButton", background=FIELD, foreground=TEXT, borderwidth=0,
                    padding=(12, 10))
        s.map("Ghost.TButton", background=[("active", "#323748")])

    def _build(self):
        root = ttk.Frame(self, padding=24)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text="Serial Generator", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="Format: PREFIX001 – PREFIX999", style="Sub.TLabel").pack(
            anchor="w", pady=(0, 16))

        card = ttk.Frame(root, style="Card.TFrame", padding=20)
        card.pack(fill="x")
        card.columnconfigure(0, weight=1)

        ttk.Label(card, text="Prefix (type new or pick existing)", style="Card.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(card, text="Quantity", style="Card.TLabel").grid(row=0, column=1, sticky="w", padx=(12, 0))

        self.prefix_var = tk.StringVar()
        self.prefix_var.trace_add("write", self._on_prefix)
        self.prefix_box = ttk.Combobox(card, textvariable=self.prefix_var,
                                       values=self.store.prefixes(), font=("Consolas", 13))
        self.prefix_box.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.prefix_box.focus()
        self.prefix_box.bind("<Return>", lambda e: self.generate())

        self.count_var = tk.IntVar(value=1)
        ttk.Spinbox(card, from_=1, to=MAX_NUMBER, textvariable=self.count_var, width=7,
                    font=("Consolas", 13)).grid(row=1, column=1, padx=(12, 0), pady=(4, 0))

        self.info = ttk.Label(card, text="Letters and digits only – stored in uppercase.",
                              style="Muted.TLabel")
        self.info.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 12))

        ttk.Label(card, text="Part number", style="Card.TLabel").grid(
            row=3, column=0, columnspan=2, sticky="w")
        self.part_var = tk.StringVar()
        part = ttk.Entry(card, textvariable=self.part_var, font=("Consolas", 13))
        part.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(4, 16))
        part.bind("<Return>", lambda e: self.generate())

        ttk.Button(card, text="Generate", style="Accent.TButton",
                   command=self.generate).grid(row=5, column=0, columnspan=2, sticky="ew")

        # Results
        head = ttk.Frame(root)
        head.pack(fill="x", pady=(20, 6))
        ttk.Label(head, text="Generated", style="Sub.TLabel").pack(side="left")
        ttk.Button(head, text="Copy all", style="Ghost.TButton",
                   command=self.copy_all).pack(side="right")

        self.results = tk.Listbox(root, bg=CARD, fg=TEXT, font=("Consolas", 13),
                                  borderwidth=0, highlightthickness=0, activestyle="none",
                                  selectbackground=ACCENT, selectforeground="#ffffff")
        self.results.pack(fill="both", expand=True)

        self.status = ttk.Label(root, text="Saved to serials.xlsx (one sheet per prefix)",
                                style="Sub.TLabel")
        self.status.pack(anchor="w", pady=(8, 0))

    def _on_prefix(self, *_):
        raw = self.prefix_var.get()
        clean = normalize_prefix(raw)
        if raw != clean:
            self.prefix_var.set(clean)  # live uppercase / filter
            return
        if clean:
            self.info.config(text=f"{self.store.remaining(clean)} serial(s) available for '{clean}'.")
        else:
            self.info.config(text="Letters and digits only – stored in uppercase.")

    def generate(self):
        try:
            count = int(self.count_var.get())
            if count < 1:
                raise ValueError("Quantity must be at least 1.")
            serials = self.store.generate(self.prefix_var.get(), count, self.part_var.get())
        except (ValueError, tk.TclError) as e:
            messagebox.showerror("Cannot generate", str(e))
            return
        self.results.delete(0, "end")
        for s in serials:
            self.results.insert("end", s)
        self.prefix_box.config(values=self.store.prefixes())
        self._on_prefix()
        prefix = normalize_prefix(self.prefix_var.get())
        self.status.config(text=f"Generated {len(serials)} × {clean_part_number(self.part_var.get())}"
                                f" · saved to sheet {prefix} in serials.xlsx")

    def copy_all(self):
        items = self.results.get(0, "end")
        if items:
            self.clipboard_clear()
            self.clipboard_append("\n".join(items))
            self.status.config(text=f"Copied {len(items)} serial(s) to clipboard")


if __name__ == "__main__":
    App().mainloop()
