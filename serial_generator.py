"""Serial Number Generator - a small, modern Tkinter app.

Serials have the form <PREFIX><NNNN>, e.g. ABC0001 ... ABC9999.
Every generated serial is saved to serials.csv and is never generated again.
"""

import csv
import os
import re
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "serials.csv")
CSV_HEADER = ["serial", "prefix", "number", "created"]
MAX_NUMBER = 9999

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


class SerialStore:
    """Persists serials in a CSV file and guarantees uniqueness."""

    def __init__(self, path: str = CSV_FILE):
        self.path = path
        self.used: set[str] = set()
        if os.path.exists(path):
            with open(path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    self.used.add(row["serial"].upper())
        else:
            with open(path, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(CSV_HEADER)

    def remaining(self, prefix: str) -> int:
        return sum(
            1 for n in range(1, MAX_NUMBER + 1) if f"{prefix}{n:04d}" not in self.used
        )

    def generate(self, prefix: str, count: int) -> list[str]:
        """Return `count` new serials (lowest unused numbers) and save them."""
        prefix = normalize_prefix(prefix)
        if not prefix:
            raise ValueError("Prefix must contain at least one letter or digit.")
        new = []
        for n in range(1, MAX_NUMBER + 1):
            serial = f"{prefix}{n:04d}"
            if serial not in self.used:
                new.append((serial, n))
                if len(new) == count:
                    break
        if len(new) < count:
            raise ValueError(
                f"Only {len(new)} serial(s) left for prefix '{prefix}'."
            )
        now = datetime.now().isoformat(timespec="seconds")
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            for serial, n in new:
                w.writerow([serial, prefix, f"{n:04d}", now])
                self.used.add(serial)
        return [s for s, _ in new]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.store = SerialStore()
        self.title("Serial Number Generator")
        self.geometry("520x600")
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
        ttk.Label(root, text="Format: PREFIX0001 – PREFIX9999", style="Sub.TLabel").pack(
            anchor="w", pady=(0, 16))

        card = ttk.Frame(root, style="Card.TFrame", padding=20)
        card.pack(fill="x")
        card.columnconfigure(0, weight=1)

        ttk.Label(card, text="Prefix", style="Card.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(card, text="Quantity", style="Card.TLabel").grid(row=0, column=1, sticky="w", padx=(12, 0))

        self.prefix_var = tk.StringVar()
        self.prefix_var.trace_add("write", self._on_prefix)
        entry = ttk.Entry(card, textvariable=self.prefix_var, font=("Consolas", 13))
        entry.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        entry.focus()
        entry.bind("<Return>", lambda e: self.generate())

        self.count_var = tk.IntVar(value=1)
        ttk.Spinbox(card, from_=1, to=MAX_NUMBER, textvariable=self.count_var, width=7,
                    font=("Consolas", 13)).grid(row=1, column=1, padx=(12, 0), pady=(4, 0))

        self.info = ttk.Label(card, text="Letters and digits only – stored in uppercase.",
                              style="Muted.TLabel")
        self.info.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 12))

        ttk.Button(card, text="Generate", style="Accent.TButton",
                   command=self.generate).grid(row=3, column=0, columnspan=2, sticky="ew")

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

        self.status = ttk.Label(root, text=f"Saved to {os.path.basename(CSV_FILE)}",
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
            serials = self.store.generate(self.prefix_var.get(), count)
        except (ValueError, tk.TclError) as e:
            messagebox.showerror("Cannot generate", str(e))
            return
        self.results.delete(0, "end")
        for s in serials:
            self.results.insert("end", s)
        self._on_prefix()
        self.status.config(text=f"Generated {len(serials)} serial(s) · saved to {os.path.basename(CSV_FILE)}")

    def copy_all(self):
        items = self.results.get(0, "end")
        if items:
            self.clipboard_clear()
            self.clipboard_append("\n".join(items))
            self.status.config(text=f"Copied {len(items)} serial(s) to clipboard")


if __name__ == "__main__":
    App().mainloop()
