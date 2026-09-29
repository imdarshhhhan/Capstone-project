from pydantic import BaseModel

class AssignHomeworkSchema(BaseModel):
    title: str
    materialId: int
    dueDate: str # Structured string expectation pattern matching: YYYY-MM-DD
