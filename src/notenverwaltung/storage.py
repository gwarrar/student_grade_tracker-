import sqlite3
from abc import ABC, abstractmethod
from typing import List
from notenverwaltung.models.student import Student
from notenverwaltung.models.course import Course
from notenverwaltung.models.grade import Grade


#1-abstract base clas 
class GradeStore(ABC):
    @abstractmethod
    def add_student(self, student: Student) -> None:
        pass

    @abstractmethod
    def get_student(self, student_id: str) -> Student:
        pass

    @abstractmethod
    def get_all_students(self) -> list[Student]:
        pass

    @abstractmethod
    def add_course(self, course: Course) -> None:
        pass

    @abstractmethod
    def get_course(self, course_id:str ) -> Course:
        pass

    @abstractmethod
    def get_all_courses(self) -> list[Course]:
        pass

    @abstractmethod
    def record_grade(self, grade:Grade) -> None:
        pass

    @abstractmethod
    def get_student_grades(self, student_id:str) -> list[Grade]:
        pass

    @abstractmethod
    def get_course_grades(self, course_id:str) -> list[Grade]:
        pass

    @abstractmethod
    def get_all_grades(self) -> list[Grade]:
        pass


    #2- In-Memory storage wraps our dicts and Lists
class InMemoryGradeStore(GradeStore):
    def __init__(self):
        self.students: dict[str, Student] = {}
        self.courses: dict[str, Course] = {}
        self.grades: list[Grade] = []

    def add_student(self, student: Student) -> None:
        self.students[student.student_id] = student

    def get_student(self, student_id: str) -> Student:
        if student_id not in self.students:
            raise KeyError(f"Student {student_id} not found.")
        return self.students[student_id]
    
    def get_all_students(self) -> list[Student]:
        return list(self.students.values())

    def add_course(self, course:Course) -> None:
        self.courses[course.course_id] = course
    
    def get_course(self, course_id:str) -> Course:
        if course_id not in self.courses:
            raise KeyError(f"Course {course_id} not found.")
        return self.courses[course_id]
    
    def get_all_courses(self) -> list[Course]:
        return list(self.courses.values())

    def record_grade(self, grade: Grade) -> None:
        self.grades.append(grade)

    def get_student_grades(self, student_id: str) -> list[Grade]:
        return [g for g in self.grades if g.student.student_id == student_id]

    def get_course_grades(self, course_id:str) -> list[Grade]:
        return [g for g in self.grades if g.course.course_id == course_id]
    
    def get_all_grades(self) -> list[Grade]:
        return self.grades


# SQLite Database Storage permanent file Storage
class  SqliteGradeStore(GradeStore):
    def __init__(self, db_path: str = "grades.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        #create Tables in the database if they don't exist
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            #enable foriegn key Support
            cursor.execute("PRAGMA foreign_keys = ON;")

            #Create students Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL
            );
        """)
        
            # Create Courses Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                course_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                max_grade REAL NOT NULL,
                passing_grade REAL NOT NULL,
                max_students INTEGER NOT NULL
            );
        """)

            # create Grades Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                course_id TEXT NOT NULL,
                score REAL NOT NULL,
                date TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                FOREIGN KEY(course_id) REFERENCES courses(course_id) ON DELETE CASCADE
            );
        """)
            conn.commit()

    def add_student(self, student:Student) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO students (student_id, first_name, last_name, email) VALUES (?, ?, ?, ?);",
                (student.student_id, student.first_name, student.last_name, student.email)
            )
            conn.commit()
        
    def get_student(self, student_id: str) -> Student:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT student_id, first_name, last_name, email FROM students WHERE student_id = ?;",
            (student_id,))
            row = cursor.fetchone()
            if not row:
                raise KeyError(f"Student {student_id} not found.")
            return Student(row[0], row[1], row[2], row[3])

    def get_all_students(self) -> list[Student]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT student_id, first_name, last_name, email FROM students;")
            rows = cursor.fetchall()
            return [Student(r[0], r[1], r[2], r[3]) for r in rows]

    def add_course(self, course:Course) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO courses (course_id, name, max_grade, passing_grade, max_students) VALUES (?, ?, ?, ?, ?);",
                (course.course_id, course.name, course.max_grade, course.passing_grade, course.max_students)
            )
            conn.commit()
            
    def get_course(self, course_id: str) -> Course:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT course_id, name, max_grade, passing_grade, max_students FROM courses WHERE course_id = ?;", (course_id,))
            row = cursor.fetchone()
            if not row:
                raise KeyError(f"Course {course_id} not found.")
            return Course(row[0], row[1], row[2], row[3], row[4])

    def get_all_courses(self) -> list[Course]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT course_id, name, max_grade, passing_grade, max_students FROM courses;")
            rows = cursor.fetchall()
            return [Course(r[0], r[1], r[2], r[3], r[4]) for r in rows]

    def record_grade(self, grade:Grade) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute(
                    "INSERT INTO grades (student_id, course_id, score, date, notes) VALUES (?, ?, ?, ?, ?);",
            (grade.student.student_id, grade.course.course_id, grade.score, grade.date, grade.notes)
        )
        conn.commit()
    
    def _row_to_grade(self, row,  conn) -> Grade:
        #help methode to build a grade object form db row 
        student = self.get_student(row[0])
        course = self.get_course(row[1])
        return Grade(student, course, row[2], row[3], row[4] or "")

    def get_student_grades(self, student_id: str) -> list[Grade]:
        with sqlite3.connect(self.db_path) as conn:
            curser = conn.cursor()
            curser.execute("SELECT student_id, course_id, score, date, notes FROM grades WHERE student_id = ?;", (student_id,))
            rows = curser.fetchall()
            return [self._row_to_grade(r, conn) for r in rows]
        
    def get_course_grades(self, course_id: str) -> list[Grade]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT student_id, course_id, score, date, notes FROM grades WHERE course_id = ?;", (course_id,))
            rows = cursor.fetchall()
            return [self._row_to_grade(r, conn) for r in rows]
        
    def get_all_grades(self) -> list[Grade]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT student_id, course_id, score, date, notes FROM grades;")
            rows = cursor.fetchall()
            return [self._row_to_grade(r, conn) for r in rows] 