from pydantic import BaseModel
from typing import List

class RequestQuestionSchema(BaseModel):
    conceptTag: str

class SubmitAnswerSchema(BaseModel):
    questionId: int
    chosenOption: str
    conceptTag: str
