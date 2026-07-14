import re
from dataclasses import dataclass
from notenverwaltung.models.student import Student
from notenverwaltung.models.course import Course

@dataclass
class Grade:
    student: Student
    course: Course
    score: float
    date: str
    notes: str = ""

    def __post_init__(self):
        if not (0 <= self.score <= self.course.max_grade):
            raise ValueError(
                f"Score {self.score} must be between 0 and {self.course.max_grade}"
                )

        # Regex pattern for DD-MM-YYYY format
        date_pattern = r'^\d{2}-\d{2}-\d{4}$'
        if not re.match(date_pattern, self.date) or len(self.date) != 10:
            raise ValueError(f"Invalid date format")
        
    @property
    def is_passing(self) -> bool:
        return self.score >= self.course.passing_grade
    
    @property
    def percentage(self) -> float:
        return (self.score / self.course.max_grade) * 100

    @property
    def letter_grade(self) -> str:
        # return the letter grade based on the percentage score
        p = self.percentage
        if p >= 90.0:
            return "A"
        elif p >= 80.0:
            return "B"
        elif p >= 70.0:
            return "C"
        elif p >= 60.0:
            return "D"
        else:
            return "F"

    def __str__(self) -> str:
        status = "Passed" if self.is_passing else "Failed"
        return f"Grade: {self.student.full_name} - {self.course.name}: {self.score}/{self.course.max_grade} ({self.letter_grade}) - {status}"
    
    def to_dict(self) -> dict:
        return {
            "student_id": self.student.student_id,
            "course_id": self.course.course_id,
            "score": self.score,
            "date": self.date,
            "notes": self.notes
        }