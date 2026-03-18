from app.extensions import db

from .school import School, SchoolStatus
from .user import User, UserRole
from .course import Course, AcademicYear, Link, File, enrollments, UserCourseOrder, KbmNote, KbmActivityType
from .quiz import Quiz, Question, Option, QuizSubmission, Answer, QuestionType, GradeType, QuizStatus
from .discussion import Discussion, Post, Like
from .issue import Issue, IssueStatus, IssuePriority
from .ticket import Ticket, TicketMessage, TicketCategory, TicketStatus, TicketPriority
from .token import EmailVerificationToken, PasswordResetToken
from .activity_log import ActivityLog
from .gradebook import GradeCategory, GradeCategoryType, LearningObjective, LearningGoal, GradeItem, GradeEntry
from .assignment import Assignment, AssignmentSubmission, AssignmentStatus, AssignmentSubmissionStatus
