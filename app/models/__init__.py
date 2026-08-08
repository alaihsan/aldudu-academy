from app.core.extensions import db

from .school import School, SchoolStatus
from .user import User, UserRole
from .course import Course, AcademicYear, Link, File, enrollments, UserCourseOrder
from app.kbm.models import KbmNote, KbmActivityType
from .content_folder import ContentFolder
from app.quiz.models import (
    Quiz, Question, Option, QuizSubmission, Answer,
    QuestionType, GradeType, QuizStatus,
    BloomLevel, QuestionBloomTaxonomy,
)
from .discussion import Discussion, Post, Like
from .issue import Issue, IssueStatus, IssuePriority
from .ticket import Ticket, TicketMessage, TicketCategory, TicketStatus, TicketPriority
from .token import EmailVerificationToken, PasswordResetToken
from .activity_log import ActivityLog
from app.gradebook.models import GradeCategory, GradeCategoryType, LearningObjective, LearningGoal, GradeItem, GradeEntry
from app.assignment.models import Assignment, AssignmentSubmission, AssignmentStatus, AssignmentSubmissionStatus
from app.whats_new.models import WhatsNew
