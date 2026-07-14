import pytest
from notenverwaltung.models.student import Student
from notenverwaltung.models.course import Course
from notenverwaltung.models.grade import Grade

#creating a reusable student and course objects using fixtures 
#in the place of creating a new opject instance every time i run the test 
# in every function i need the opject its somting like a globale variable 
@pytest.fixture
def sample_student():
    return Student("5001", "Anna", "Schmidt", "anna@example.com")


@pytest.fixture
def sample_course():
    return Course("C2532", "Programming", max_grade=100.0, passing_grade=50.0 )

def test_grade_creation(sample_student, sample_course):
    grade = Grade(sample_student, sample_course, score=85.0, date="07-07-2026", notes="well done!")
    assert grade.student == sample_student
    assert grade.course == sample_course
    assert grade.score == 85.0
    assert grade.date == "07-07-2026"
    assert grade.notes == "well done!"
    assert grade.is_passing is True
    assert grade.percentage == 85.0


def test_grade_validation_invalid_score(sample_student, sample_course):
    
    with pytest.raises(ValueError):
        #score connot be negative
        Grade(sample_student, sample_course, score=-5.0, date="07-07-2026")

        #score connt exceed the max grade like (105.0)
        with pytest.raises(ValueError):
            Grade(sample_student, sample_course, score=105.0, date = "07-07-2026")
        
def test_grade_validation_invalid_date(sample_student, sample_course):
    #testing the invalid date formats
    with pytest.raises(ValueError):
        Grade(sample_student, sample_course, score=80.0, date = "07/07/2026")
    
    with pytest.raises(ValueError):
        Grade(sample_student, sample_course, score=80.0, date = "07-07-26")

    with pytest.raises(ValueError):
        Grade(sample_student, sample_course, score=80.0, date = "7-7-2026")

# 4. Parametrized test for Letter grades
@pytest.mark.parametrize(
    "score, expected_letter, expected_passing",
    [
        (95.0, "A", True),
        (90.0, "A", True),
        (85.0, "B", True),
        (80.0, "B", True),
        (75.0, "C", True),
        (70.0, "C", True),
        (65.0, "D", True),
        (60.0, "D", True),
        (55.0, "F", True),   # 55% is F but passing (passing_grade=50.0)
        (45.0, "F", False),  # Failing
    ]
)

def test_letter_grade(sample_student, sample_course, score, expected_letter, expected_passing):
    grade = Grade(sample_student, sample_course, score=score, date="07-07-2026", notes="well done!")
    assert grade.letter_grade == expected_letter
    assert grade.is_passing == expected_passing