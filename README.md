# Serial Number Generator

A dark-themed Tkinter desktop app that generates serials of the form `PREFIX001` – `PREFIX999`.

- The prefix can be any length of letters and digits. Letters are always stored in uppercase.
- Each batch is tagged with a part number (any text, including `-` and `_`).
- Pick an existing prefix from the dropdown or type a new one.
- Each prefix has its own sheet in `serials.xlsx`. A serial is never generated again, even after a restart.
- You can generate several serials at once and copy them to the clipboard.

## Run

Needs Python 3.9+ with Tkinter (included with the standard Python installers). Install the one dependency first:

```bash
pip install -r requirements.txt
```

Then:

```bash
python serial_generator.py
```
