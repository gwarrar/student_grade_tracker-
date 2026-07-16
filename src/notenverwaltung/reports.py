import csv
from abc import ABC, abstractmethod
from notenverwaltung.gradebook import GradeBook

# Abstract Base Class for Report Generator
class ReportGenerator(ABC):
    @abstractmethod
    def generate(self, gradebook: GradeBook, filepath: str) -> None:
        """Generate a report from the GradeBook and write it to filepath."""
        pass


#text Based Formated Report Generator
class TextReportGenerator(ReportGenerator):
    def generate(self, gradebook: GradeBook, filepath: str) -> None:
        """Generate a report from the all , course and student data  and write it to a file."""
        overall , at_risk, top_students, courses = gradebook.calculate_statistics()
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("GradeBook Report")
            f.write("=" * 60 + "\n")
            f.write("\n")

            #over all statistics
            f.write(".......... Overall Metrics ..........\n")
            for row in overall[2:]: #skip the first row header 
                f.write(f" {row[0]:<20}: {row[1]}\n") 
            f.write("\n")

            # course Statistics
            f.write(".......... Course Statistics ..........\n")
            f.write(f" {'Course ID':<12} {'Course Name':<25} {'Enrolled':<10} {'Pass Rate':<10}\n")
            f.write("-" * 60 + "\n")
            if len(courses) > 2:
                for row in courses[2:]:
                    f.write(f"{row[0]:<12} {row[1]:<25} {row[2]:<10} {row[3]:<10}\n")
            else:
                f.write("No course Data avaialbe.\n")
            f.write("\n")

            # to students
            f.write("..........TOP PERFORMING STUDENTS (MAX 10) ..........\n")
            f.write(f" {'Student ID':<12} {'Name':<25} {'Average':<15} {'Status':<15}\n")
            f.write("-" * 60 + "\n")
            if len(top_students) > 2:
                for row in top_students[2:]:
                    f.write(f"{row[0]:<12} {row[1]:<25} {row[2]:<15}\n")
            else:
                f.write("No Top Students data available")
            f.write("\n")

            # AT Risk students
            f.write("..........AT-RISK STUDENTS ..........\n")
            f.write(f"{'Student ID':<12} {'Student Name':<25} {'Email':<30} {'Average':<10}\n")
            f.write("-" * 60 + "\n")
            if len(at_risk) > 3:
                for row in at_risk[3:]: 
                    f.write(f"{row[0]:<12} {row[1]:<25} {row[2]:<30} {row[3]:<10}\n")
            else:
                f.write("No AT-Risk students data available")
            f.write("\n")            


# CSV Course Netrics Report Generator
class CsvReportGenerator(ReportGenerator):
    def generate(self, gradebook: GradeBook, filepath:str ) -> None:
        """Generate a report from the all , course and student data  and write it to a file."""
        _, _, _, courses = gradebook.calculate_statistics()
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Header row
            writer.writerow(['Course ID', 'Course Name', 'Enrolled Students', 'Pass Rate (%)'])
            # Course data (skip header row if any)
            for row in courses[2:]:
                writer.writerow(row)