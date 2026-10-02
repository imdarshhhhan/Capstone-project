
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from  db.sessions import getDb
from  db.models import ContentMaterial
from  services.rag_service import RAGService
from  api.auth import verifyFirebaseTokenDependency


router = APIRouter(
    prefix="/documents",
    tags=["Teacher Content Management"]
)

ragService = RAGService()



class UploadMaterialSchema(BaseModel):
    title: str
    textBody: str

@router.post("/upload", status_code=status.HTTP_201_CREATED)
def processTeacherDocument(
    payload: UploadMaterialSchema,
    db: Session = Depends(getDb),
    currentFirebaseUser: dict = Depends(verifyFirebaseTokenDependency)
):
    """
    Creates a teacher content record in PostgreSQL
    and indexes its text content into ChromaDB.
    """

    # 1. Check Firebase-synchronized user role
    if currentFirebaseUser.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Teacher permissions required."
        )

    # 2. Get the teacher's database ID
    teacherId = currentFirebaseUser.get("userId")

    if not teacherId:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Teacher database ID not found."
        )

    newMaterialRecord = ContentMaterial(
        title=payload.title,
        generatedStudyGuide=payload.textBody[:200],
        teacherId=teacherId
    )

    db.add(newMaterialRecord)
    db.commit()
    db.refresh(newMaterialRecord)

    # Index content into ChromaDB
    try:
        totalChunksIndexed = ragService.add_document_content(
            payload.textBody
        )

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector database indexing failed: {str(e)}"
        )

    return {
        "status": "success",
        "materialId": newMaterialRecord.id,
        "title": newMaterialRecord.title,
        "chunksIndexed": totalChunksIndexed
    }
