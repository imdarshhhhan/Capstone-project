from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

#db functions
from  db.sessions import getDb
from  db.models import QuestionPool, Assignment

# adaptive engine
from  services.adaptive_engine import AdaptiveEngine

from  api.auth import verifyFirebaseTokenDependency

# chema checkpoints
from  schemas.question import RequestQuestionSchema, SubmitAnswerSchema
from  schemas.quiz import AssignHomeworkSchema

from  api.auth import verifyFirebaseTokenDependency

from  api.auth import verifyFirebaseTokenDependency


router = APIRouter(prefix="/quizzes", tags=["Adaptive Assessment & Assignments"])

@router.post("/next-question", status_code=status.HTTP_200_OK)
def fetchAdaptiveQuestion(
    payload: RequestQuestionSchema,
    db: Session = Depends(getDb),
    currentUser: dict = Depends(verifyFirebaseTokenDependency) # <-- Updated right here!
):
    studentId = currentUser.get("userId")


@router.post("/next-question", status_code=status.HTTP_200_OK)
def fetchAdaptiveQuestion(
    payload: RequestQuestionSchema,
    db: Session = Depends(getDb),
    currentUser: dict = Depends(verifyFirebaseTokenDependency)
):
    studentId = currentUser.get("userId")


@router.post("/next-question", status_code=status.HTTP_200_OK)
def fetchAdaptiveQuestion(
    payload: RequestQuestionSchema,
    db: Session = Depends(getDb),
    currentFirebaseUser: dict = Depends(verifyFirebaseTokenDependency)
):
    #feature 4  : Adaptive engine
    studentId = currentFirebaseUser.get("userId") if currentFirebaseUser else 1
    
    # item response theory 
    adaptiveQuestion = AdaptiveEngine.selectNextAdtvQ(db, studentId, payload.conceptTag)
    
    if not adaptiveQuestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insufficient item variants matching this concept tag inside the question bank."
        )

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
    currentFirebaseUser: dict = Depends(verifyFirebaseTokenDependency)
):
    studentId = currentFirebaseUser.get("userId") if currentFirebaseUser else 1

    # fetching row from PostgreSQL
    targetQuestion = db.query(QuestionPool).filter(QuestionPool.id == payload.questionId).first()
    if not targetQuestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Targeted assessment item reference not found."
        )
    isCorrect = targetQuestion.correctAnswer.strip().lower() == payload.chosenOption.strip().lower()

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
    currentFirebaseUser: dict = Depends(verifyFirebaseTokenDependency) 
):
    """
    [FEATURE - TEACHER: ASSIGN AN ACTIVITY / HOMEWORK]
    Links a lesson material item to a due date window constraint.
    """
    if currentFirebaseUser.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: This operation requires teacher account permissions."
        )

    newAssignment = Assignment(
        title=payload.title,
        materialId=payload.materialId,
        teacherId=currentFirebaseUser.get("userId") if currentFirebaseUser else 1,
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
