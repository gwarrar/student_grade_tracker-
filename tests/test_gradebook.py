import pytest
from notenverwaltung.gradebook import GradeBook
from notenverwaltung.models.student import Student
from notenverwaltung.models.course import Course
from notenverwaltung.models.grade import Grade
import csv


@pytest.fixture
def empty_gradebook():
    return GradeBook()

@pytest.fixture
def sample_gradebook():
    gb = GradeBook()

    #add Students 
    s1 = Student("S001", "Anna", "Schmidt", "anna@example.com")
    s2 = Student("S002", "Ben", "Müller", "ben@example.com")
    s3 = Student("S003", "Charlie", "Fischer", "charlie@example.com")
    gb.add_student(s1)
    gb.add_student(s2)
    gb.add_student(s3)

    #Add Courses
    c1 = Course("CS101", "Intro to Programming", max_grade=100.0, passing_grade=50.0, max_students=30)
    c2 = Course("CS102", "Data Structures", max_grade=50.0, passing_grade=25.0, max_students=30)
    gb.add_course(c1)
    gb.add_course(c2)

    #Add Recorded grades
    gb.record_grade("S001", "CS101", 85, "15-01-2026", "")
    gb.record_grade("S001", "CS102", 40, "18-01-2026", "")
    gb.record_grade("S002", "CS101", 92, "16-01-2026", "")
    gb.record_grade("S002", "CS102", 43, "19-01-2026", "")
    gb.record_grade("S003", "CS101", 20, "17-01-2026", "")
    gb.record_grade("S003", "CS102", 10, "20-01-2026", "")

    return gb

def test_add_student_and_course(empty_gradebook):
    s = Student("S001", "Anna", "Schmidt", "anna@example.com")
    c = Course("CS101", "Intro to Programming")
    
    empty_gradebook.add_student(s)
    empty_gradebook.add_course(c)

    assert empty_gradebook.students["S001"] == s
    assert empty_gradebook.courses["CS101"] == c

def test_add_duplicate_student_or_course(empty_gradebook):
    s = Student("S001", "Anna", "Schmidt", "anna@example.com")
    c = Course("CS101", "Intro to Programming")
    
    empty_gradebook.add_student(s)
    empty_gradebook.add_course(c)

    with pytest.raises(ValueError):
        empty_gradebook.add_student(s)

    with pytest.raises(ValueError):
        empty_gradebook.add_course(c)

def test_record_grade_validation(empty_gradebook):
    with pytest.raises(ValueError):
        empty_gradebook.record_grade("S001", "CS101", 80.0, "08-07-2026")

def test_student_and_course_averages(sample_gradebook):
    assert sample_gradebook.student_average('S001') == pytest.approx((85+40)/2)  
    assert sample_gradebook.student_average('S002') == pytest.approx((92+43)/2)   
    assert sample_gradebook.student_average('S003') == pytest.approx((20+10)/2)

    assert sample_gradebook.course_average('CS101') == pytest.approx((85+92+20)/3)
    assert sample_gradebook.course_average('CS102') == pytest.approx((40+43+10)/3)

def test_course_pass_rate(sample_gradebook):
    assert sample_gradebook.course_pass_rate('CS101') == pytest.approx(66.66666666666666)
    # Add 4 spaces here:
    assert sample_gradebook.course_pass_rate('CS102') == pytest.approx(66.66666666666666)

def test_top_students(sample_gradebook):
    top = sample_gradebook.top_students(n=3)
    assert len(top) == 3
    assert top[0][0].student_id == "S002"
    assert top[1][0].student_id == "S001"
    assert top[2][0].student_id == "S003"

def test_students_at_risk(sample_gradebook):
    at_risk= sample_gradebook.students_at_risk()
    assert len(at_risk) == 1
    assert at_risk[0].student_id == "S003"

def test_search_students(sample_gradebook):
    schmidt_search = sample_gradebook.search_students("Schmidt")
    assert len(schmidt_search) == 1
    assert schmidt_search[0].student_id == "S001"
    assert schmidt_search[0].first_name == "Anna"
    assert schmidt_search[0].last_name == "Schmidt"

    domain_search = sample_gradebook.search_students("@example.com")
    assert len(domain_search) == 3
    assert [s.student_id for s in domain_search] == ["S001", "S002", "S003"]

def test_search_courses(sample_gradebook):
    search_cs = sample_gradebook.search_courses("Programming") 
    assert len(search_cs) == 1
    assert search_cs[0].course_id == "CS101"

def test_json_serialization(sample_gradebook, tmp_path):   
    # tmp_path is a built-in pytest fixture that creates a temporary directory for the test
    json_file = tmp_path / "gradebook.json"

    #save the data
    sample_gradebook.save_json(str(json_file))
    assert json_file.exists()

    #Load into a new empty Gradebook
    new_gb = GradeBook()
    new_gb.load_json(str(json_file))

    #verify the loaded data matches the original data
    assert len(new_gb.students) == 3
    assert len(new_gb.courses) == 2
    assert len(new_gb.grades) == 6
    assert new_gb.student_average("S001") == pytest.approx(sample_gradebook.student_average("S001"))

def test_csv_export_and_import(sample_gradebook, tmp_path):
    csv_file = tmp_path / "grades.csv"

    # Export grades
    sample_gradebook.export_csv(str(csv_file))
    assert csv_file.exists()

    # create new clean Gradebook and add the same student and courses as before
    new_gb = GradeBook()
    for student in sample_gradebook.students.values():
        new_gb.add_student(student)
    for course in sample_gradebook.courses.values():
        new_gb.add_course(course)

    report = new_gb.import_csv(str(csv_file))

    assert report["imported"] == 6
    assert report["skipped"] == 0
    assert len(report["errors"]) == 0
    assert len(new_gb.grades) == 6


def test_csv_import_corrupted(sample_gradebook, tmp_path):
    csv_file = tmp_path / "corrupted_grades.csv"

    # Create a corrupted CSV file by removing the header and last line
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["student_id", "course_id", "score", "date", "notes"])
        # Row 2 : valid
        writer.writerow(["S001", "CS101", "90.0", "15-01-2026", "Valid Notes"])
          # Row 3: Invalid Student ID (doesn't exist)
        writer.writerow(["S999", "CS101", "80.0", "15-01-2026", "", "Unknown", "unknown@example.com"])
        # Row 4: Invalid Score (non-numeric)
        writer.writerow(["S001", "CS101", "abc", "15-01-2026", "", "Anna Schmidt", "anna@example.com"])
        # Row 5: Missing columns
        writer.writerow(["S001", "CS101"])

    new_gb = GradeBook()
    new_gb.add_student(Student("S001","Anna","Schmidt","anna@example.com"))
    new_gb.add_course(Course("CS101", "Intro to Programming ", max_grade=100, passing_grade=50, max_students=30))

    report = new_gb.import_csv(str(csv_file))
   # Assertions: 
    # Row 2 passes. Rows 3, 4, 5 fail.
    assert report["imported"] == 1
    assert report["skipped"] == 3
    assert len(report["errors"]) == 3
    # Verify the error messages logged the line numbers
    assert "Row 3" in report["errors"][0]
    assert "Row 4" in report["errors"][1]
    assert "Row 5" in report["errors"][2]
    