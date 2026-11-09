# MotoPulse

A terminal app for keeping track of motorcycle maintenance. Built by Evan Exanes and Rhona-mae P. Prudenciado as a
two-person team in first-year BSIT, for a data structures course.

You register an account, add your motorcycles by plate number, and schedule maintenance tasks.
MotoPulse ranks the open tasks by how overdue they are, so the job that needs doing first is at
the top of the list.

## What it does
- Register, log in and reset a password. Passwords are stored as SHA-256 hashes, never as text.
- Add and edit motorcycles (plate, make, model, year, mileage).
- Pick from nine standard jobs (oil change, chain, brake fluid and so on) or add your own.
  Each job remembers the interval you set for it, and a standard job offers its usual interval as the default the first time.
- Rank open tasks with a priority queue (`heapq`). Urgency adds the kilometres overdue to a
  date score: 10 points for each day overdue, 7 on the due date and 1 to 6 in the week before.
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

## Project layout

| File | Role |
|---|---|
| `MotoPulse_UI.py` | The menus: login, dashboard, motorcycle screens, date parsing and undo |
| `MotoPulse_UX.py` | The data model (users, motorcycles, tasks, service records), the priority queue and the JSON saving |

## Notes
First-year coursework, shared as it was submitted apart from small edits and the changes below.

Changes after submission:
- A header block, comments and docstrings in both files.
- The urgency score no longer falls to 0 on the due date. Before, a task due tomorrow outranked one due today.
- The completed-work prompt asks for the COMPLETION DATE. It used to say DUE DATE.
- Standard jobs offer their usual interval as the default.

## Source file headers
Every source file opens with a header block: program name, description, author, date compiled and a change history. A commit that changes a file adds a row to its history.
