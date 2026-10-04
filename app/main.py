from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from  db.sessions import engine
from  db.models import Base
from db.migrations import migrate_firebase_auth_schema

from  api import auth_router, documents_router, quizzes_router,dashboard_router
from config import settings

from  services.rag_service import RAGService
from  services.llm_service import LLMService
from  services.validator import QuestionValidator
Base.metadata.create_all(bind=engine)
migrate_firebase_auth_schema(engine)

app = FastAPI(title="AI Adaptive Quiz API")

# Configuration of CORS with frontend to make secure fetch requests
app.add_middleware(
    CORSMiddleware, #allowing the req coming from frontend
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_service = RAGService()
llm_service = LLMService()


app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(quizzes_router)
app.include_router(dashboard_router)  



@app.get("/")
def readSystemRoot():
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
    #source grounded generation
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
        
    # Generating the final structured assessment choice
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


@app.post("/create-test")
def create_test(payload: GenerationPayload):
    #topuc input and getting the results
    topic = payload.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Please enter a topic.")
    if len(topic) > 200:
        raise HTTPException(status_code=400, detail="Topic is too long (200 characters max).")

    try:
        questions = llm_service.generate_test(topic)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"questions": questions}
