class GradeBookError(ValueError):
    """Base class for all GradeBook exceptions."""
    pass


class StudentNotFoundError(GradeBookError):
    """Raised when a student is not found."""
    pass


class CourseNotFoundError(GradeBookError):
    """Raised when a course is not found."""
    pass


class GradeNotFoundError(GradeBookError):
    """Raised when a grade is not found."""
    pass


class ValidationError(GradeBookError):
    """Raised when data validation fails."""
    pass


class DuplicateEntryError(GradeBookError):
    """Raised when trying to add a student or course with an ID that already exists."""
    pass