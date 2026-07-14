import re
from notenverwaltung.models.student import Student
from notenverwaltung.models.course import Course
from notenverwaltung.models.grade import Grade
from notenverwaltung.storage import GradeStore, InMemoryGradeStore
from typing import Dict, List, Set, Tuple, Optional, Union, cast
import json
import csv
from notenverwaltung.exceptions import(
    StudentNotFoundError,
    CourseNotFoundError,
    DuplicateEntryError
)

class GradeBook:
    def __init__(self, store: GradeStore | None = None) -> None:
        self.store = store if store is not None else InMemoryGradeStore()
    
    # those properties students ,curses and grades read directly from the storage engine
    @property
    def students(self) -> dict[str, Student]:
        return {s.student_id: s for s in self.store.get_all_students()}

    @property
    def courses(self) -> dict[str, Course]:
        return {c.course_id: c for c in self.store.get_all_courses()}

    @property
    def grades(self) -> List[Grade]:
        return self.store.get_all_grades()


    def add_student(self, student: Student) -> None:
        #EAFP (Easier to Ask for Forgiveness than Permission) Pattern
        try:
            self.store.get_student(student.student_id)
            raise DuplicateEntryError(f"Student with ID {student.student_id} already exists")
        except KeyError:
            self.store.add_student(student)
    
    def add_course(self, course: Course) -> None:
        try:
            self.store.get_course(course.course_id)
            raise DuplicateEntryError(f"Course with ID {course.course_id} already exists")
        except KeyError:
            self.store.add_course(course)
    
    def record_grade(self, student_id: str, course_id: str, score: float, date: str, notes: str= "") -> Grade:
        try:
            student = self.store.get_student(student_id)
        except KeyError:
            raise StudentNotFoundError(f"Student with ID {student_id} not found")
    
        try:
            course = self.store.get_course(course_id)
        except KeyError:
            raise CourseNotFoundError(f"Course with ID {course_id} not found")
    
        grade = Grade(student, course, score, date, notes)
        self.store.record_grade(grade)
        return grade

    def get_student_grades(self, student_id) -> List[Grade]:
        try:
            self.store.get_student(student_id)
        except KeyError:
            raise StudentNotFoundError(f"Student with ID {student_id} not found")
        return self.store.get_student_grades(student_id)
    
    def get_course_grades(self, course_id) -> list[Grade]:
        try:
            self.store.get_course(course_id)
        except KeyError:
            raise CourseNotFoundError(f"Course with ID {course_id} not found")
        return self.store.get_course_grades(course_id)

    def student_average(self, student_id: str) -> float:
        if student_id not in self.students:
            raise ValueError(f"Student with ID {student_id} not found")
        grades = self.get_student_grades(student_id)
        if not grades:
            return 0.0
        return sum(g.score for g in grades) / len(grades)

    def course_average(self, course_id: str) -> float:
        if course_id not in self.courses:
            raise ValueError(f"Course with ID {course_id} not found")
        grades = self.get_course_grades(course_id)
        if not grades:
            return 0.0
        return sum(g.score for g in grades) / len(grades)
    
    def course_pass_rate(self, course_id) -> float:
        if course_id not in self.courses:
            raise ValueError(f"Course with ID {course_id} not found")
        grades = self.get_course_grades(course_id)
        if not grades:
            return 0.0
        passing_count = sum(1 for g in grades if g.is_passing)
        return (passing_count / len(grades)) * 100
    
    def top_students(self, n: int = 5) -> list[tuple[Student, float]]:
        averages = [
            (student, self.student_average(sid)) for sid, student in self.students.items() if self.get_student_grades(sid)
        ]
        averages.sort(key=lambda x: x[1], reverse=True)
        return averages[:n]
    
    def students_at_risk(self, threshold: float = 60.0 ) -> list[Student]:
        at_risk = []
        for sid, student in self.students.items():
            try:
                avg = self.student_average(sid)
                if avg < threshold:
                    at_risk.append(student)
            except ValueError:
                continue 
        return at_risk 

    def search_students(self, query:str) -> list[Student]:
        results = []
        for student in self.students.values():
            if(re.search(query, student.first_name, re.IGNORECASE) or 
               re.search(query, student.last_name, re.IGNORECASE) or
               re.search(query, student.email, re.IGNORECASE)):
               results.append(student)
        return results

    def search_courses(self, query:str) -> list[Course]:
        return [
            course for course in self.courses.values()
            if re.search(query, course.name, re.IGNORECASE) or re.search(query, course.course_id, re.IGNORECASE)
        ]

    def course_enrollment_count(self, course_id: str) -> int:
        """Return the number of students enrolled in a specific course"""
        if course_id not in self.courses:
            raise ValueError(f"Course with ID {course_id} not found")
        grades = self.get_course_grades(course_id)
        return len(grades)
    
    def course_capacity(self, course_id: str) -> int:
        """Return the capacity of a specific course"""
        if course_id not in self.courses:
            raise ValueError(f"Course with ID {course_id} not found")
        return self.courses[course_id].max_students 
    
    def is_course_full(self, course_id: str) -> bool:
        return self.course_enrollment_count(course_id) >= self.course_capacity(course_id)
    

    def to_dict(self) -> dict:
        return {
            "students": {sid: s.to_dict() for sid, s in self.students.items()},
            "courses": {cid: c.to_dict() for cid, c in self.courses.items()},
            "grades": [g.to_dict() for g in self.grades]
        }
    
    def from_dict(self, data: dict) -> None:
        #1. Load students into storage
        for s in data["students"].values():
            self.store.add_student(Student.from_dict(s))

        #2. Load courses into storage
        for c in data["courses"].values():
            self.store.add_course(Course.from_dict(c))

        #3. Load grades into storage
        for g in data["grades"]:
            student = self.store.get_student(g["student_id"])
            course = self.store.get_course(g["course_id"])
            self.store.record_grade(Grade(student, course, g["score"], g["date"], g["notes"]))
        
    def save_json(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4, ensure_ascii=False)
    
    def load_json(self, filepath: str) -> None:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.from_dict(data)

    def export_csv(self, filepath: str) -> None:
        """Export all grades to a CSV file"""
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            #write the header
            writer.writerow(["student_id", "course_id", "score", "date", "notes"])
            for g in self.grades:
                writer.writerow([
                    g.student.student_id,
                    g.course.course_id,
                    g.score,
                    g.date,
                    g.notes
                ])
    
    def import_csv(self, filepath: str) -> None:
        """Import grades from a CSV file and Skips invalid rows and returns an import report."""
        imported_count = 0
        skipped_count= 0
        errors = []

        #Expected headers
        expected_headers = ["student_id", "course_id", "score", "date", "notes"]
        
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            
            #simple header validation
            if header and [h.strip().lower() for h in header] != expected_headers:
                raise ValueError("CSV header does not match expected format.")
            
            for line_no, row in enumerate(reader, start=2):
                if len(row) != 5:
                    errors.append(f"Row {line_no}: Invalid number of columns {len(row)}, expected 5")
                    skipped_count += 1
                    continue
            
                student_id = row[0].strip()
                course_id = row[1].strip()
                score_str = row[2].strip()
                date_str = row[3].strip()
                notes = row[4].strip()
                try: 
                    score = float(score_str)
                    # This will automatically validate that the student/course exist,
                    #and that score & date are valid!
                    self.record_grade(student_id, course_id, score, date_str, notes)
                    imported_count += 1
                except ValueError as e: 
                    errors.append(f"Row {line_no}: {str(e)}")
                    skipped_count += 1
            
            return {
                "imported": imported_count,
                "skipped": skipped_count,
                "errors": errors
            }

    def calculate_statistics(self) -> dict:
        """Calculate statistics and return them as a list of lists for Gradio."""
        if not self.grades:
            return [["No data"]]
        
        # Overall stats
        total_points = sum(g.score for g in self.grades)
        total_students = len(self.students)
        avg_score = total_points / len(self.grades) if self.grades else 0
        passed_count = sum(1 for g in self.grades if g.is_passing)
        pass_rate = (passed_count / len(self.grades)) * 100 if self.grades else 0

        # At-risk students
        at_risk_list = self.students_at_risk()
        at_risk_data = [[s.student_id, s.full_name, s.email, f"{self.student_average(s.student_id):.1f}"] for s in at_risk_list]

        # Top students
        top_students_list = self.top_students(10) # Top 10 for display
        top_students_data = [[s.student_id, s.full_name, f"{avg:.1f}"] for s, avg in top_students_list]

        # Course stats
        course_data = []
        for cid, course in self.courses.items():
            grades = self.get_course_grades(cid)
            if grades:
                course_pass_rate = self.course_pass_rate(cid)
                course_data.append([
                    cid,
                    course.name,
                    len(grades),
                    f"{course_pass_rate:.1f}%"
                ])
        
        # Return data grouped by section
        return [
            [f"Overall Statistics"], 
            ["Metric", "Value"],
            ["Total Grades", len(self.grades)],
            ["Total Students", total_students],
            ["Average Score", f"{avg_score:.1f}"],
            ["Pass Rate", f"{pass_rate:.1f}%"]
        ], [
            [f"At-Risk Students"],
            [f"Max Threshold: 60.0"],
            ["Student ID", "Name", "Email", "Average"],
            *at_risk_data
        ], [
            [f"Top 10 Students"],
            [f"Student ID", "Name", "Average"],
            *top_students_data
        ], [
            [f"Course Statistics"],
            [f"Course ID", "Name", "Enrolled", "Pass Rate"],
            *course_data
        ]