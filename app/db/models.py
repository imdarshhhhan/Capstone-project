import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Float, Boolean, Enum, Table
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class UserRole(str, enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"

class NotificationType(str, enum.Enum):
    SUBMISSION = "submission"     # Student finished an assignment
    ASSIGNMENT = "assignment"     # Teacher assigned a quiz
    GROUP_INVITE = "group_invite" # Joined a study group

# many-to-many bridge linking students to study groups
groupMembership = Table(
    "group_membership",
    Base.metadata,
    Column("student_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", Integer, ForeignKey("study_groups.id", ondelete="CASCADE"), primary_key=True),
    Column("joined_at", DateTime, default=datetime.utcnow)
)


class User(Base):
    """
    Tracks application users, hashes, and profiles.
    Permits clear dashboard splits for teachers vs students.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebaseUid = Column(String, unique=True, index=True, nullable=True)
    
    email = Column(String, unique=True, index=True, nullable=False)
    fullName = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    avatarUrl = Column(String, nullable=True)
    achievements = Column(JSON, default=list) 
    createdAt = Column(DateTime, default=datetime.utcnow)

    # Relationships
    folders = relationship("Folder", back_populates="owner", cascade="all, delete-orphan")
    materialsCreated = relationship("ContentMaterial", back_populates="teacher")
    assignmentsCreated = relationship("Assignment", back_populates="creator")
    quizAttempts = relationship("QuizAttempt", back_populates="student")
    masteries = relationship("StudentMastery", back_populates="student")
    ownedGroups = relationship("StudyGroup", back_populates="creator")
    joinedGroups = relationship("StudyGroup", secondary=groupMembership, back_populates="members")
    notifications = relationship("Notification", back_populates="recipient", cascade="all, delete-orphan")


class Folder(Base):
    """Subject-wise or exam-wise containers managed by students."""
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    folderType = Column(String, default="subject") # "subject" or "exam"
    ownerId = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="folders")
    savedQuizzes = relationship("SavedQuiz", back_populates="folder", cascade="all, delete-orphan")


class ContentMaterial(Base):
    """Saves texts uploaded or compiled by instructors for RAG generations."""
    __tablename__ = "content_materials"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    generatedStudyGuide = Column(String, nullable=True) # Summary generated notes text
    teacherId = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("User", back_populates="materialsCreated")
    questions = relationship("QuestionPool", back_populates="sourceMaterial", cascade="all, delete-orphan")


class QuestionPool(Base):
    """
    Main bank storing your verified questions. Holds validation status flags,
    Bloom's ratings, and running psychometric counts.
    """
    __tablename__ = "question_pool"

    id = Column(Integer, primary_key=True, index=True)
    materialId = Column(Integer, ForeignKey("content_materials.id", ondelete="CASCADE"), nullable=False)
    conceptTag = Column(String, index=True, nullable=False) # e.g. "Photosynthesis"
    cognitiveLevel = Column(String, default="Remember")    # Bloom's value
    questionText = Column(String, nullable=False)
    optionsMatrix = Column(JSON, nullable=False)            # 4 string options
    correctAnswer = Column(String, nullable=False)
    sourceQuote = Column(String, nullable=False)
    
    # Validation gates flags (Feature 2)
    isApprovedAutomatically = Column(Boolean, default=True)
    validationWarnings = Column(JSON, default=list)
    
    # Psychometrics (Feature 5)
    totalAttemptsLogged = Column(Integer, default=0)
    correctAttemptsLogged = Column(Integer, default=0)
    difficulty_index_p = Column(Float, default=1.0) # Correct / Total ratio

    sourceMaterial = relationship("ContentMaterial", back_populates="questions")


class Assignment(Base):
    """Activity mappings created by teachers tied to specific windows."""
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    materialId = Column(Integer, ForeignKey("content_materials.id"), nullable=False)
    teacherId = Column(Integer, ForeignKey("users.id"), nullable=False)
    availableWindowStart = Column(DateTime, default=datetime.utcnow)
    dueDate = Column(DateTime, nullable=False)

    creator = relationship("User", back_populates="assignmentsCreated")
    attempts = relationship("QuizAttempt", back_populates="assignment", cascade="all, delete-orphan")


class QuizAttempt(Base):
    """Logs individual assessment submissions along with context feedback."""
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    studentId = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assignmentId = Column(Integer, ForeignKey("assignments.id"), nullable=True) # None if practice test
    score = Column(Float, nullable=False)
    totalQuestions = Column(Integer, nullable=False)
    studentFeedbackNotes = Column(String, nullable=True) # Grounded remediation tips
    attemptTimestamp = Column(DateTime, default=datetime.utcnow)

    student = relationship("User", back_populates="quizAttempts")
    assignment = relationship("Assignment", back_populates="attempts")
    savedReferences = relationship("SavedQuiz", back_populates="attemptOrigin", cascade="all, delete-orphan")


class SavedQuiz(Base):
    """Saves links to quiz reviews bookmarked in specific student folders."""
    __tablename__ = "saved_quizzes"

    id = Column(Integer, primary_key=True, index=True)
    folderId = Column(Integer, ForeignKey("folders.id", ondelete="CASCADE"), nullable=False)
    attemptId = Column(Integer, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False)
    bookmarkedAt = Column(DateTime, default=datetime.utcnow)

    folder = relationship("Folder", back_populates="savedQuizzes")
    attemptOrigin = relationship("QuizAttempt", back_populates="savedReferences")


class StudyGroup(Base):
    """Collaborative student group workspaces initialized via unique join codes."""
    __tablename__ = "study_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    uniqueGroupCode = Column(String, unique=True, index=True, nullable=False)
    creatorId = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    creator = relationship("User", back_populates="ownedGroups")
    members = relationship("User", secondary=groupMembership, back_populates="joinedGroups")


class StudentMastery(Base):
    """Maintains a decimal mastery competency track per student per concept."""
    __tablename__ = "student_mastery"

    id = Column(Integer, primary_key=True, index=True)
    studentId = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conceptTag = Column(String, index=True, nullable=False)
    masteryScore = Column(Float, default=0.5)
    lastUpdated = Column(DateTime, default=datetime.utcnow)

    student = relationship("User", back_populates="masteries")


class Notification(Base):
    """Dispatches tracking indicators like submissions or homework announcements."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipientId = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notificationType = Column(Enum(NotificationType), nullable=False)
    messageBody = Column(String, nullable=False)
    isRead = Column(Boolean, default=False)
    createdAt = Column(DateTime, default=datetime.utcnow)

    recipient = relationship("User", back_populates="notifications")
