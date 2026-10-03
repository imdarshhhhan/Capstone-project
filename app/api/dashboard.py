from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.auth import verifyFirebaseTokenDependency
from db.models import (
    Assignment,
    ContentMaterial,
    QuestionPool,
    QuizAttempt,
    StudentMastery,
    User,
)
from db.sessions import getDb

router = APIRouter(prefix="/dashboard", tags=["Dashboards"])


def _requireRole(currentUser: dict, role: str) -> None:
    """Server-side role gate. The frontend redirect is only a convenience."""
    if currentUser["role"] != role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This dashboard is only available to {role} accounts.",
        )


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


@router.get("/teacher")
def readTeacherDashboard(
    db: Session = Depends(getDb),
    currentUser: dict = Depends(verifyFirebaseTokenDependency),
):
    _requireRole(currentUser, "teacher")
    teacherId = currentUser["userId"]

    materials = (
        db.query(ContentMaterial)
        .filter(ContentMaterial.teacherId == teacherId)
        .order_by(ContentMaterial.createdAt.desc())
        .all()
    )
    materialIds = [m.id for m in materials]
    materialTitles = {m.id: m.title for m in materials}

    questionCounts = dict(
        db.query(QuestionPool.materialId, func.count(QuestionPool.id))
        .filter(QuestionPool.materialId.in_(materialIds))
        .group_by(QuestionPool.materialId)
        .all()
    )

    assignments = (
        db.query(Assignment)
        .filter(Assignment.teacherId == teacherId)
        .order_by(Assignment.dueDate.desc())
        .all()
    )
    attemptCounts = dict(
        db.query(QuizAttempt.assignmentId, func.count(QuizAttempt.id))
        .filter(QuizAttempt.assignmentId.in_([a.id for a in assignments]))
        .group_by(QuizAttempt.assignmentId)
        .all()
    )

    return {
        "profile": currentUser,
        "stats": {
            "materials": len(materials),
            "assignments": len(assignments),
            "questionsInBank": sum(questionCounts.values()),
            "submissions": sum(attemptCounts.values()),
        },
        "materials": [
            {
                "id": m.id,
                "title": m.title,
                "createdAt": _iso(m.createdAt),
                "questionCount": questionCounts.get(m.id, 0),
            }
            for m in materials
        ],
        "assignments": [
            {
                "id": a.id,
                "title": a.title,
                "materialTitle": materialTitles.get(a.materialId, "Unknown material"),
                "dueDate": _iso(a.dueDate),
                "submissions": attemptCounts.get(a.id, 0),
            }
            for a in assignments
        ],
    }


@router.get("/student")
def readStudentDashboard(
    db: Session = Depends(getDb),
    currentUser: dict = Depends(verifyFirebaseTokenDependency),
):
    _requireRole(currentUser, "student")
    studentId = currentUser["userId"]
    now = datetime.utcnow()

    # Assignments + material title + teacher name in one query
    rows = (
        db.query(Assignment, ContentMaterial.title, User.fullName)
        .join(ContentMaterial, Assignment.materialId == ContentMaterial.id)
        .join(User, Assignment.teacherId == User.id)
        .order_by(Assignment.dueDate.asc())
        .all()
    )

    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.studentId == studentId)
        .order_by(QuizAttempt.attemptTimestamp.desc())
        .all()
    )
    bestScoreByAssignment: dict[int, float] = {}
    for attempt in attempts:
        if attempt.assignmentId is None or not attempt.totalQuestions:
            continue
        percent = attempt.score / attempt.totalQuestions * 100
        bestScoreByAssignment[attempt.assignmentId] = max(
            bestScoreByAssignment.get(attempt.assignmentId, 0.0), percent
        )

    assignmentTitles = {a.id: a.title for a, _, _ in rows}

    assignmentItems = []
    for assignment, materialTitle, teacherName in rows:
        done = assignment.id in bestScoreByAssignment
        # The due day is inclusive: overdue once the whole day has passed.
        overdue = assignment.dueDate + timedelta(days=1) <= now
        assignmentItems.append(
            {
                "id": assignment.id,
                "title": assignment.title,
                "materialTitle": materialTitle,
                "teacherName": teacherName,
                "dueDate": _iso(assignment.dueDate),
                "status": "completed" if done else ("overdue" if overdue else "open"),
                "bestScorePercent": (
                    round(bestScoreByAssignment[assignment.id], 1) if done else None
                ),
            }
        )

    mastery = (
        db.query(StudentMastery)
        .filter(StudentMastery.studentId == studentId)
        .order_by(StudentMastery.masteryScore.asc())  # weakest concepts first
        .all()
    )

    scored = [a for a in attempts if a.totalQuestions]
    averageScore = (
        round(sum(a.score / a.totalQuestions * 100 for a in scored) / len(scored), 1)
        if scored
        else None
    )

    return {
        "profile": currentUser,
        "stats": {
            "openAssignments": sum(1 for a in assignmentItems if a["status"] == "open"),
            "completedAssignments": sum(
                1 for a in assignmentItems if a["status"] == "completed"
            ),
            "averageScorePercent": averageScore,
            "conceptsTracked": len(mastery),
        },
        "assignments": assignmentItems,
        "mastery": [
            {
                "conceptTag": m.conceptTag,
                "masteryPercent": round(m.masteryScore * 100),
                "lastUpdated": _iso(m.lastUpdated),
            }
            for m in mastery
        ],
        "recentAttempts": [
            {
                "id": a.id,
                "assignmentTitle": assignmentTitles.get(a.assignmentId, "Practice quiz"),
                "scorePercent": (
                    round(a.score / a.totalQuestions * 100, 1) if a.totalQuestions else 0
                ),
                "attemptedAt": _iso(a.attemptTimestamp),
            }
            for a in attempts[:5]
        ],
    }