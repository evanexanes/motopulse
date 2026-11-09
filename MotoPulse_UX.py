# Program name: MotoPulse_UX.py
# Description: Data model and storage for MotoPulse: users, motorcycles, maintenance
#    tasks, service records and the undo stack. Ranks open tasks with a heapq priority
#    queue and saves everything to motopulse_data.json.
# Author: Exanes, Evan Prens (two-person team project)
# Date Compiled: 10/08/2026
# ======================================================================
# Date           Description                      Programmer name
# ======================================================================
# 10/08/2026     Initial Implementation           EPPE
# 11/09/2026     Added header and comments        EPPE
# ======================================================================

import json
import os
import heapq
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Formats tried in order when scoring urgency. The UI stores dates as MONTH-DD-YEAR, the first
# entry. The others cover spaced and numeric variants.
DATE_FORMATS = ["%B-%d-%Y", "%B - %d - %Y", "%m-%d-%Y", "%m - %d - %Y", "%B %d, %Y", "%Y-%m-%d"]


class ServiceRecord:
    """One completed job: its date, the mileage and cost, and what was done."""

    def __init__(self, date: str, mileage: int, cost: float, description: str):
        self.date = date
        self.mileage = mileage
        self.cost = cost
        self.description = description

    def to_dict(self):
        return {
            "date": self.date,
            "mileage": self.mileage,
            "cost": self.cost,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            date=data["date"],
            mileage=data["mileage"],
            cost=data["cost"],
            description=data["description"]
        )


class MaintenanceTask:
    """A scheduled job with a due mileage and a due date. Either one can make it overdue."""

    def __init__(
        self,
        name: str,
        description: str,
        due_mileage: int,
        due_date: str,
        suggested_mileage: int = 0,
        task_id: Optional[str] = None
    ):
        # Timestamp as a string id. Tasks loaded from the save file keep the id they were saved with.
        self.task_id = task_id or str(datetime.now().timestamp())
        self.name = name                          
        self.description = description            
        self.due_mileage = due_mileage            
        self.due_date = due_date                  
        self.suggested_mileage = suggested_mileage  

    def __lt__(self, other):
        """Break ties in heap priority queues using the unique task_id."""
        return self.task_id < other.task_id

    def calculate_urgency(self, current_mileage: int) -> int:
        """Score how overdue the task is: kilometres past due plus a date score. Higher is more urgent.

        Each day past the due date adds 10, so one day counts as ten kilometres. In the week before
        the date the score adds 0 to 6, rising as the date nears, then drops back to 0 on the due date
        itself. A date that matches no format counts as zero days overdue.
        """
        mileage_overdue = current_mileage - self.due_mileage
        days_overdue = 0
        
        for fmt in DATE_FORMATS:
            try:
                due_date_obj = datetime.strptime(self.due_date, fmt)
                days_overdue = (datetime.now() - due_date_obj).days
                break
            except ValueError:
                continue

        if days_overdue < 0:
            date_score = 0 if days_overdue < -7 else (7 + days_overdue)
        else:
            date_score = days_overdue * 10

        urgency_score = mileage_overdue + date_score
        return urgency_score

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "due_mileage": self.due_mileage,
            "due_date": self.due_date,
            "suggested_mileage": self.suggested_mileage
        }

    @classmethod
    def from_dict(cls, data: dict):
        # Older save files have no "name" field, so the description doubles as the name.
        legacy_desc = data.get("description", "MAINTENANCE")
        return cls(
            task_id=data.get("task_id"),
            name=data.get("name", legacy_desc),
            description=legacy_desc,
            due_mileage=data["due_mileage"],
            due_date=data["due_date"],
            suggested_mileage=data.get("suggested_mileage", 0)
        )


class Motorcycle:
    """One motorcycle with its service history, open tasks and remembered service intervals."""

    def __init__(self, plate_number: str, make: str, model: str, year: int, current_mileage: int):
        self.plate_number = plate_number
        self.make = make
        self.model = model
        self.year = year
        self.current_mileage = current_mileage

        self.service_history: List[ServiceRecord] = []
        self.pending_tasks: List[MaintenanceTask] = []
        
        # Task name to interval in km. Scheduling the same task again reuses it instead of asking.
        self.custom_intervals: Dict[str, int] = {}

    def add_service_record(self, record: ServiceRecord):
        self.service_history.append(record)

    def add_maintenance_task(self, task: MaintenanceTask):
        self.pending_tasks.append(task)

    def get_tasks_by_priority(self) -> List[Tuple[int, MaintenanceTask]]:
        """Return (urgency, task) pairs, most urgent first.

        Scores are negated so the min-heap pops the highest first. Ties go to the smaller task_id.
        """
        task_heap = []
        for task in self.pending_tasks:
            urgency = task.calculate_urgency(self.current_mileage)
            heapq.heappush(task_heap, (-urgency, task.task_id, task))

        urgent_tasks = []
        while task_heap:
            neg_urgency, _, task = heapq.heappop(task_heap)
            urgent_tasks.append((-neg_urgency, task))  
        return urgent_tasks

    def get_total_expenses(self) -> float:
        total = 0.0
        for record in self.service_history:
            total += record.cost
        return total

    def to_dict(self):
        return {
            "plate_number": self.plate_number,
            "make": self.make,
            "model": self.model,
            "year": self.year,
            "current_mileage": self.current_mileage,
            "service_history": [r.to_dict() for r in self.service_history],
            "pending_tasks": [t.to_dict() for t in self.pending_tasks],
            "custom_intervals": self.custom_intervals
        }

    @classmethod
    def from_dict(cls, data: dict):
        moto = cls(
            plate_number=data["plate_number"],
            make=data["make"],
            model=data["model"],
            year=data["year"],
            current_mileage=data["current_mileage"]
        )
        moto.service_history = [ServiceRecord.from_dict(r) for r in data.get("service_history", [])]
        moto.pending_tasks = [MaintenanceTask.from_dict(t) for t in data.get("pending_tasks", [])]
        moto.custom_intervals = data.get("custom_intervals", {})
        return moto


class User:
    """An account holder. Motorcycles are keyed by plate number."""

    def __init__(self, username: str, password_hash: str):
        self.username = username
        self.password_hash = password_hash
        self.motorcycles: Dict[str, Motorcycle] = {}

    def add_motorcycle(self, moto: Motorcycle):
        self.motorcycles[moto.plate_number] = moto

    def get_motorcycle(self, plate_number: str) -> Optional[Motorcycle]:
        return self.motorcycles.get(plate_number)

    def to_dict(self):
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "motorcycles": {plate: moto.to_dict() for plate, moto in self.motorcycles.items()}
        }

    @classmethod
    def from_dict(cls, data: dict):
        user = cls(
            username=data["username"],
            password_hash=data["password_hash"]
        )
        for plate, moto_data in data.get("motorcycles", {}).items():
            user.motorcycles[plate] = Motorcycle.from_dict(moto_data)
        return user


class AppState:
    """All users plus the undo stack, saved together in one JSON file."""

    def __init__(self, data_file: str = "motopulse_data.json"):
        self.data_file = data_file
        self.users: Dict[str, User] = {}
        self.action_stack = []

    def push_action(self, action: dict):
        """Record how to reverse the latest change. The stack is shared by every user and saved to disk."""
        self.action_stack.append(action)

    def pop_action(self) -> Optional[dict]:
        if self.action_stack:
            return self.action_stack.pop()
        return None

    def save_data(self):
        """Write users and the undo stack to the JSON file. A failed write prints a message and does not raise."""
        data = {
            "users": {username: user.to_dict() for username, user in self.users.items()},
            "action_stack": self.action_stack
        }
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Failed to save data: {e}")

    def load_data(self):
        """Read the JSON file if it exists. A corrupt or unexpected file is reported and the app starts empty."""
        if not os.path.exists(self.data_file):
            return
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    print("Warning: Data file has unexpected format, starting fresh.")
                    return
                # Older files are a bare users dict with no undo stack.
                if "users" in data:
                    users_data = data["users"]
                    self.action_stack = data.get("action_stack", [])
                else:
                    users_data = data
                    self.action_stack = []
                self.users = {username: User.from_dict(user_data) for username, user_data in users_data.items()}
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
            print(f"Failed to load data, starting fresh. Error: {e}")
            self.users = {}