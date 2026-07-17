import csv
import io
from abc import ABC, abstractmethod
from notenverwaltung.gradebook import GradeBook

# Abstract Base Class for Report Generator
class ReportGenerator(ABC):
    @abstractmethod
    def generate_student_report(self, student_id: str, gradebook: GradeBook) -> str:
        """Generate a report for an individual student and return it as a string."""
        pass

    @abstractmethod
    def generate_course_report(self, course_id: str, gradebook: GradeBook) -> str:
        """Generate a report for a specific course and return it as a string."""
        pass

    @abstractmethod
    def generate_summary_report(self, gradebook: GradeBook) -> str:
        """Generate a summary report for the entire gradebook and return it as a string."""
        pass

    def generate(self, gradebook: GradeBook, filepath: str) -> None:
        """Generate the summary report and write it to filepath (for backward compatibility)."""
        content = self.generate_summary_report(gradebook)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)


# Text-Based Formatted Report Generator
class TextReportGenerator(ReportGenerator):
    def generate_student_report(self, student_id: str, gradebook: GradeBook) -> str:
        """Generate a human-readable text report for a single student."""
        if student_id not in gradebook.students:
            raise ValueError(f"Student with ID {student_id} not found")
        
        student = gradebook.students[student_id]
        grades = gradebook.get_student_grades(student_id)
        
        lines = []
        lines.append(f"Student Report: {student.full_name} ({student_id})")
        lines.append(f"Email: {student.email}")
        lines.append("-" * 60)
        lines.append(f"{'Course ID':<12} {'Course Name':<25} {'Score':<10} {'Grade':<6} {'Status':<8}")
        lines.append("-" * 60)
        
        for g in grades:
            status = "Pass" if g.is_passing else "Fail"
            lines.append(f"{g.course.course_id:<12} {g.course.name:<25} {g.score:<10.1f} {g.letter_grade:<6} {status:<8}")
            
        lines.append("-" * 60)
        avg = gradebook.student_average(student_id)
        lines.append(f"Overall Average: {avg:.2f}")
        return "\n".join(lines) + "\n"

    def generate_course_report(self, course_id: str, gradebook: GradeBook) -> str:
        """Generate a human-readable text report for a specific course."""
        if course_id not in gradebook.courses:
            raise ValueError(f"Course with ID {course_id} not found")
            
        course = gradebook.courses[course_id]
        grades = gradebook.get_course_grades(course_id)
        
        lines = []
        lines.append(f"Course Report: {course.name} ({course_id})")
        lines.append(f"Max Possible: {course.max_grade} | Passing Threshold: {course.passing_grade}")
        lines.append("-" * 60)
        lines.append(f"{'Student ID':<12} {'Student Name':<25} {'Score':<10} {'Grade':<6}")
        lines.append("-" * 60)
        
        grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for g in grades:
            lines.append(f"{g.student.student_id:<12} {g.student.full_name:<25} {g.score:<10.1f} {g.letter_grade:<6}")
            grade_counts[g.letter_grade] = grade_counts.get(g.letter_grade, 0) + 1
            
        lines.append("-" * 60)
        avg = gradebook.course_average(course_id)
        pass_rate = gradebook.course_pass_rate(course_id)
        lines.append(f"Class Average: {avg:.2f}")
        lines.append(f"Pass Rate: {pass_rate:.1f}%")
        lines.append("Grade Distribution:")
        for letter, count in grade_counts.items():
            lines.append(f"  {letter}: {count}")
        return "\n".join(lines) + "\n"

    def generate_summary_report(self, gradebook: GradeBook) -> str:
        """Generate a human-readable text summary report for all gradebook statistics."""
        overall, at_risk, top_students, courses = gradebook.calculate_statistics()
        
        lines = []
        lines.append("=" * 60)
        lines.append("GradeBook Report")
        lines.append("=" * 60)
        lines.append("")

        # Overall statistics
        lines.append(".......... Overall Metrics ..........")
        for row in overall[2:]: # skip the first row header 
            lines.append(f" {row[0]:<20}: {row[1]}") 
        lines.append("")

        # Course Statistics
        lines.append(".......... Course Statistics ..........")
        lines.append(f" {'Course ID':<12} {'Course Name':<25} {'Enrolled':<10} {'Pass Rate':<10}")
        lines.append("-" * 60)
        if len(courses) > 2:
            for row in courses[2:]:
                lines.append(f"{row[0]:<12} {row[1]:<25} {row[2]:<10} {row[3]:<10}")
        else:
            lines.append("No course Data avaialbe.")
        lines.append("")

        # Top Students
        lines.append("..........TOP PERFORMING STUDENTS (MAX 10) ..........")
        lines.append(f" {'Student ID':<12} {'Name':<25} {'Average':<15}")
        lines.append("-" * 60)
        if len(top_students) > 2:
            for row in top_students[2:]:
                lines.append(f"{row[0]:<12} {row[1]:<25} {row[2]:<15}")
        else:
            lines.append("No Top Students data available")
        lines.append("")

        # At-Risk Students
        lines.append("..........AT-RISK STUDENTS ..........")
        lines.append(f"{'Student ID':<12} {'Student Name':<25} {'Email':<30} {'Average':<10}")
        lines.append("-" * 60)
        if len(at_risk) > 3:
            for row in at_risk[3:]: 
                lines.append(f"{row[0]:<12} {row[1]:<25} {row[2]:<30} {row[3]:<10}")
        else:
            lines.append("No AT-Risk students data available")
        lines.append("")
        
        return "\n".join(lines) + "\n"


# CSV Course Metrics Report Generator
class CsvReportGenerator(ReportGenerator):
    def generate_student_report(self, student_id: str, gradebook: GradeBook) -> str:
        """Generate a CSV report for an individual student and return it as a string."""
        if student_id not in gradebook.students:
            raise ValueError(f"Student with ID {student_id} not found")
        
        student = gradebook.students[student_id]
        grades = gradebook.get_student_grades(student_id)
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Student ID", "Student Name", "Course ID", "Course Name", "Score", "Letter Grade", "Status"])
        for g in grades:
            status = "Pass" if g.is_passing else "Fail"
            writer.writerow([student.student_id, student.full_name, g.course.course_id, g.course.name, g.score, g.letter_grade, status])
        return output.getvalue()

    def generate_course_report(self, course_id: str, gradebook: GradeBook) -> str:
        """Generate a CSV report for a specific course and return it as a string."""
        if course_id not in gradebook.courses:
            raise ValueError(f"Course with ID {course_id} not found")
            
        course = gradebook.courses[course_id]
        grades = gradebook.get_course_grades(course_id)
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Course ID", "Course Name", "Student ID", "Student Name", "Score", "Letter Grade"])
        for g in grades:
            writer.writerow([course.course_id, course.name, g.student.student_id, g.student.full_name, g.score, g.letter_grade])
        return output.getvalue()

    def generate_summary_report(self, gradebook: GradeBook) -> str:
        """Generate a CSV summary report of course metrics and return it as a string."""
        _, _, _, courses = gradebook.calculate_statistics()
        
        output = io.StringIO()
        writer = csv.writer(output)
        # Header row
        writer.writerow(['Course ID', 'Course Name', 'Enrolled Students', 'Pass Rate (%)'])
        # Course data
        if len(courses) > 2:
            for row in courses[2:]:
                writer.writerow(row)
        return output.getvalue()