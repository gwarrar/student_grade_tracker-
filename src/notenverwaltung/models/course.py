from dataclasses import dataclass

@dataclass
class Course:
    course_id: str
    name: str
    max_grade: float = 100.0
    passing_grade: float = 50.0
    max_students: int = 30

    def __post_init__(self):
        if not self.course_id.strip():
            raise ValueError("Course ID cannot be empty.")
        
        if not self.name.strip():
            raise ValueError("Course name cannot be empty.")
        
        if self.max_grade <= 0:
            raise ValueError("Maximum grade must be greater than 0.")
        
        if self.passing_grade <= 0 or self.passing_grade > self.max_grade:
            raise ValueError(f"Passing grade must be greater than 0 and less than {self.max_grade}.")

        if self.max_students <= 0:
            raise ValueError(f"Max number of students must be greater than 0.")   
            
    def __str__(self) -> str:
        return f"{self.name} (ID: {self.course_id})"   
    
    def to_dict(self) -> dict:
        return {
            "course_id":self.course_id,
            "name":self.name,
            "max_grade":self.max_grade,
            "passing_grade":self.passing_grade,
            "max_students":self.max_students
        }
        
    @classmethod
    def from_dict(cls, data:dict) -> "Course":
        return cls(
            course_id=data["course_id"],
            name=data["name"],
            max_grade=data["max_grade"],
            passing_grade=data["passing_grade"],
            max_students=data["max_students"]
        )