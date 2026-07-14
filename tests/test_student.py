import pytest

# We import our Student class to test it
from notenverwaltung.models.student import Student

# 1. Test standard successful creation
def test_student_creation():
    student = Student("5001" , "Lara" , "Müller" , "lara@example.com")

    assert student.student_id == "5001"
    assert student.first_name == "Lara"
    assert student.last_name == "Müller"
    assert student.email == "lara@example.com"
    assert student.full_name == "Lara Müller"
    assert str(student) == "Student: Lara Müller (5001)"

# 2. Test that validation correctly blocks empty inputs
def test_student_validation_empty_names():
    with pytest.raises(ValueError):
        Student("5002", "", "Müller", "lara@example.com")

    with pytest.raises(ValueError): 
        Student("5002", "Max", " ", "lara@example.com")

#3. Test that vaidation blocks emails without '@' or dots
def test_student_validationn_invalid_email():
    with pytest.raises(ValueError):
        Student("5003","Jonas","Schneider","jonas.schnieder.com")
    
    with pytest.raises(ValueError):
        Student("5004", "Lisa", "Fischer", "lisa@examplecom")
    
    with pytest.raises(ValueError):
        Student("5005", "Tim", "Weiss", "tim@example.com@")
