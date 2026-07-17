import pytest
from notenverwaltung.gradebook import GradeBook
from notenverwaltung.models.student import Student
from notenverwaltung.models.course import Course
from notenverwaltung.reports import TextReportGenerator, CsvReportGenerator

@pytest.fixture
def sample_gradebook_for_reports():
    gb = GradeBook()

    # Add student
    s1 = Student("S001", "Anna", "Schmidt", "anna@example.com")
    gb.add_student(s1)

    # Add Course
    c1 = Course("CS101", "Introduction to Computer Science", max_grade=100.0, passing_grade=50.0, max_students=30)
    gb.add_course(c1)

    # Add Record Grade
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


def test_text_individual_reports(sample_gradebook_for_reports):
    generator = TextReportGenerator()
    
    # 1. Student Report
    student_report = generator.generate_student_report("S001", sample_gradebook_for_reports)
    assert "Student Report: Anna Schmidt (S001)" in student_report
    assert "CS101" in student_report
    assert "85.0" in student_report
    assert "Pass" in student_report
    
    # 2. Course Report
    course_report = generator.generate_course_report("CS101", sample_gradebook_for_reports)
    assert "Course Report: Introduction to Computer Science (CS101)" in course_report
    assert "Anna Schmidt" in course_report
    assert "85.0" in course_report
    assert "Class Average: 85.00" in course_report

    # 3. Summary Report
    summary_report = generator.generate_summary_report(sample_gradebook_for_reports)
    assert "GradeBook Report" in summary_report
    assert "Anna Schmidt" in summary_report


def test_csv_individual_reports(sample_gradebook_for_reports):
    generator = CsvReportGenerator()
    
    # 1. Student Report
    student_report = generator.generate_student_report("S001", sample_gradebook_for_reports)
    assert "Student ID,Student Name,Course ID,Course Name,Score,Letter Grade,Status" in student_report
    assert "S001,Anna Schmidt,CS101,Introduction to Computer Science,85.0,B,Pass" in student_report

    # 2. Course Report
    course_report = generator.generate_course_report("CS101", sample_gradebook_for_reports)
    assert "Course ID,Course Name,Student ID,Student Name,Score,Letter Grade" in course_report
    assert "CS101,Introduction to Computer Science,S001,Anna Schmidt,85.0,B" in course_report

    # 3. Summary Report
    summary_report = generator.generate_summary_report(sample_gradebook_for_reports)
    assert "Course ID,Course Name,Enrolled Students,Pass Rate (%)" in summary_report
    assert "CS101,Introduction to Computer Science,1,100.0%" in summary_report