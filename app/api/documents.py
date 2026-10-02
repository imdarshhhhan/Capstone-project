from fastapi import APIRouter, Depends, HTTPException, status,router
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Import our session database portals and data tables
from app.db.sessions import getDb
from app.db.models import ContentMaterial
from app.services.rag_service import RAGService

# Import our fresh Firebase token verification handler directly from our authentication module
from app.api.auth import verifyAndSyncFirebaseLogin


# Update your import line near the top:
from app.api.auth import verifyFirebaseTokenDependency

@router.post("/upload", status_code=status.HTTP_201_CREATED)
def processTeacherDocument(
    payload: UploadMaterialSchema, 
    db: Session = Depends(getDb),
    currentUser: dict = Depends(verifyFirebaseTokenDependency) # <-- Updated right here!
):
    if currentUser.get("role") != "teacher":
        # ... (Rest of your code stays exactly the same)



        router = APIRouter(prefix="/documents", tags=["Teacher Content Management"])
ragService = RAGService()

# ─── DATA INPUT VALIDATION SCHEMAS ───
class UploadMaterialSchema(BaseModel):
    title: str
    textBody: str

@router.post("/upload", status_code=status.HTTP_201_CREATED)
def processTeacherDocument(
    payload: UploadMaterialSchema, 
    db: Session = Depends(getDb),
    # We call our login validator as a secure dependency check block
    currentFirebaseUser: dict = Depends(verifyAndSyncFirebaseLogin)
):
    """
    [FEATURE: CREATE CONTENT & GENERATE STUDY MATERIALS]
    Validates user credentials via Firebase tokens, writes a context record 
    to PostgreSQL rows, and streams text blocks down to ChromaDB.
    """
    # Security Gateway: Read the synchronized database role parameters safely
    if currentFirebaseUser.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: This operational control dashboard requires teacher permissions."
        )

    # 1. Store a tracking entry inside our PostgreSQL tables
    newMaterialRecord = ContentMaterial(
        title=payload.title,
        generatedStudyGuide=payload.textBody[:200], # Provide a short snippet preview block
        teacherId=1 # Temporary hardcoded layout index until user tables lock together cleanly
    )
    db.add(newMaterialRecord)
    db.commit()
    db.refresh(newMaterialRecord)

    # 2. Slice text inputs and stream chunks into ChromaDB
    try:
        totalChunksIndexed = ragService.add_document_content(payload.textBody)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector Database Indexing Exception: {str(e)}"
        )

    return {
        "status": "success",
        "materialId": newMaterialRecord.id,
        "title": newMaterialRecord.title,
        "chunksIndexed": totalChunksIndexed
    }
