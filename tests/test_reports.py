import pytest
from notenverwaltung.gradebook import GradeBook
from notenverwaltung.models.student import Student
from notenverwaltung.models.course import Course
from notenverwaltung.models.grade import Grade
from notenverwaltung.storage import InMemoryGradeStore
from notenverwaltung.reports import TextReportGenerator , CsvReportGenerator

@pytest.fixture
def sample_gradebook_for_reports():
    gb = GradeBook()

    #add students
    s1 = Student("S001", "Anna", "Schmidt", "anna@example.com")
    gb.add_student(s1)

    #add Course
    c1 = Course("CS101", "Introduction to Computer Science", max_grade=100, passing_grade=50.0, max_students=30)
    gb.add_course(c1)

    #add Record Grade
    gb.record_grade("S001", "CS101", 85.0, "15-01-2026", "Aced it!")
    return gb


def test_text_report_generator(sample_gradebook_for_reports, tmp_path):
    report_file = tmp_path / "report.txt"
    generator = TextReportGenerator()
    generator.generate(sample_gradebook_for_reports, str(report_file))

    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")
    assert "GradeBook Report" in content
    assert "Anna Schmidt" in content
    assert "CS101" in content
    assert "85.0" in content

def test_csv_report_generator(sample_gradebook_for_reports, tmp_path):
    report_file = tmp_path / "report.csv"
    generator = CsvReportGenerator()
    generator.generate(sample_gradebook_for_reports, str(report_file))

    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")
    assert "Course ID,Course Name,Enrolled Students,Pass Rate" in content
    assert "CS101,Introduction to Computer Science,1,100.0%" in content