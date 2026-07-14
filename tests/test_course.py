import pytest
from notenverwaltung.models.course import Course

def test_course_creation_defaults():
    course = Course("A102","Advanced Math")
    assert course.course_id == "A102"
    assert course.name == "Advanced Math"
    assert course.max_grade == 100.0
    assert course.passing_grade == 50.0
    assert course.max_students == 30

def test_course_creation_custom():
    course = Course("PY101", "Python Basic", max_grade=5.0, passing_grade=4.0)
    assert course.course_id == "PY101"
    assert course.name == "Python Basic"
    assert course.max_grade == 5.0
    assert course.passing_grade == 4.0
    assert course.max_students == 30
    
def test_course_validation_empty():
    with pytest.raises(ValueError):
        Course("", "Math")

    with pytest.raises(ValueError):
        Course("M102", "   ")

def test_course_validation_invalid_grades():
    with pytest.raises(ValueError):
        Course("A102", "Advanced Math", max_grade=0)
        
    with pytest.raises(ValueError):
        Course("M102", "Math", max_grade=100, passing_grade = 105)

    with pytest.raises(ValueError):
        Course("M102", "Math", max_grade=100, passing_grade=-5)
    
    with pytest.raises(ValueError):
        Course("M102", "Math", max_students=0)