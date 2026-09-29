from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Import our session portal and data models
from app.db.sessions import getDb
from app.db.models import ContentMaterial
from app.services.rag_service import RAGService
from app.api.auth import decodeSessionToken

router = APIRouter(prefix="/documents", tags=["Teacher Content Management"])
ragService = RAGService()

class UploadMaterialSchema(BaseModel):
    title: str
    textBody: str

@router.post("/upload", status_code=status.HTTP_201_CREATED)
def processTeacherDocument(
    payload: UploadMaterialSchema, 
    db: Session = Depends(getDb),
    currentUser: dict = Depends(decodeSessionToken)
):
    """
    [FEATURE: CREATE CONTENT & STUDY MATERIALS]
    Validates user credentials, inserts a material record into PostgreSQL, 
    and streams the text context down to our local ChromaDB cluster.
    """
    # Security Gateway: Verify that only teachers can ingest study material records
    if currentUser.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: This operation requires teacher account permissions."
        )

    # 1. Create a historical record tracking entry inside PostgreSQL
    newMaterialRecord = ContentMaterial(
        title=payload.title,
        raw_text_preview=payload.textBody[:200], # Keep a compact summary preview text
        teacher_id=currentUser.get("userId")
    )
    db.add(newMaterialRecord)
    db.commit()
    db.refresh(newMaterialRecord)

    # 2. Extract, chunk, and index the text body inside our local vector engine
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
