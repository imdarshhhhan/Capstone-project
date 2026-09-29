from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

from app.db.sessions  import getDb
from app.db.models import QuestionPool, QuizAttempt, Assignment
from app.services.adaptive_engine import AdaptiveEngine
from app.api.auth import decodeSessionToken

router = APIRouter(prefix="/quizzes", tags=["Adaptive Assessment & Assignments"])

# ─── DATA SCHEMA STRUCTURES ───
class RequestQuestionSchema(BaseModel):
    conceptTag: str

class SubmitAnswerSchema(BaseModel):
    questionId: int
    chosenOption: str
    conceptTag: str

class AssignHomeworkSchema(BaseModel):
    title: str
    materialId: int
    dueDate: str # Format string pattern: YYYY-MM-DD HH:MM:SS


# ─── API ROUTE CONTROLLERS (CAMELCASE) ───

@router.post("/next-question", status_code=status.HTTP_200_OK)
def fetchAdaptiveQuestion(
    payload: RequestQuestionSchema,
    db: Session = Depends(getDb),
    currentUser: dict = Depends(decodeSessionToken)
):
    """
    [FEATURE 4: GENUINE ADAPTIVE ASSESSMENT]
    Queries the student's mastery tracker logs from PostgreSQL and 
    extracts the target question whose item difficulty matches their skill level.
    """
    studentId = currentUser.get("userId")
    
    # Run our camelCase mathematical target sorting routine block
    adaptiveQuestion = AdaptiveEngine.selectNextAdtvQ(db, studentId, payload.conceptTag)
    
    if not adaptiveQuestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insufficient item variants matching this concept tag inside the question bank."
        )

    # Return the clean question parameters, completely stripping away the correct answer key
    return {
        "questionId": adaptiveQuestion.id,
        "questionText": adaptiveQuestion.questionText,
        "optionsMatrix": adaptiveQuestion.optionsMatrix,
        "cognitiveLevel": adaptiveQuestion.cognitiveLevel
    }


@router.post("/submit-answer", status_code=status.HTTP_200_OK)
def evaluateStudentSubmission(
    payload: SubmitAnswerSchema,
    db: Session = Depends(getDb),
    currentUser: dict = Depends(decodeSessionToken)
):
    """
    [FEATURE 5: ITEM ANALYSIS & MASTERY UPDATING]
    Evaluates student answer accuracy, updates their decimal mastery record, 
    and recalculates the question's item difficulty parameters.
    """
    studentId = currentUser.get("userId")

    # 1. Fetch targeted item verification variables
    targetQuestion = db.query(QuestionPool).filter(QuestionPool.id == payload.questionId).first()
    if not targetQuestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Targeted assessment item reference not found."
        )

    # 2. Evaluate accuracy string match parameters
    isCorrect = targetQuestion.correctAnswer.strip().lower() == payload.chosenOption.strip().lower()

    # 3. Trigger psychometric recalculations using your custom camelCase algorithms
    newMasteryScore = AdaptiveEngine.updateStudentMastery(
        db, studentId, payload.conceptTag, targetQuestion.difficulty_index_p, isCorrect
    )
    
    newItemDifficultyP = AdaptiveEngine.updateItemDiffMetric(
        db, targetQuestion.id, isCorrect
    )

    return {
        "evaluationStatus": "correct" if isCorrect else "incorrect",
        "correctAnswerKey": targetQuestion.correctAnswer,
        "remediationQuote": targetQuestion.sourceQuote, # Feature 6: Evidence-based feedback
        "updatedStudentMastery": round(newMasteryScore, 4),
        "updatedItemDifficultyMetric": round(newItemDifficultyP, 4)
    }


@router.post("/assign", status_code=status.HTTP_201_CREATED)
def assignHomeworkActivity(
    payload: AssignHomeworkSchema,
    db: Session = Depends(getDb),
    currentUser: dict = Depends(decodeSessionToken)
):
    """
    [FEATURE - TEACHER: ASSIGN AN ACTIVITY / HOMEWORK]
    Links a lesson material item to a due date window constraint.
    """
    if currentUser.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: This operation requires teacher account permissions."
        )

    newAssignment = Assignment(
        title=payload.title,
        materialId=payload.materialId,
        teacherId=currentUser.get("userId"),
        dueDate=payload.dueDate
    )
    
    db.add(newAssignment)
    db.commit()
    db.refresh(newAssignment)

    return {
        "status": "success",
        "assignmentId": newAssignment.id,
        "title": newAssignment.title,
        "windowClosedAt": newAssignment.dueDate
    }
