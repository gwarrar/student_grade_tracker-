from dataclasses import dataclass

# The @dataclass decorator automatically writes standard methods for us, 
# such as __init__() (constructor) and __repr__() (how it displays when printed).
@dataclass
class Student:
    student_id: str
    first_name: str
    last_name: str
    email:str

    
    # __post_init__ is a special hook method called automatically after __init__ completes.
    # We use it to validate our data fields.
    def __post_init__(self):

        # .strip() removes leading and trailing whitespaces. 
        # If the ID, first name, or last name are empty strings, raise a ValueError.
        if not self.student_id.strip():
            raise ValueError("Student ID connot be empty.")

        if not self.first_name.strip():
            raise ValueError("First name cannot be empty")

        if not self.last_name.strip():
            raise ValueError("Last name connot be empty.")
        
        if "@" not in self.email or "." not in self.email or not self.email.strip() or self.email.count("@") != 1:
            raise ValueError("Invalid email address.")
        
    # @property makes this method behave like a read-only variable.
    # You can access it via student.full_name (WITHOUT parenthesis).
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
        
    # __str__ defines how this object behaves when turned into a string.
    # e.g., when you run print(student),,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
    def __str__(self) -> str:
        return f"Student: {self.full_name} ({self.student_id})"

    def to_dict(self) -> dict:
        return {
            "student_id": self.student_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email
            }

    @classmethod
    def from_dict(cls, data:dict) -> "Student":
        return cls(
            student_id= data["student_id"],
            first_name=data["first_name"],
            last_name = data["last_name"],
            email=data["email"]
        )