import sys
import hashlib
from getpass import getpass
from datetime import datetime
from MotoPulse_UX import AppState, User, Motorcycle, MaintenanceTask, ServiceRecord

# ── Layout Constants ──────────────────────────────────────────────────────────
W = 38  # Layout width optimized for new menu items

# ── Maintenance Choices (Reference Constants) ─────────────────────────────────
STANDARD_TASKS = [
    {"name": "ENGINE OIL CHANGE", "desc": "DRAIN AND REPLACE ENGINE OIL", "interval": 2000},
    {"name": "GEAR OIL CHANGE [AT]", "desc": "REPLACE TRANSMISSION GEAR OIL", "interval": 6000},
    {"name": "CHAIN CLEANING & TENSION [MT]", "desc": "CLEAN, LUBRICATE, AND ADJUST CHAIN", "interval": 500},
    {"name": "OIL FILTER REPLACEMENT", "desc": "REPLACE ENGINE OIL FILTER ELEMENT", "interval": 6000},
    {"name": "AIR FILTER INSPECTION/REPLACE", "desc": "CLEAN AIR BOX OR REPLACE ELEMENT", "interval": 10000},
    {"name": "CVT CLEANING & BELT CHECK [AT]", "desc": "CLEAN CVT CASING AND INSPECT COMPONENTS", "interval": 10000},
    {"name": "SPARK PLUG REPLACEMENT", "desc": "REPLACE SPARK PLUG FOR OPTIMAL TIMING", "interval": 10000},
    {"name": "BRAKE FLUID FLUSH", "desc": "FLUSH OLD BRAKE FLUID AND BLEED SYSTEM", "interval": 20000},
    {"name": "COOLANT REPLACEMENT", "desc": "DRAIN AND REPLACE RADIATOR CORE COOLANT", "interval": 15000},
]

# ── Custom Exceptions ─────────────────────────────────────────────────────────

class CancelOperation(Exception):
    """Raised when the user intentionally cancels an operation."""
    pass


# ── Layout & Parsing Utilities ────────────────────────────────────────────────

def visual_width(text: str) -> int:
    width = 0
    for char in text:
        if char == '\ufe0f': continue
        cp = ord(char)
        if cp >= 0x1F000 or (0x2600 <= cp <= 0x27BF) or (0x1F500 <= cp <= 0x1F6FF):
            width += 2
        else:
            width += 1
    return width


def _c(text: str) -> str:
    vis_w = visual_width(text)
    if vis_w >= W: return text
    left_padding = (W - vis_w) // 2
    right_padding = W - vis_w - left_padding
    return " " * left_padding + text + " " * right_padding


def _r(prompt: str) -> str:
    return prompt


def _check_cancel(val: str):
    """Intercepts an 'X' input to cancel the current flow."""
    if val.strip().upper() == 'X':
        raise CancelOperation()


def tinput(prompt: str) -> str:
    """Enforces UPPERCASE across text inputs and listens for cancellation."""
    val = input(_r(prompt))
    _check_cancel(val)
    return val.strip().upper()


def ninput(prompt: str) -> str:
    """Standard input for numerical/raw data that listens for cancellation."""
    val = input(_r(prompt))
    _check_cancel(val)
    return val.strip()


def standardize_date(date_input: str) -> str:
    """Intelligent date parser: Converts any date to 'MONTH-DD-YEAR' format."""
    if not date_input or date_input.upper() == "N/A" or date_input.upper() == "X":
        return "N/A"
        
    clean = date_input.replace(',', ' ').replace('.', ' ').strip()
    clean = ' '.join(clean.split())
    
    upper_clean = clean.upper()
    if "SEPT " in upper_clean or "SEPT-" in upper_clean:
        clean = upper_clean.replace("SEPT", "SEP")
        
    formats = [
        "%B %d %Y", "%b %d %Y", "%m %d %Y",
        "%B-%d-%Y", "%b-%d-%Y", "%m-%d-%Y",
        "%Y %m %d", "%Y-%m-%d", "%d %B %Y",
        "%m/%d/%Y", "%d/%m/%Y"
    ]
    
    for fmt in formats:
        try:
            parsed = datetime.strptime(clean, fmt)
            return parsed.strftime("%B-%d-%Y").upper()
        except ValueError:
            continue
            
    return date_input.upper()


# ── Password Utility ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ── CLI Application ───────────────────────────────────────────────────────────

class MotoPulseCLI:
    def __init__(self):
        self.app_state = AppState()
        self.app_state.load_data()
        self.current_user = None

    def display_welcome(self):
        print("\n" + "═" * W)
        print(_c("🏍️  MOTOPULSE  🏍️"))
        print(_c("MOTORCYCLE MAINTENANCE TRACKER"))
        print(_c("YOUR RIDE, ALWAYS ON TIME."))
        print("═" * W)

    def main_menu(self):
        while True:
            if not self.current_user:
                self.auth_menu()
            else:
                self.user_dashboard()

    # ── Authentication ────────────────────────────────────────────────────────

    def auth_menu(self):
        print("\n" + "─" * W)
        print(_c("🔐  AUTHENTICATION MENU  🔐"))
        print("─" * W)
        print("1.  🔐  LOGIN")
        print("2.  📝  REGISTER")
        print("3.  🔑  FORGOT PASSWORD")
        print("4.  🚪  EXIT")
        print("─" * W)

        choice = input(_r("Select an option (1-4): ")).strip()

        if choice == '1':
            self.login()
        elif choice == '2':
            self.register()
        elif choice == '3':
            self.forgot_password()
        elif choice == '4':
            print("THANK YOU FOR USING MOTOPULSE. RIDE SAFE! 🏍️")
            self.app_state.save_data()
            sys.exit(0)
        else:
            print("❌  INVALID OPTION. PLEASE TRY AGAIN.")

    def login(self):
        print("\n" + "─" * W)
        print(_c("🔐  LOGIN"))
        print("─" * W)
        username = input(_r("Username: ")).strip()
        password = getpass(_r("Password: "))

        user = self.app_state.users.get(username)
        if user and user.password_hash == hash_password(password):
            print(f"✅  LOGIN SUCCESSFUL! WELCOME BACK, {username.upper()}.")
            self.current_user = user
        else:
            print("❌  ERROR: INVALID USERNAME OR PASSWORD.")

    def register(self):
        print("\n" + "─" * W)
        print(_c("📝  REGISTER"))
        print("─" * W)
        username = input(_r("Choose a username: ")).strip()
        if not username:
            print("❌  USERNAME CANNOT BE EMPTY.")
            return

        if username in self.app_state.users:
            print("❌  ERROR: USERNAME ALREADY EXISTS.")
            return

        password = getpass(_r("Choose a password: "))
        if not password:
            print("❌  PASSWORD CANNOT BE EMPTY.")
            return

        confirm_password = getpass(_r("Confirm password: "))
        if password != confirm_password:
            print("❌  ERROR: PASSWORDS DO NOT MATCH.")
            return

        new_user = User(username=username, password_hash=hash_password(password))
        self.app_state.users[username] = new_user
        self.app_state.save_data()
        print(f"✅  REGISTRATION SUCCESSFUL! YOU CAN NOW LOG IN, {username.upper()}.")

    def forgot_password(self):
        print("\n" + "─" * W)
        print(_c("🔑  FORGOT PASSWORD"))
        print("─" * W)
        username = input(_r("Enter your username: ")).strip()

        user = self.app_state.users.get(username)
        if not user:
            print("❌  ERROR: USERNAME NOT FOUND.")
            return

        new_password = getpass(_r("Enter new password: "))
        if not new_password:
            print("❌  PASSWORD CANNOT BE EMPTY.")
            return

        confirm_password = getpass(_r("Confirm new password: "))
        if new_password != confirm_password:
            print("❌  ERROR: PASSWORDS DO NOT MATCH.")
            return

        user.password_hash = hash_password(new_password)
        self.app_state.save_data()
        print("✅  PASSWORD UPDATED SUCCESSFULLY! PLEASE LOG IN.")

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def user_dashboard(self):
        print("\n" + "═" * W)
        print(_c(f"📊  {self.current_user.username.upper()}'S DASHBOARD  📊"))
        print("═" * W)
        print("1.  🏍️   ADD A MOTORCYCLE")
        print("2.  📋  VIEW MOTORCYCLES")
        print("3.  🔧  MANAGE A MOTORCYCLE")
        print("4.  🚪  LOGOUT")
        print("U.  ↩️   UNDO LAST ACTION")
        print("─" * W)

        choice = input(_r("Select an option (1-4, U): ")).strip().lower()

        try:
            if choice == '1':
                self.add_motorcycle()
            elif choice == '2':
                self.view_motorcycles()
            elif choice == '3':
                self.select_motorcycle()
            elif choice == '4':
                self.current_user = None
                print("✅  LOGGED OUT SUCCESSFULLY.")
            elif choice == 'u':
                self.undo_last_action()
            else:
                print("❌  INVALID OPTION. PLEASE TRY AGAIN.")
        except CancelOperation:
            print("\n🚫  ACTION CANCELLED. RETURNING TO DASHBOARD...")

    # ── Motorcycle Management ─────────────────────────────────────────────────

    def add_motorcycle(self):
        print("\n" + "─" * W)
        print(_c("🏍️   ADD A MOTORCYCLE"))
        print(_c("(Type 'X' to cancel)"))
        print("─" * W)
        
        plate_number = tinput("Plate Number: ")
        if not plate_number:
            print("❌  ERROR: PLATE NUMBER CANNOT BE EMPTY.")
            return

        if self.current_user.get_motorcycle(plate_number):
            print(f"❌  ERROR: MOTORCYCLE '{plate_number}' ALREADY REGISTERED.")
            return

        make  = tinput("MAKE/BRAND: ")
        model = tinput("Model: ")

        try:
            year            = int(ninput("Year: "))
            current_mileage = int(ninput("Current Mileage (km): "))
        except ValueError:
            print("❌  ERROR: YEAR AND MILEAGE MUST BE VALID NUMBERS.")
            return

        new_moto = Motorcycle(
            plate_number=plate_number,
            make=make,
            model=model,
            year=year,
            current_mileage=current_mileage
        )

        self.current_user.add_motorcycle(new_moto)
        self.app_state.save_data()

        undo_action = {
            "type": "add_motorcycle",
            "username": self.current_user.username,
            "plate_number": plate_number
        }
        self.app_state.push_action(undo_action)

        print(f"✅  '{make} {model}' ({plate_number}) HAS BEEN ADDED!")

    def view_motorcycles(self):
        print("\n" + "─" * W)
        print(_c("📋  YOUR MOTORCYCLES"))
        print("─" * W)
        if not self.current_user.motorcycles:
            print("YOU HAVE NO MOTORCYCLES REGISTERED YET.")
            input(_r("Press Enter to continue..."))
            return

        for plate, moto in self.current_user.motorcycles.items():
            print(f"🏍️   {moto.make} {moto.model} ({moto.year})  |  PLATE: {plate}  |  MILEAGE: {moto.current_mileage:,} KM")
        input(_r("Press Enter to continue..."))

    def select_motorcycle(self):
        if not self.current_user.motorcycles:
            print("❌  YOU HAVE NO MOTORCYCLES. ADD ONE FIRST.")
            return

        print("\n" + "─" * W)
        print(_c("🔧  SELECT A MOTORCYCLE"))
        print(_c("(Type 'X' to cancel)"))
        print("─" * W)
        for plate, moto in self.current_user.motorcycles.items():
            print(f"🏍️   {moto.make} {moto.model}  |  PLATE: {plate}")

        plate = tinput("Enter Plate Number: ")
        moto  = self.current_user.get_motorcycle(plate)
        if moto:
            self.manage_motorcycle(moto)
        else:
            print("❌  MOTORCYCLE NOT FOUND.")

    def manage_motorcycle(self, moto: Motorcycle):
        while True:
            urgent_tasks = moto.get_tasks_by_priority()

            print("\n" + "═" * W)
            if urgent_tasks and urgent_tasks[0][0] > 0:
                print(_c("⚠️  URGENT MAINTENANCE REQUIRED  ⚠️"))
                print(_c("CHECK YOUR PRIORITIZED ALERTS NOW!"))
                print("─" * W)

            print(_c(f"🏍️   {moto.make} {moto.model}  ({moto.plate_number})"))
            print(_c(f"📏  MILEAGE: {moto.current_mileage:,} KM   |   💰  EXPENSES: ₱{moto.get_total_expenses():,.2f}"))
            print("─" * W)
            print("1.  📏  LOG CURRENT MILEAGE")
            print("2.  🛠️   SCHEDULE MAINTENANCE TASK")
            print("3.  🔔  VIEW PRIORITIZED ALERTS")
            print("4.  ✅  LOG COMPLETED MAINTENANCE")
            print("5.  ✏️   EDIT MOTORCYCLE INFO")
            print("6.  📋  VIEW LOGGED MAINTENANCE HISTORY")
            print("7.  ⚙️   MANAGE TASK INTERVALS")
            print("8.  🔙  BACK TO DASHBOARD")
            print("U.  ↩️   UNDO LAST ACTION")
            print("─" * W)

            choice = input(_r("Select an option (1-8, U): ")).strip().lower()

            try:
                if choice == '1':
                    self.log_mileage(moto)
                elif choice == '2':
                    self.schedule_task(moto)
                elif choice == '3':
                    self.view_alerts(moto)
                elif choice == '4':
                    self.log_completed_maintenance(moto)
                elif choice == '5':
                    self.edit_motorcycle(moto)
                elif choice == '6':
                    self.view_logged_maintenance(moto)
                elif choice == '7':
                    self.manage_task_intervals(moto)
                elif choice == '8':
                    break
                elif choice == 'u':
                    self.undo_last_action()
                else:
                    print("❌  INVALID OPTION.")
            except CancelOperation:
                print("\n🚫  ACTION CANCELLED. RETURNING TO MENU...")

    # ── Operational Dashboards ────────────────────────────────────────────────

    def edit_motorcycle(self, moto: Motorcycle):
        print("\n" + "─" * W)
        print(_c("✏️  EDIT MOTORCYCLE INFO"))
        print(_c("(Type 'X' to cancel)"))
        print("─" * W)
        print(f"CURRENT: {moto.make} {moto.model} ({moto.year})")
        print("LEAVE BLANK TO KEEP THE CURRENT VALUE.")
        print("─" * W)

        old_make  = moto.make
        old_model = moto.model
        old_year  = moto.year

        new_make = tinput(f"New MAKE/BRAND [{moto.make}]: ")
        if new_make: moto.make = new_make

        new_model = tinput(f"New Model [{moto.model}]: ")
        if new_model: moto.model = new_model

        year_str = ninput(f"New Year [{moto.year}]: ")
        if year_str:
            try: moto.year = int(year_str)
            except ValueError: print("❌  INVALID YEAR FORMAT. YEAR NOT CHANGED.")

        self.app_state.save_data()

        undo_action = {
            "type": "edit_motorcycle",
            "username": self.current_user.username,
            "plate_number": moto.plate_number,
            "old_make": old_make,
            "old_model": old_model,
            "old_year": old_year
        }
        self.app_state.push_action(undo_action)

        print(f"✅  MOTORCYCLE UPDATED TO: {moto.make} {moto.model} ({moto.year})")

    def view_logged_maintenance(self, moto: Motorcycle):
        print("\n" + "─" * W)
        print(_c("📋  VIEW LOGGED MAINTENANCE HISTORY"))
        print("─" * W)
        if not moto.service_history:
            print("❌  NO MAINTENANCE HISTORY FOUND.")
            input(_r("Press Enter to continue..."))
            return

        for i, record in enumerate(moto.service_history, 1):
            print(f"{i}. {record.description} | {record.date} | ₱{record.cost:,.2f}")
        print("─" * W)
        print(f"💰  TOTAL ACCUMULATED EXPENSES: ₱{moto.get_total_expenses():,.2f}")
        print("─" * W)
        input(_r("Press Enter to return..."))

    def manage_task_intervals(self, moto: Motorcycle):
        print("\n" + "─" * W)
        print(_c("⚙️  MANAGE TASK INTERVALS"))
        print(_c("(Type 'X' to cancel)"))
        print("─" * W)
        if not moto.custom_intervals:
            print("❌  NO SAVED INTERVALS YET.")
            print("SCHEDULE A TASK TO AUTOMATICALLY SAVE ITS INTERVAL.")
            input(_r("Press Enter to continue..."))
            return
        
        intervals = list(moto.custom_intervals.items())
        for i, (name, interval) in enumerate(intervals, 1):
            print(f"{i}. {name} ({interval:,} KM)")
        print("─" * W)
        
        try:
            choice = int(ninput(f"Select task interval to edit (1-{len(intervals)}): "))
        except ValueError:
            print("❌  INVALID SELECTION.")
            return
            
        if not (1 <= choice <= len(intervals)):
            print("❌  SELECTION OUT OF RANGE.")
            return
            
        selected_name = intervals[choice - 1][0]
        current_interval = intervals[choice - 1][1]
        
        print(f"\nEDITING INTERVAL FOR: {selected_name}")
        try:
            new_interval_str = ninput(f"New Interval [{current_interval:,} KM]: ")
            if new_interval_str:
                new_interval = int(new_interval_str.replace(',', ''))
                
                old_interval = current_interval
                moto.custom_intervals[selected_name] = new_interval
                self.app_state.save_data()
                
                undo_action = {
                    "type": "edit_interval",
                    "username": self.current_user.username,
                    "plate_number": moto.plate_number,
                    "task_name": selected_name,
                    "old_interval": old_interval
                }
                self.app_state.push_action(undo_action)
                print(f"✅  INTERVAL FOR '{selected_name}' UPDATED TO {new_interval:,} KM.")
        except ValueError:
            print("❌  INVALID INTERVAL FORMAT.")

    # ── Core Operations ───────────────────────────────────────────────────────

    def log_mileage(self, moto: Motorcycle):
        print("\n" + "─" * W)
        print(_c("📏  LOG CURRENT MILEAGE"))
        print(_c("(Type 'X' to cancel)"))
        print("─" * W)
        try:
            new_mileage = int(ninput("Enter new current mileage (km): "))
            if new_mileage >= moto.current_mileage:
                old_mileage = moto.current_mileage
                moto.current_mileage = new_mileage
                self.app_state.save_data()

                undo_action = {
                    "type": "update_mileage",
                    "username": self.current_user.username,
                    "plate_number": moto.plate_number,
                    "old_mileage": old_mileage
                }
                self.app_state.push_action(undo_action)

                print(f"✅  MILEAGE UPDATED TO {new_mileage:,} KM.")
            else:
                print("❌  NEW MILEAGE MUST BE GREATER OR EQUAL TO CURRENT MILEAGE.")
        except ValueError:
            print("❌  INVALID INPUT. MILEAGE MUST BE A NUMBER.")

    def schedule_task(self, moto: Motorcycle):
        print("\n" + "─" * W)
        print(_c("🛠️   SCHEDULE MAINTENANCE TASK"))
        print(_c("(Type 'X' to cancel)"))
        print("─" * W)

        for i, task in enumerate(STANDARD_TASKS, 1):
            print(f"{i}. {task['name']}")
        
        custom_idx = len(STANDARD_TASKS) + 1
        print(f"{custom_idx}. ADD CUSTOM TASK")
        print("─" * W)

        try:
            choice = int(ninput(f"Select option (1-{custom_idx}): "))
        except ValueError:
            print("❌  INVALID INPUT. ENTER A NUMBER.")
            return

        if not (1 <= choice <= custom_idx):
            print("❌  SELECTION OUT OF RANGE.")
            return

        # Handle Naming based on selection
        if choice == custom_idx:
            name = tinput("Maintenance Name: ")
            description = tinput("Detailed Description: ")
            print(f"\nSELECTED: {name}")
        else:
            selected_task = STANDARD_TASKS[choice - 1]
            name = selected_task["name"]
            description = selected_task["desc"]
            print(f"\nSELECTED: {name}")

        # ── Automated Memory Calculation Logic ──
        if name in moto.custom_intervals:
            suggested_mileage = moto.custom_intervals[name]
            print(f"🔄  AUTO-APPLYING SAVED INTERVAL: {suggested_mileage:,} KM")
            due_mileage = moto.current_mileage + suggested_mileage
            print(f"📍  AUTO-CALCULATED DUE MILEAGE: {due_mileage:,} KM")
        else:
            try:
                suggested_mileage = int(ninput("Service Interval: "))
                due_mileage = int(ninput("Due at Mileage: "))
                moto.custom_intervals[name] = suggested_mileage
            except ValueError:
                print("❌  INVALID INPUT. MILEAGE MUST BE A NUMBER.")
                return

        raw_date = ninput("DUE DATE [MONTH-DD-YEAR]: ")
        due_date = standardize_date(raw_date)

        task = MaintenanceTask(
            name=name,
            description=description,
            suggested_mileage=suggested_mileage,
            due_mileage=due_mileage,
            due_date=due_date
        )
        moto.add_maintenance_task(task)
        self.app_state.save_data()

        undo_action = {
            "type": "add_task",
            "username": self.current_user.username,
            "plate_number": moto.plate_number,
            "task_id": task.task_id
        }
        self.app_state.push_action(undo_action)

        print(f"✅  '{name}' SCHEDULED SUCCESSFULLY!")

    def view_alerts(self, moto: Motorcycle):
        print("\n" + "─" * W)
        print(_c("🔔  PRIORITIZED ALERTS"))
        print("─" * W)
        urgent_tasks = moto.get_tasks_by_priority()

        if not urgent_tasks:
            print("✅  NO PENDING MAINTENANCE TASKS.")
            input(_r("Press Enter to continue..."))
            return

        print("TASKS ORDERED BY URGENCY:")
        for score, task in urgent_tasks:
            status       = "⚠️  OVERDUE" if score > 0 else "🕐 UPCOMING"
            interval_str = f"{task.suggested_mileage:,} KM" if task.suggested_mileage > 0 else "N/A"
            print("─" * W)
            print(f"{status}   [URGENCY SCORE: {score}]")
            print(f"🔧  {task.name}")
            print(f"📝  {task.description}")
            print(f"📅  DUE: {task.due_date}   |   📏  DUE AT: {task.due_mileage:,} KM")
            print(f"🔄  SERVICE INTERVAL: {interval_str}")
        print("─" * W)
        input(_r("Press Enter to continue..."))

    def log_completed_maintenance(self, moto: Motorcycle):
        print("\n" + "─" * W)
        print(_c("✅  LOG COMPLETED MAINTENANCE"))
        print(_c("(Type 'X' to cancel)"))
        print("─" * W)

        urgent_tasks = moto.get_tasks_by_priority()
        if not urgent_tasks:
            print("❌  NO PENDING TASKS FOUND. SCHEDULE A TASK FIRST.")
            input(_r("Press Enter to continue..."))
            return

        print("SELECT THE TASK YOU HAVE COMPLETED:")
        print("─" * W)
        for i, (score, task) in enumerate(urgent_tasks):
            print(f"{i + 1}.  🔧  {task.name}  (DUE: {task.due_date} OR {task.due_mileage:,} KM)")
        print("─" * W)

        try:
            choice = int(ninput(f"Select a task (1-{len(urgent_tasks)}): "))
        except ValueError:
            print("❌  INVALID SELECTION.")
            return

        if not (1 <= choice <= len(urgent_tasks)):
            print("❌  INVALID SELECTION.")
            return

        completed_task = urgent_tasks[choice - 1][1]

        try:
            cost = float(ninput("Total Cost (₱): "))
        except ValueError:
            print("❌  INVALID COST FORMAT.")
            return

        raw_date = ninput("DUE DATE [MONTH-DD-YEAR]: ")
        date = standardize_date(raw_date)

        completed_task_dict = completed_task.to_dict()
        moto.pending_tasks = [t for t in moto.pending_tasks if t.task_id != completed_task.task_id]

        record = ServiceRecord(
            date=date,
            mileage=moto.current_mileage,
            cost=cost,
            description=completed_task.name
        )
        moto.add_service_record(record)
        self.app_state.save_data()

        undo_action = {
            "type": "log_maintenance",
            "username": self.current_user.username,
            "plate_number": moto.plate_number,
            "completed_task_dict": completed_task_dict
        }
        self.app_state.push_action(undo_action)

        print(f"✅  MAINTENANCE LOGGED! TOTAL VEHICLE EXPENSES: ₱{moto.get_total_expenses():,.2f}")

    # ── Undo ──────────────────────────────────────────────────────────────────

    def undo_last_action(self):
        action = self.app_state.pop_action()
        if not action:
            print("❌  NOTHING TO UNDO.")
            input(_r("Press Enter to continue..."))
            return

        print(f"↩️   UNDOING LAST ACTION: {action['type'].upper()}...")
        user = self.app_state.users.get(action['username'])
        if not user:
            print("❌  ERROR: USER FOR THIS ACTION NO LONGER EXISTS.")
            return

        if action['type'] == 'add_motorcycle':
            plate = action['plate_number']
            if plate in user.motorcycles:
                del user.motorcycles[plate]
                print(f"✅  MOTORCYCLE {plate} REGISTRATION UNDONE.")

        elif action['type'] == 'update_mileage':
            moto = user.get_motorcycle(action['plate_number'])
            if moto:
                moto.current_mileage = action['old_mileage']
                print(f"✅  MILEAGE REVERTED TO {moto.current_mileage:,} KM.")

        elif action['type'] == 'add_task':
            moto = user.get_motorcycle(action['plate_number'])
            if moto:
                moto.pending_tasks = [t for t in moto.pending_tasks if t.task_id != action['task_id']]
                print("✅  SCHEDULED TASK REMOVED.")

        elif action['type'] == 'log_maintenance':
            moto = user.get_motorcycle(action['plate_number'])
            if moto:
                if moto.service_history:
                    moto.service_history.pop()
                if action.get('completed_task_dict'):
                    task = MaintenanceTask.from_dict(action['completed_task_dict'])
                    moto.pending_tasks.append(task)
                print("✅  MAINTENANCE LOG REVERTED.")

        elif action['type'] == 'edit_motorcycle':
            moto = user.get_motorcycle(action['plate_number'])
            if moto:
                moto.make  = action['old_make']
                moto.model = action['old_model']
                moto.year  = action['old_year']
                print(f"✅  MOTORCYCLE INFO REVERTED TO: {moto.make} {moto.model} ({moto.year}).")

        elif action['type'] == 'edit_interval':
            moto = user.get_motorcycle(action['plate_number'])
            if moto:
                moto.custom_intervals[action['task_name']] = action['old_interval']
                print(f"✅  INTERVAL FOR '{action['task_name']}' REVERTED.")

        self.app_state.save_data()
        input(_r("Press Enter to continue..."))


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli = MotoPulseCLI()
    cli.display_welcome()
    try:
        cli.main_menu()
    except KeyboardInterrupt:
        print("\n🏍️  EXITING MOTOPULSE... RIDE SAFE!")
        cli.app_state.save_data()
        sys.exit(0)