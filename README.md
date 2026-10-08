# MotoPulse

A terminal app for keeping track of motorcycle maintenance. Built in a two-person team in my first year of BSIT, as a
Python project for a data structures course.

You register an account, add your motorcycles by plate number, and schedule maintenance tasks.
MotoPulse ranks the open tasks by how overdue they are, so the job that needs doing first is at
the top of the list.

## What it does
- Register, log in and reset a password. Passwords are stored as SHA-256 hashes, never as text.
- Add and edit motorcycles (plate, make, model, year, mileage).
- Pick from nine standard jobs (oil change, chain, brake fluid and so on) or add your own.
  Each job remembers the interval you set for it.
- Rank open tasks with a priority queue (`heapq`). Urgency adds the kilometres overdue to the
  days overdue, and days count for more.
- Log completed work with its date and cost, and see the total spent per motorcycle.
- Undo recent actions with a stack: new motorcycles, mileage updates, scheduled tasks, completed
  maintenance and edits.
- Save everything to a local `motopulse_data.json` file.

## Run it
Python 3.8 or newer. No packages to install.

```bash
python MotoPulse_UI.py
```

Keep both files in the same folder. `MotoPulse_UI.py` is the menus, `MotoPulse_UX.py` is the data
model and the saving.

## What I would change today
- Passwords use plain SHA-256 with no salt. A real app needs a slow, salted hash such as bcrypt.
- Dates are typed as text and parsed against eleven formats. A date picker would be safer.
- Everything is in one JSON file, which is fine for a class project and not for real users.

## Notes
First-year coursework, shared as it was submitted apart from small edits.
