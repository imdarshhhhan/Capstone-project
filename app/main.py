from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.db.sessions import engine
from app.db.models import Base

from app.api import  auth, documents ,quizzes

from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.services.validator import QuestionValidator
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Adaptive Quiz API")

# Configure CORS so frontend can make secure fetch requests
app.add_middleware(
    CORSMiddleware, #allowing the req coming from frontend
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate service objects
rag_service = RAGService()
llm_service = LLMService()


app.include_router(auth.router)
app.include_router(documents.router)
@app.get("/")
def readSystemRoot():
    """Simple health check endpoint to confirm the server is responsive."""
    return {"status": "online", "engine": "FastAPI Core", "database": "Connected"}

# Pydantic schemas to validate raw incoming  data
class DocumentPayload(BaseModel):
    text: str #text must be string

class GenerationPayload(BaseModel):  #post the data / generate questions
    topic: str

@app.post("/ingest")
def ingest_document(payload: DocumentPayload):
    """Endpoint for uploading study materials."""
    try:
        total_chunks = rag_service.add_document_content(payload.text)
        return {"status": "success", 
                "chunks_indexed": total_chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-quiz")
def generate_quiz_question(payload: GenerationPayload):
    """Endpoint to trigger source-grounded question creation."""
    #  Look up the vector data matching the student's request
    context, is_grounded = rag_service.retrieve_grounded_context(payload.topic)
    
    if not context:
        raise HTTPException(
            status_code=404, 
            detail="No documentation content found."
        )
        
    # Groundedness 
    if not is_grounded:
        raise HTTPException(
            status_code=422, 
            detail="Source-Grounded Abort: Uploaded notes do not contain sufficient content on this topic."
        )
        
    #  Generate the final structured assessment choice
    quiz_question = llm_service.generate_mcq(
                        context,
                        payload.topic
                    )
    #validation tag
    is_valid, validation_flags = QuestionValidator.validate_mcq_structure(quiz_question)
    
    # Append the evaluation flags directly to the API response object schema
    quiz_question["is_approved_automatically"] = is_valid
    quiz_question["validation_warnings"] = validation_flags
    return quiz_question
