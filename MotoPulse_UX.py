import json
import os
import heapq
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Supported date formats — updated to handle various spacing of MONTH-DD-YEAR
DATE_FORMATS = ["%B-%d-%Y", "%B - %d - %Y", "%m-%d-%Y", "%m - %d - %Y", "%B %d, %Y", "%Y-%m-%d"]


class ServiceRecord:
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
    def __init__(
        self,
        name: str,
        description: str,
        due_mileage: int,
        due_date: str,
        suggested_mileage: int = 0,
        task_id: Optional[str] = None
    ):
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
    def __init__(self, plate_number: str, make: str, model: str, year: int, current_mileage: int):
        self.plate_number = plate_number
        self.make = make
        self.model = model
        self.year = year
        self.current_mileage = current_mileage

        self.service_history: List[ServiceRecord] = []
        self.pending_tasks: List[MaintenanceTask] = []
        
        # Memory Dictionary: Remembers user-defined intervals for automatic calculation
        self.custom_intervals: Dict[str, int] = {}

    def add_service_record(self, record: ServiceRecord):
        self.service_history.append(record)

    def add_maintenance_task(self, task: MaintenanceTask):
        self.pending_tasks.append(task)

    def get_tasks_by_priority(self) -> List[Tuple[int, MaintenanceTask]]:
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
    def __init__(self, data_file: str = "motopulse_data.json"):
        self.data_file = data_file
        self.users: Dict[str, User] = {}
        self.action_stack = []

    def push_action(self, action: dict):
        self.action_stack.append(action)

    def pop_action(self) -> Optional[dict]:
        if self.action_stack:
            return self.action_stack.pop()
        return None

    def save_data(self):
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
        if not os.path.exists(self.data_file):
            return
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    print("Warning: Data file has unexpected format, starting fresh.")
                    return
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