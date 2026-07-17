# Notenverwaltung (Student Grade Tracker) Study Guide

This document is your learning companion for the Student Grade Tracker homework project. It outlines the project roadmap, the structural design, the tools used, and key Python concepts to refresh your skills.

---

## 1. Project Directory Structure (The "Source Layout")

We organize our code using the professional Python **source layout**:

```text
grade_tracker/
├── pyproject.toml              # UV configuration & project dependencies
├── README.md                   # Quick description of the application
├── STUDY_GUIDE.md              # This file (your learning reference)
├── src/                        # Isolated source folder for clean builds
│   └── notenverwaltung/        # The root package of our code
│       ├── __init__.py         # Makes 'notenverwaltung' a package
│       ├── exceptions.py       # Custom exception definitions
│       ├── gradebook.py        # Central business logic and statistics
│       ├── models/             # Sub-package containing data structures
│       │   ├── __init__.py
│       │   ├── student.py      # Student representation
│       │   ├── course.py       # Course representation
│       │   └── grade.py        # Grade representation (scores, letter grades)
│       ├── storage.py          # Data persistence layer (InMemory & SQLite stores)
│       ├── reports.py          # Plaintext and CSV report generators
│       └── app.py              # Gradio web interface
└── tests/                      # Testing package
    ├── test_student.py         # Tests student model validation
    ├── test_course.py          # Tests course model validation
    ├── test_grade.py           # Tests grade scores and limits
    ├── test_gradebook.py       # Tests business logic and SQLite storage
    └── test_reports.py         # Tests plain text & CSV report formatting
```

### Why Do We Separate Files Like This?
* **Separation of Concerns (SoC)**: We isolate different jobs. Our data models (`models/`) don't care how they are saved. Our database code (`storage/`) doesn't care how reports are formatted. This makes the code modular, readable, and easy to maintain.
* **Testing isolation**: Keeping tests in `/tests` separate from production code in `/src` prevents shipping test files to production.

---

## 2. Tooling and Commands

### UV (Modern Python Package Manager)
`uv` replaces legacy tools (`pip`, `virtualenv`, `pip-tools`) with a single high-performance package manager written in Rust.

* **Initialize a project**: `uv init --lib`
* **Create a virtual environment**: Automatically managed by `uv`. It creates a `.venv` directory containing the isolated Python interpreter.
* **Add dependencies**:
  * `uv add gradio` (Adds Gradio to the project runtime)
  * `uv add --dev pytest` (Adds Pytest to the development environment)
* **Run commands inside the environment**: `uv run <command>` (e.g., `uv run pytest`). This ensures python runs with the exact packages listed in `pyproject.toml`.

### Pytest (Testing Framework)
`pytest` is the standard for Python unit testing.
* It searches for files matching `test_*.py`.
* Inside those files, it runs any function starting with `test_`.
* **Assertions**: Standard python `assert` statements are used to verify results.
* **Exception Testing**: We test if error paths are triggered correctly using `with pytest.raises(ValueError):`.

---

## 3. Core Python OOP Concepts Used

### A. Dataclasses (`@dataclass`)
In standard Python, a class needs a lot of boilerplate code:
```python
class Student:
    def __init__(self, student_id, first_name, last_name, email):
        self.student_id = student_id
        self.first_name = first_name
        # ... and so on
```
With the `@dataclass` decorator, Python generates the `__init__`, `__repr__` (printable string), and `__eq__` (equality checks) for you:
```python
from dataclasses import dataclass

@dataclass
class Student:
    student_id: str
    first_name: str
    last_name: str
    email: str
```

### B. Post-Initialization (`__post_init__`)
Since `@dataclass` automatically generates the constructor (`__init__`), how do we validate the inputs? Python provides a special hook method called `__post_init__` that runs immediately *after* the fields are set:
```python
def __post_init__(self):
    if not self.student_id.strip():
        raise ValueError("ID cannot be empty")
```

### C. Properties (`@property`)
Properties turn methods into read-only attributes. They allow us to compute values on the fly without using parenthesis:
```python
@property
def full_name(self) -> str:
    return f"{self.first_name} {self.last_name}"

# Usage:
# print(student.full_name)  # NO parenthesis!
```

---

## 4. Phase-by-Phase Roadmap

### Phase 1: Core Models (TDD)
Build and validate `Student`, `Course`, and `Grade` using `pytest`.

### Phase 2: Registry & Aggregation (GradeBook)
Implement storage containers for our models, calculate grade averages, find at-risk students, and search using Regex (`re`).

### Phase 3: Serialization & Exceptions
Develop save/load routines in JSON and a custom CSV parser with input validation, defining our own Exception classes (e.g., `StudentNotFoundError`).

### Phase 4: Database Storage
Introduce the Repository Pattern using an Abstract Base Class (`GradeStore`) and implement SQLite storage (`sqlite3`) so data persists permanently on disk.

### Phase 5: UI & Packaging
Build a web interface using Gradio and wrap the application as a professional, installable Python library package.

---

## 5. Advanced Python & Database Concepts (Lessons Learned)

### A. Alternative Constructors (`@classmethod`)
When importing data from JSON or dictionaries, we want to create objects directly from raw data. We do this using `@classmethod`, which acts as an **alternative constructor**:

```python
@classmethod
def from_dict(cls, data: dict) -> "Student":
    # cls refers to the class itself (e.g. Student)
    return cls(
        student_id=data["student_id"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=data["email"]
    )
```
* **Key Point**: Using `"Student"` in quotes as a return type hint is called a **forward reference**. It tells Python that the class name exists, even though the class declaration is not yet finished.

### B. SQLite Connection-Level PRAGMA Settings
When working with relational databases, **Foreign Key Constraints** ensure data integrity (e.g. you cannot record a grade for a student ID that does not exist).
* **SQLite Trap**: In SQLite, foreign key enforcement is **disabled by default** to preserve backward compatibility.
* **The Fix**: You must run the command `PRAGMA foreign_keys = ON;` **every single time** you open a database connection. It is a connection-level configuration and does not persist when the connection is closed.

```python
import sqlite3

# This must be run on every new connection
conn = sqlite3.connect("grades.db")
conn.execute("PRAGMA foreign_keys = ON;")
```

### C. Dependency Injection (DI)
Instead of forcing our `GradeBook` to talk directly to SQLite, we inject the storage backend in the constructor. This is called **Dependency Injection**:

```python
class GradeBook:
    def __init__(self, store: GradeStore = None):
        # We can pass an InMemoryGradeStore (for testing)
        # or a SqliteGradeStore (for real use)
        self.store = store or InMemoryGradeStore()
```
* **Why?** It makes testing incredibly easy. In our tests, we can use a temporary, fast in-memory store. In production, we swap it out for a SQLite database store without changing any of the business logic!

---

## 6. Output Formatting & String Syntax

### String Format Specifiers
When writing text-based reports or formatting tables in the terminal, we want columns to align nicely regardless of their content length. We use Python's formatting syntax:

* **Syntax**: `{value:<width}`
  * `<` means **left-align**.
  * `width` is the total character spaces allocated for that field.

```python
# Format table headers
print(f"{'Student ID':<12} {'Name':<25} {'Email':<30}")
# Output:
# Student ID   Name                      Email                         
```

* **⚠️ Syntax Trap (No spaces allowed inside formatting)**:
  * `{row[0]:< 20}` ❌ Will raise a `ValueError` because spaces are not allowed inside the formatting block.
  * `{row[0]:<20}`  ✅ Correct.

---

## 7. Interactive UI Development (Gradio 6)

### A. Unified Application Updates
When building reactive dashboards, changes in one tab (e.g., adding a student) must show up in all other tabs (e.g., in the dropdown selector or statistics table).
We achieve this in Gradio by returning a **tuple of updates** for all elements in our callback function:

```python
def update_all_ui(message):
    return (
        message, 
        get_overall_stats(), 
        get_all_students_table(),
        gr.update(choices=get_student_choices()) # updates dropdown values
    )
```

### B. Modifying component properties dynamically (`gr.update()`)
To update a component's values, configuration, or choices inside a callback, we use `gr.update()`.
* To update choices in a dropdown: `gr.update(choices=["S001", "S002"])`
* To keep a component's state unchanged (e.g., during error handling): `gr.update()`

---

## 8. Python Module Executions (`-m` flag)

When running the application, we use the command:
```powershell
uv run python -m notenverwaltung.app
```

* **`uv run`**: Ensures the command runs inside the project's virtual environment `.venv` with our project packages (Gradio, Pandas, etc.).
* **`-m`**: Tells Python to run the target as a **module** (resolving from the base package directory) rather than running a raw script file directly.
* **Why not run `python src/notenverwaltung/app.py`?**:
  * Running a file directly changes Python's import directory to `src/notenverwaltung`. When the code tries to import `from notenverwaltung.gradebook import GradeBook`, Python fails with `ModuleNotFoundError`.
  * Using `-m notenverwaltung.app` keeps the root folder in Python's search path, letting it find the `notenverwaltung` package and resolve all imports perfectly.

---

## 9. Abstract Base Classes & Custom Exceptions

### A. Interfaces & Abstract Base Classes (ABCs)
In Python, an interface contract is defined using Abstract Base Classes. This ensures any class inheriting from it **must** implement specific methods, establishing a common contract across multiple backends.

```python
from abc import ABC, abstractmethod

class GradeStore(ABC):
    @abstractmethod
    def save_student(self, student) -> None:
        """Must be overridden by subclasses (e.g., SqliteGradeStore)"""
        pass
```
* **Why?** It ensures that `SqliteGradeStore` and `InMemoryGradeStore` have the exact same method names and signatures. Our controller (`GradeBook`) can then call `.save_student(...)` without needing to know *how* or *where* the data is being stored.

### B. Custom Exception Classes
Python allows us to create specific exceptions for targeted error handling. We inherit from Python's built-in `Exception` or `ValueError`:

```python
class StudentNotFoundError(ValueError):
    """Raised when looking up a student ID that does not exist."""
    pass
```
* **Why?** It allows clean control flow. In our backend code, we `raise StudentNotFoundError("S001")`. In our Gradio UI frontend, we can write a targeted catch block:
```python
try:
    gb.record_grade(student_id, course_id, score)
except StudentNotFoundError:
    return "❌ Error: Student ID not found in database!"
```

---

## 10. Data Searching (Regex) & SQL bindings

### A. Regular Expression Fuzzy Searching (`re` module)
When searching for records, users might type a partial name, lowercase letters, or a domain. We use Python's **`re`** library for flexible matching:

```python
import re

# Match anywhere in the string, ignoring upper/lowercase differences
if re.search(query, student.full_name, re.IGNORECASE):
    # Match found!
```
* `re.search(pattern, text)` checks if `pattern` is located anywhere inside `text`.
* `re.IGNORECASE` makes the search case-insensitive (e.g. "anna" matches "Anna").

### B. SQL Parameter Bindings & Single-Element Tuples
When executing SQL statements in Python using `sqlite3`, we use parameter bindings (`?`) to prevent **SQL Injection attacks**.
* **Tuple Syntax Gotcha**: Python's `execute()` method expects bindings to be passed as a sequence (like a list or tuple). If you are passing a **single** value, you must write it as a tuple with a trailing comma: `(value,)`.

```python
# ❌ INCORRECT: Python treats (student_id) as grouped parentheses, not a tuple!
cursor.execute("SELECT * FROM students WHERE id = ?", (student_id))

# ✅ CORRECT: The trailing comma creates a single-element tuple
cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
```

---

## 11. Testing & Test Isolation (Pytest)

### A. Reusable Test Setups (`@pytest.fixture`)
When writing tests, we often need a pre-configured database or gradebook filled with sample data. We use **fixtures** to set up this data once and inject it into our test functions:

```python
import pytest

@pytest.fixture
def sample_gradebook():
    gb = GradeBook()
    # Add a default student and course for testing
    gb.add_student(Student("S001", "Anna", "Schmidt", "anna@example.com"))
    return gb

# The fixture name is passed as an argument to the test function
def test_record_grade(sample_gradebook):
    # sample_gradebook is automatically injected here!
    sample_gradebook.record_grade("S001", "CS101", 85.0)
    assert len(sample_gradebook.grades) == 1
```

### B. Testing for Errors (`pytest.raises`)
Testing that your code **correctly throws errors** on invalid input is just as important as testing the success path:

```python
def test_invalid_grade_range():
    # Verify that setting a grade of 150 (out of 100 max) raises a ValueError
    with pytest.raises(ValueError):
        Grade(score=150.0, max_grade=100.0)
```

### C. Temporary Directory Isolation (`tmp_path`)
When testing code that reads or writes files (like database storage or CSV export), we must avoid writing real files to our workspace because it leaves garbage behind. 
Pytest provides a built-in fixture called **`tmp_path`** which creates a clean, temporary folder that is deleted automatically after the test finishes.

```python
def test_sqlite_persistence(tmp_path):
    # Create a temporary database file path
    db_file = tmp_path / "test_grades.db"
    
    # Run database operations on the temporary file
    store = SqliteGradeStore(str(db_file))
    store.save_student(Student("S001", "Anna", "Schmidt", "anna@example.com"))
    
    # Assert that the data was written and can be read back
    assert len(store.get_all_students()) == 1
```
