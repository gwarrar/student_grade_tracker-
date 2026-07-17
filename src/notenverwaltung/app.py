import os
import csv
import pandas as pd
import gradio as gr
from notenverwaltung.gradebook import GradeBook
from notenverwaltung.storage import SqliteGradeStore
from notenverwaltung.reports import TextReportGenerator, CsvReportGenerator
from notenverwaltung.exceptions import StudentNotFoundError, CourseNotFoundError, DuplicateEntryError
from notenverwaltung.models.student import Student
from notenverwaltung.models.course import Course

# Initialize database storage and GradeBook
db_path = "grades.db"
store = SqliteGradeStore(db_path)
gb = GradeBook(store=store)

# =====================================================================
# Helper Functions & UI Synchronizers (returning pandas DataFrames)
# =====================================================================

def get_student_choices():
    return [s.student_id for s in gb.store.get_all_students()]

def get_course_choices():
    return [c.course_id for c in gb.store.get_all_courses()]

def get_all_students_table():
    data = [[s.student_id, s.full_name, s.email] for s in gb.store.get_all_students()]
    return pd.DataFrame(data, columns=["Student ID", "Full Name", "Email"])

def get_all_courses_table():
    data = [[c.course_id, c.name, c.max_grade, c.passing_grade, c.max_students] for c in gb.store.get_all_courses()]
    return pd.DataFrame(data, columns=["Course ID", "Name", "Max Grade", "Passing Grade", "Capacity"])

def get_all_grades_table():
    data = [[g.student.student_id, g.student.full_name, g.course.course_id, g.score, g.date, g.notes] for g in gb.grades]
    return pd.DataFrame(data, columns=["Student ID", "Name", "Course ID", "Score", "Date", "Notes"])

def refresh_stats():
    """Retrieve statistics and format them as pandas DataFrames."""
    overall, at_risk, top_students, courses = gb.calculate_statistics()
    
    # overall
    overall_data = overall[2:]
    overall_df = pd.DataFrame(overall_data, columns=["Metric", "Value"])
    
    # at_risk
    at_risk_data = at_risk[3:] if len(at_risk) > 3 else []
    at_risk_df = pd.DataFrame(at_risk_data, columns=["Student ID", "Name", "Email", "Average"])
    
    # top_students
    top_data = top_students[2:] if len(top_students) > 2 else []
    top_df = pd.DataFrame(top_data, columns=["Student ID", "Name", "Average"])
    
    # courses
    courses_data = courses[2:] if len(courses) > 2 else []
    courses_df = pd.DataFrame(courses_data, columns=["Course ID", "Name", "Enrolled", "Pass Rate"])
    
    return overall_df, at_risk_df, top_df, courses_df

def get_course_stats_plot():
    """Build a pandas DataFrame for the course pass rates bar chart."""
    _, _, _, courses = gb.calculate_statistics()
    if len(courses) <= 2:
        return pd.DataFrame(columns=["Course ID", "Pass Rate (%)"])
    
    data = []
    for row in courses[2:]:
        pass_rate_str = row[3].replace("%", "")
        try:
            pass_rate = float(pass_rate_str)
        except ValueError:
            pass_rate = 0.0
        data.append({
            "Course ID": row[0],
            "Pass Rate (%)": pass_rate
        })
    return pd.DataFrame(data)

def get_course_averages_plot():
    """Build a pandas DataFrame for the course average scores bar chart."""
    _, _, _, courses = gb.calculate_statistics()
    if len(courses) <= 2:
        return pd.DataFrame(columns=["Course ID", "Average Score"])
    
    data = []
    for row in courses[2:]:
        cid = row[0]
        try:
            avg = gb.course_average(cid)
        except Exception:
            avg = 0.0
        data.append({
            "Course ID": cid,
            "Average Score": avg
        })
    return pd.DataFrame(data)

def get_grade_distribution_plot():
    """Build a pandas DataFrame for the letter grade distribution bar chart."""
    grades = gb.grades
    counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for g in grades:
        counts[g.letter_grade] = counts.get(g.letter_grade, 0) + 1
    
    data = [{"Grade": k, "Count": v} for k, v in counts.items()]
    return pd.DataFrame(data)

# =====================================================================
# Local Tab Focus Focus Event Handlers (avoids updating hidden inputs)
# =====================================================================

def on_select_stats_tab():
    overall_df, at_risk_df, top_df, courses_df = refresh_stats()
    chart_pass_df = get_course_stats_plot()
    chart_avg_df = get_course_averages_plot()
    chart_dist_df = get_grade_distribution_plot()
    return (
        gr.update(value=overall_df),
        gr.update(value=courses_df),
        gr.update(value=top_df),
        gr.update(value=at_risk_df),
        gr.update(value=chart_pass_df),
        gr.update(value=chart_avg_df),
        gr.update(value=chart_dist_df)
    )

def on_select_students_tab():
    return gr.update(value=get_all_students_table())

def on_select_courses_tab():
    return gr.update(value=get_all_courses_table())

def on_select_grades_tab():
    s_choices = get_student_choices()
    c_choices = get_course_choices()
    return (
        gr.update(value=get_all_grades_table()),
        gr.update(choices=s_choices),
        gr.update(choices=c_choices)
    )

def on_select_reports_tab():
    s_choices = get_student_choices()
    c_choices = get_course_choices()
    return (
        gr.update(choices=s_choices),
        gr.update(choices=c_choices)
    )

# =====================================================================
# Local Tab CRUD Button Handlers
# =====================================================================

def add_student_handler(student_id, first_name, last_name, email):
    try:
        student = Student(student_id, first_name, last_name, email)
        gb.add_student(student)
        return get_all_students_table(), f"✅ Student {student.full_name} added successfully!", "", "", "", ""
    except Exception as e:
        return gr.update(), f"❌ Error: {str(e)}", gr.update(), gr.update(), gr.update(), gr.update()

def add_course_handler(course_id, name, max_grade, passing_grade, max_students):
    try:
        course = Course(course_id, name, float(max_grade), float(passing_grade), int(max_students))
        gb.add_course(course)
        return get_all_courses_table(), f"✅ Course {course.name} added successfully!", "", "", 100.0, 50.0, 30.0
    except Exception as e:
        return gr.update(), f"❌ Error: {str(e)}", gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

def record_grade_handler(student_id, course_id, score, date, notes):
    try:
        gb.record_grade(student_id, course_id, float(score), date, notes)
        return get_all_grades_table(), "✅ Grade recorded successfully!", "", "", ""
    except Exception as e:
        return gr.update(), f"❌ Error: {str(e)}", gr.update(), gr.update(), gr.update()

def search_students_ui(query):
    results = gb.search_students(query)
    data = [[s.student_id, s.full_name, s.email] for s in results]
    return pd.DataFrame(data, columns=["Student ID", "Full Name", "Email"])

def search_courses_ui(query):
    results = gb.search_courses(query)
    data = [[c.course_id, c.name, c.max_grade, c.passing_grade, c.max_students] for c in results]
    return pd.DataFrame(data, columns=["Course ID", "Name", "Max Grade", "Passing Grade", "Capacity"])

# =====================================================================
# CSV Import / Export Handlers
# =====================================================================

def import_grades_handler(file):
    if file is None:
        return gr.update(), "❌ Please upload a CSV file."
    try:
        report = gb.import_csv(file.name)
        msg = f"📊 CSV Import Complete! Imported: {report['imported']}, Skipped: {report['skipped']}"
        if report['errors']:
            msg += "\n\nErrors:\n" + "\n".join(report['errors'][:5])
        return get_all_grades_table(), msg
    except Exception as e:
        return gr.update(), f"❌ Import Error: {str(e)}"

def export_grades_handler():
    filepath = "grades_export.csv"
    try:
        gb.export_csv(filepath)
        return gr.update(value=filepath, visible=True), f"💾 Exported all grades to: {os.path.abspath(filepath)}"
    except Exception as e:
        return gr.update(), f"❌ Export Error: {str(e)}"

def import_students_handler(file):
    if file is None:
        return gr.update(), "❌ Please upload a CSV file."
    try:
        imported, skipped = 0, 0
        errors = []
        with open(file.name, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for line_no, row in enumerate(reader, start=2):
                if len(row) < 4:
                    errors.append(f"Line {line_no}: Invalid column count")
                    skipped += 1
                    continue
                try:
                    student = Student(row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip())
                    gb.add_student(student)
                    imported += 1
                except Exception as e:
                    errors.append(f"Line {line_no}: {str(e)}")
                    skipped += 1
        msg = f"👤 Students Imported: {imported}, Skipped: {skipped}"
        if errors:
            msg += "\nErrors:\n" + "\n".join(errors[:5])
        return get_all_students_table(), msg
    except Exception as e:
        return gr.update(), f"❌ Import Error: {str(e)}"

def export_students_handler():
    filepath = "students_export.csv"
    try:
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["student_id", "first_name", "last_name", "email"])
            for s in gb.store.get_all_students():
                writer.writerow([s.student_id, s.first_name, s.last_name, s.email])
        return gr.update(value=filepath, visible=True), f"💾 Exported students to: {os.path.abspath(filepath)}"
    except Exception as e:
        return gr.update(), f"❌ Export Error: {str(e)}"

def import_courses_handler(file):
    if file is None:
        return gr.update(), "❌ Please upload a CSV file."
    try:
        imported, skipped = 0, 0
        errors = []
        with open(file.name, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for line_no, row in enumerate(reader, start=2):
                if len(row) < 5:
                    errors.append(f"Line {line_no}: Invalid column count")
                    skipped += 1
                    continue
                try:
                    course = Course(row[0].strip(), row[1].strip(), float(row[2]), float(row[3]), int(row[4]))
                    gb.add_course(course)
                    imported += 1
                except Exception as e:
                    errors.append(f"Line {line_no}: {str(e)}")
                    skipped += 1
        msg = f"📚 Courses Imported: {imported}, Skipped: {skipped}"
        if errors:
            msg += "\nErrors:\n" + "\n".join(errors[:5])
        return get_all_courses_table(), msg
    except Exception as e:
        return gr.update(), f"❌ Import Error: {str(e)}"

def export_courses_handler():
    filepath = "courses_export.csv"
    try:
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["course_id", "name", "max_grade", "passing_grade", "max_students"])
            for c in gb.store.get_all_courses():
                writer.writerow([c.course_id, c.name, c.max_grade, c.passing_grade, c.max_students])
        return gr.update(value=filepath, visible=True), f"💾 Exported courses to: {os.path.abspath(filepath)}"
    except Exception as e:
        return gr.update(), f"❌ Export Error: {str(e)}"

# =====================================================================
# Row Selection Preview Handlers (Dynamic .select() callbacks)
# =====================================================================

def on_select_student(df, evt: gr.SelectData):
    """Retrieve selected student ID and return their report string."""
    row_idx = evt.index[0]
    student_id = df.iloc[row_idx, 0]
    try:
        generator = TextReportGenerator()
        report = generator.generate_student_report(student_id, gb)
        return report, student_id
    except Exception as e:
        return f"❌ Error: {str(e)}", ""

def on_select_course(df, evt: gr.SelectData):
    """Retrieve selected course ID and return its report string."""
    row_idx = evt.index[0]
    course_id = df.iloc[row_idx, 0]
    try:
        generator = TextReportGenerator()
        report = generator.generate_course_report(course_id, gb)
        return report, course_id
    except Exception as e:
        return f"❌ Error: {str(e)}", ""

def on_select_grade(df, evt: gr.SelectData):
    """Retrieve student ID from the selected grade record and return their report string."""
    row_idx = evt.index[0]
    student_id = df.iloc[row_idx, 0]
    try:
        generator = TextReportGenerator()
        report = generator.generate_student_report(student_id, gb)
        return report, student_id
    except Exception as e:
        return f"❌ Error: {str(e)}", ""

# =====================================================================
# Report Selection Preview Handlers (Dropdown callbacks)
# =====================================================================

def view_student_report_handler(student_id):
    if not student_id:
        return "❌ Please select a Student ID from the dropdown."
    try:
        generator = TextReportGenerator()
        return generator.generate_student_report(student_id, gb)
    except Exception as e:
        return f"❌ Error generating report: {str(e)}"

def view_course_report_handler(course_id):
    if not course_id:
        return "❌ Please select a Course ID from the dropdown."
    try:
        generator = TextReportGenerator()
        return generator.generate_course_report(course_id, gb)
    except Exception as e:
        return f"❌ Error generating report: {str(e)}"

def view_summary_report_handler():
    try:
        generator = TextReportGenerator()
        return generator.generate_summary_report(gb)
    except Exception as e:
        return f"❌ Error generating summary report: {str(e)}"

# =====================================================================
# Report Export File Handlers (writes to files)
# =====================================================================

def export_selected_student_report(student_id):
    if not student_id:
        return gr.update(), "❌ No student selected. Please click on a student in the table first."
    filepath = f"student_report_{student_id}.txt"
    try:
        generator = TextReportGenerator()
        content = generator.generate_student_report(student_id, gb)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return gr.update(value=filepath, visible=True), f"💾 Exported report to: {os.path.abspath(filepath)}"
    except Exception as e:
        return gr.update(), f"❌ Export Error: {str(e)}"

def export_selected_course_report(course_id):
    if not course_id:
        return gr.update(), "❌ No course selected. Please click on a course in the table first."
    filepath = f"course_report_{course_id}.txt"
    try:
        generator = TextReportGenerator()
        content = generator.generate_course_report(course_id, gb)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return gr.update(value=filepath, visible=True), f"💾 Exported report to: {os.path.abspath(filepath)}"
    except Exception as e:
        return gr.update(), f"❌ Export Error: {str(e)}"

def generate_text_report_handler():
    filepath = "gradebook_report.txt"
    try:
        generator = TextReportGenerator()
        generator.generate(gb, filepath)
        return f"📄 Text Report generated at: {os.path.abspath(filepath)}"
    except Exception as e:
        return f"❌ Report Error: {str(e)}"

def generate_csv_report_handler():
    filepath = "course_metrics_report.csv"
    try:
        generator = CsvReportGenerator()
        generator.generate(gb, filepath)
        return f"📊 CSV Summary generated at: {os.path.abspath(filepath)}"
    except Exception as e:
        return f"❌ Report Error: {str(e)}"

# =====================================================================
# Gradio Blocks UI Layout
# =====================================================================

theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="slate",
    neutral_hue="slate"
)

# In Gradio 6.0, Blocks doesn't take 'theme' in its constructor (moved to launch)
with gr.Blocks(title="GradeBook Registry") as demo:
    # State values to track current row selections
    selected_student_id = gr.State(value="")
    selected_course_id = gr.State(value="")
    selected_grade_student_id = gr.State(value="")

    gr.Markdown(
        """
        # 🎓 GradeBook Management Registry
        An elegant dashboard for managing students, courses, grading schemas, and data persistence.
        """
    )
    
    with gr.Tabs():
        # TAB 1: DASHBOARD / STATISTICS
        with gr.TabItem("📊 Averages & Statistics") as tab_stats:
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Overall Statistics")
                    overall_tbl = gr.Dataframe(
                        headers=["Metric", "Value"],
                        datatype=["str", "str"],
                        interactive=False,
                        value=refresh_stats()[0]
                    )
                with gr.Column(scale=2):
                    gr.Markdown("### Course Statistics")
                    courses_tbl = gr.Dataframe(
                        headers=["Course ID", "Name", "Enrolled", "Pass Rate"],
                        datatype=["str", "str", "number", "str"],
                        interactive=False,
                        value=refresh_stats()[3]
                    )
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Top Performing Students (Max 10)")
                    top_tbl = gr.Dataframe(
                        headers=["Student ID", "Name", "Average"],
                        datatype=["str", "str", "str"],
                        interactive=False,
                        value=refresh_stats()[2]
                    )
                with gr.Column(scale=1):
                    gr.Markdown("### At-Risk Students (< 60% Average)")
                    at_risk_tbl = gr.Dataframe(
                        headers=["Student ID", "Name", "Email", "Average"],
                        datatype=["str", "str", "str", "str"],
                        interactive=False,
                        value=refresh_stats()[1]
                    )
            
            with gr.Row():
                gr.Markdown("## 📊 Visual Analytics & Performance Charts")
            with gr.Row():
                with gr.Column():
                    course_plot = gr.BarPlot(
                        value=get_course_stats_plot(),
                        x="Course ID",
                        y="Pass Rate (%)",
                        title="Pass Rate per Course (%)",
                        tooltip=["Course ID", "Pass Rate (%)"],
                        y_lim=[0, 100],
                        height=280
                    )
                with gr.Column():
                    course_avg_plot = gr.BarPlot(
                        value=get_course_averages_plot(),
                        x="Course ID",
                        y="Average Score",
                        title="Average Score per Course",
                        tooltip=["Course ID", "Average Score"],
                        y_lim=[0, 100],
                        height=280
                    )
                with gr.Column():
                    grade_dist_plot = gr.BarPlot(
                        value=get_grade_distribution_plot(),
                        x="Grade",
                        y="Count",
                        title="Overall Grade Distribution (A-F)",
                        tooltip=["Grade", "Count"],
                        height=280
                    )
            
            with gr.Row():
                refresh_btn = gr.Button("🔄 Refresh Data", variant="primary")

        # TAB 2: MANAGE STUDENTS
        with gr.TabItem("👤 Manage Students") as tab_students:
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Add New Student")
                    student_id = gr.Textbox(label="Student ID (e.g. S001)")
                    first_name = gr.Textbox(label="First Name")
                    last_name = gr.Textbox(label="Last Name")
                    email = gr.Textbox(label="Email Address")
                    add_student_btn = gr.Button("➕ Add Student", variant="primary")
                    
                    gr.Markdown("---")
                    gr.Markdown("### Bulk Import/Export")
                    student_csv_input = gr.File(label="Upload Students CSV File")
                    import_students_btn = gr.Button("📥 Import Students CSV", variant="secondary")
                    export_students_btn = gr.Button("💾 Export Students to CSV", variant="secondary")
                    student_csv_output = gr.File(label="Download Students CSV Export", visible=False)
                    
                with gr.Column(scale=2):
                    gr.Markdown("### Search / Registry")
                    student_search = gr.Textbox(placeholder="Search by ID, name, or email...")
                    students_list = gr.Dataframe(
                        headers=["Student ID", "Full Name", "Email"],
                        datatype=["str", "str", "str"],
                        interactive=False,
                        value=get_all_students_table()
                    )
                    refresh_btn_s = gr.Button("🔄 Refresh Data", variant="secondary")
                    
                with gr.Column(scale=2):
                    gr.Markdown("### 👤 Student Report Preview")
                    student_report_preview = gr.Textbox(
                        label="Click on any student in the table on the left to load their report", 
                        lines=15, 
                        interactive=False
                    )
                    export_selected_student_btn = gr.Button("💾 Export Selected Student Report", variant="secondary")
                    selected_student_file_output = gr.File(label="Download Report", visible=False)

        # TAB 3: MANAGE COURSES
        with gr.TabItem("📚 Manage Courses") as tab_courses:
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Add New Course")
                    course_id = gr.Textbox(label="Course ID (e.g. CS101)")
                    course_name = gr.Textbox(label="Course Name")
                    max_grade = gr.Number(label="Max Possible Grade", value=100.0)
                    passing_grade = gr.Number(label="Passing Threshold Grade", value=50.0)
                    max_students = gr.Number(label="Max Capacity (Default 30)", value=30.0)
                    add_course_btn = gr.Button("➕ Add Course", variant="primary")
                    
                    gr.Markdown("---")
                    gr.Markdown("### Bulk Import/Export")
                    course_csv_input = gr.File(label="Upload Courses CSV File")
                    import_courses_btn = gr.Button("📥 Import Courses CSV", variant="secondary")
                    export_courses_btn = gr.Button("💾 Export Courses to CSV", variant="secondary")
                    course_csv_output = gr.File(label="Download Courses CSV Export", visible=False)
                    
                with gr.Column(scale=2):
                    gr.Markdown("### Search / Registry")
                    course_search = gr.Textbox(placeholder="Search by ID or name...")
                    courses_list = gr.Dataframe(
                        headers=["Course ID", "Name", "Max Grade", "Passing Grade", "Capacity"],
                        datatype=["str", "str", "number", "number", "number"],
                        interactive=False,
                        value=get_all_courses_table()
                    )
                    refresh_btn_c = gr.Button("🔄 Refresh Data", variant="secondary")
                    
                with gr.Column(scale=2):
                    gr.Markdown("### 📚 Course Report Preview")
                    course_report_preview = gr.Textbox(
                        label="Click on any course in the table on the left to load its report", 
                        lines=15, 
                        interactive=False
                    )
                    export_selected_course_btn = gr.Button("💾 Export Selected Course Report", variant="secondary")
                    selected_course_file_output = gr.File(label="Download Report", visible=False)

        # TAB 4: RECORD GRADES
        with gr.TabItem("📝 Record Grades") as tab_grades:
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Enter Grade Record")
                    grade_student_id = gr.Dropdown(label="Select Student ID", choices=get_student_choices())
                    grade_course_id = gr.Dropdown(label="Select Course ID", choices=get_course_choices())
                    grade_score = gr.Number(label="Score")
                    grade_date = gr.Textbox(label="Date (DD-MM-YYYY)")
                    grade_notes = gr.Textbox(label="Notes (Optional)")
                    record_grade_btn = gr.Button("📝 Save Record", variant="primary")
                    
                    gr.Markdown("---")
                    gr.Markdown("### Bulk Import/Export")
                    grade_csv_input = gr.File(label="Upload Grades CSV File")
                    import_grades_btn = gr.Button("📥 Import Grades CSV", variant="secondary")
                    export_grades_btn = gr.Button("💾 Export Grades to CSV", variant="secondary")
                    grade_csv_output = gr.File(label="Download Grades CSV Export", visible=False)
                    
                with gr.Column(scale=2):
                    gr.Markdown("### Grade Records Book")
                    grades_list = gr.Dataframe(
                        headers=["Student ID", "Name", "Course ID", "Score", "Date", "Notes"],
                        datatype=["str", "str", "str", "number", "str", "str"],
                        interactive=False,
                        value=get_all_grades_table()
                    )
                    refresh_btn_g = gr.Button("🔄 Refresh Data", variant="secondary")
                    
                with gr.Column(scale=2):
                    gr.Markdown("### 👤 Student Report Preview")
                    grade_student_report_preview = gr.Textbox(
                        label="Click on any grade in the table to load that student's full report", 
                        lines=15, 
                        interactive=False
                    )
                    export_grade_student_btn = gr.Button("💾 Export Selected Student Report", variant="secondary")
                    grade_student_file_output = gr.File(label="Download Report", visible=False)

        # TAB 5: REPORTS & FORMATTERS
        with gr.TabItem("💾 Generate & View Reports") as tab_reports:
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 👤 Student Report Preview")
                    report_student_id = gr.Dropdown(label="Select Student ID", choices=get_student_choices())
                    btn_view_student = gr.Button("🔍 View Student Report", variant="secondary")
                    txt_student_preview = gr.Textbox(label="Student Report Preview", lines=12, interactive=False)
                    
                with gr.Column(scale=1):
                    gr.Markdown("### 📚 Course Report Preview")
                    report_course_id = gr.Dropdown(label="Select Course ID", choices=get_course_choices())
                    btn_view_course = gr.Button("🔍 View Course Report", variant="secondary")
                    txt_course_preview = gr.Textbox(label="Course Report Preview", lines=12, interactive=False)

                with gr.Column(scale=1):
                    gr.Markdown("### 📊 Summary Report & Exports")
                    btn_view_summary = gr.Button("🔍 View Summary Report", variant="primary")
                    txt_summary_preview = gr.Textbox(label="Summary Report Preview", lines=10, interactive=False)
                    gr.Markdown("---")
                    text_report_btn = gr.Button("📄 Export Summary to Text File", variant="secondary")
                    csv_report_btn = gr.Button("📊 Export Summary to CSV File", variant="secondary")
            
        # Global status output shown at the top
        # global_status = gr.Textbox(label="System Log / Messages", value="🟢 System ready.", interactive=False)

    # =====================================================================
    # Tab Selection Refresh Listeners (Local updates on Tab select)
    # =====================================================================
    tab_stats.select(
        fn=on_select_stats_tab,
        outputs=[overall_tbl, courses_tbl, top_tbl, at_risk_tbl, course_plot, course_avg_plot, grade_dist_plot]
    )
    
    tab_students.select(
        fn=on_select_students_tab,
        outputs=[students_list]
    )
    
    tab_courses.select(
        fn=on_select_courses_tab,
        outputs=[courses_list]
    )
    
    tab_grades.select(
        fn=on_select_grades_tab,
        outputs=[grades_list, grade_student_id, grade_course_id]
    )
    
    tab_reports.select(
        fn=on_select_reports_tab,
        outputs=[report_student_id, report_course_id]
    )

    # =====================================================================
    # Local Manual Refresh Buttons on all tabs
    # =====================================================================
    refresh_btn.click(
        fn=on_select_stats_tab, 
        outputs=[overall_tbl, courses_tbl, top_tbl, at_risk_tbl, course_plot, course_avg_plot, grade_dist_plot]
    )
    refresh_btn_s.click(
        fn=on_select_students_tab, 
        outputs=[students_list]
    )
    refresh_btn_c.click(
        fn=on_select_courses_tab, 
        outputs=[courses_list]
    )
    refresh_btn_g.click(
        fn=on_select_grades_tab, 
        outputs=[grades_list, grade_student_id, grade_course_id]
    )

    # =====================================================================
    # Row Selection Event Bindings (.select() handlers)
    # =====================================================================
    students_list.select(
        fn=on_select_student,
        inputs=[students_list],
        outputs=[student_report_preview, selected_student_id]
    )
    
    courses_list.select(
        fn=on_select_course,
        inputs=[courses_list],
        outputs=[course_report_preview, selected_course_id]
    )
    
    grades_list.select(
        fn=on_select_grade,
        inputs=[grades_list],
        outputs=[grade_student_report_preview, selected_grade_student_id]
    )

    # =====================================================================
    # Selected Row Export Bindings
    # =====================================================================
    export_selected_student_btn.click(
        fn=export_selected_student_report,
        inputs=[selected_student_id],
        outputs=[selected_student_file_output, global_status]
    )
    
    export_selected_course_btn.click(
        fn=export_selected_course_report,
        inputs=[selected_course_id],
        outputs=[selected_course_file_output, global_status]
    )
    
    export_grade_student_btn.click(
        fn=export_selected_student_report,
        inputs=[selected_grade_student_id],
        outputs=[grade_student_file_output, global_status]
    )

    # =====================================================================
    # CRUD & Import Event Bindings (local outputs only to prevent crashes)
    # =====================================================================
    
    # Add student handler
    add_student_btn.click(
        fn=add_student_handler,
        inputs=[student_id, first_name, last_name, email],
        outputs=[students_list, global_status, student_id, first_name, last_name, email]
    )
    student_search.change(
        fn=search_students_ui,
        inputs=[student_search],
        outputs=[students_list]
    )
    import_students_btn.click(
        fn=import_students_handler,
        inputs=[student_csv_input],
        outputs=[students_list, global_status]
    )
    export_students_btn.click(
        fn=export_students_handler, 
        outputs=[student_csv_output, global_status]
    )

    # Add course handler
    add_course_btn.click(
        fn=add_course_handler,
        inputs=[course_id, course_name, max_grade, passing_grade, max_students],
        outputs=[courses_list, global_status, course_id, course_name, max_grade, passing_grade, max_students]
    )
    course_search.change(
        fn=search_courses_ui,
        inputs=[course_search],
        outputs=[courses_list]
    )
    import_courses_btn.click(
        fn=import_courses_handler,
        inputs=[course_csv_input],
        outputs=[courses_list, global_status]
    )
    export_courses_btn.click(
        fn=export_courses_handler, 
        outputs=[course_csv_output, global_status]
    )

    # Record grade handler
    record_grade_btn.click(
        fn=record_grade_handler,
        inputs=[grade_student_id, grade_course_id, grade_score, grade_date, grade_notes],
        outputs=[grades_list, global_status, grade_score, grade_date, grade_notes]
    )
    import_grades_btn.click(
        fn=import_grades_handler,
        inputs=[grade_csv_input],
        outputs=[grades_list, global_status]
    )
    export_grades_btn.click(
        fn=export_grades_handler, 
        outputs=[grade_csv_output, global_status]
    )

    # Interactive Report Views (tab-specific)
    btn_view_student.click(fn=view_student_report_handler, inputs=[report_student_id], outputs=[txt_student_preview])
    btn_view_course.click(fn=view_course_report_handler, inputs=[report_course_id], outputs=[txt_course_preview])
    btn_view_summary.click(fn=view_summary_report_handler, outputs=[txt_summary_preview])

    # Report file exporters
    text_report_btn.click(fn=generate_text_report_handler, outputs=[global_status])
    csv_report_btn.click(fn=generate_csv_report_handler, outputs=[global_status])
    

# Launch the app (with Gradio 6.0 theme parameter support)
if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, theme=theme, share=True)
