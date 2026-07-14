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
│       ├── storage/            # Database and in-memory storage implementations
│       │   ├── __init__.py
│       │   ├── base.py         # GradeStore Abstract Base Class
│       │   ├── memory.py       # Dict-based mock store
│       │   └── sqlite.py       # SQLite database store
│       ├── reports/            # Output generation
│       │   ├── __init__.py
│       │   ├── base.py         # ReportGenerator (ABC)
│       │   ├── text.py         # Text report formatter
│       │   └── csv.py          # CSV report formatter
│       └── app.py              # Gradio web interface
└── tests/                      # Testing package
    ├── __init__.py
    ├── test_student.py
    ├── test_course.py
    ├── test_grade.py
    ├── test_gradebook.py
    ├── test_storage.py
    └── test_reports.py
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
