# Serial Number Generator

A dark-themed Tkinter desktop app that generates serials of the form `PREFIX0001` – `PREFIX9999`.

- The prefix can be any length of letters and digits. Letters are always stored in uppercase.
- Each serial is saved to `serials.csv` and is never generated again, even after a restart.
- You can generate several serials at once and copy them to the clipboard.

## Run

Needs Python 3.9+ with Tkinter (included with the standard Python installers). No other dependencies.

```bash
python serial_generator.py
```
