from fastapi import APIRouter, Depends, HTTPException, status,router
from sqlalchemy.orm import Session

# Import our foundational connections, databases, and algorithms
from app.db.sessions import getDb
from app.db.models import QuestionPool, Assignment

# Import our new camelCase mathematical adaptive logic engine
from app.services.adaptive_engine import AdaptiveEngine

# ─── UPDATE: IMPORT FIREBASE USER VERIFICATION DIRECTLY FROM AUTH ───
from app.api.auth import verifyAndSyncFirebaseLogin

# Import our schema checkpoints
from app.schemas.question import RequestQuestionSchema, SubmitAnswerSchema
from app.schemas.quiz import AssignHomeworkSchema


# Change your import line near line 10 to fetch our clean checker function:
from app.api.auth import verifyFirebaseTokenDependency

# Change your import line near line 10 to fetch our clean checker function:
from app.api.auth import verifyFirebaseTokenDependency

# Update your route controllers to load the checker as their secure dependency:
@router.post("/next-question", status_code=status.HTTP_200_OK)
def fetchAdaptiveQuestion(
    payload: RequestQuestionSchema,
    db: Session = Depends(getDb),
    currentUser: dict = Depends(verifyFirebaseTokenDependency) # <-- Updated right here!
):
    studentId = currentUser.get("userId")
    # ... (Rest of your code stays exactly the same)


# Update your route controllers to load the checker as their secure dependency:
@router.post("/next-question", status_code=status.HTTP_200_OK)
def fetchAdaptiveQuestion(
    payload: RequestQuestionSchema,
    db: Session = Depends(getDb),
    currentUser: dict = Depends(verifyFirebaseTokenDependency) # <-- Updated right here!
):
    studentId = currentUser.get("userId")


router = APIRouter(prefix="/quizzes", tags=["Adaptive Assessment & Assignments"])

# ─── API ROUTE CONTROLLERS (SECURE CAMELCASE) ───

@router.post("/next-question", status_code=status.HTTP_200_OK)
def fetchAdaptiveQuestion(
    payload: RequestQuestionSchema,
    db: Session = Depends(getDb),
    # Secure dependency gate checking the active Firebase session
    currentFirebaseUser: dict = Depends(verifyAndSyncFirebaseLogin)
):
    """
    [FEATURE 4: GENUINE ADAPTIVE ASSESSMENT]
    Queries the student's mastery tracker and extracts the optimal question 
    whose item difficulty matches their skill level.
    """
    # Look up the custom synchronized profile row ID from your database map
    studentId = currentFirebaseUser.get("userId") if currentFirebaseUser else 1
    
    # Run your custom human-engineered camelCase mathematical selection algorithm
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
    currentFirebaseUser: dict = Depends(verifyAndSyncFirebaseLogin)
):
    """
    [FEATURE 5: ITEM ANALYSIS & MASTERY UPDATING]
    Evaluates student answer accuracy, updates their decimal mastery records,
    and recalculates the question's item difficulty metrics over time.
    """
    studentId = currentFirebaseUser.get("userId") if currentFirebaseUser else 1

    # 1. Fetch the targeted item row from PostgreSQL
    targetQuestion = db.query(QuestionPool).filter(QuestionPool.id == payload.questionId).first()
    if not targetQuestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Targeted assessment item reference not found."
        )

    # 2. Evaluate string accuracy parameters
    isCorrect = targetQuestion.correctAnswer.strip().lower() == payload.chosenOption.strip().lower()

    # 3. Trigger running psychometric updates using your clean camelCase methods
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
    # ─── THE FIXED LINE IS RIGHT HERE ───
    currentFirebaseUser: dict = Depends(verifyAndSyncFirebaseLogin) 
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
