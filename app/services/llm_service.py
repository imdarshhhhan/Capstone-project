import json
import ollama

class LLMService:
    def __init__(self, model_name="qwen2.5:3b"):
        self.model_name = model_name

    def generate_mcq(self, context: str, topic: str) -> dict:
#Asking the context based Mcq questions by giving the strict prompt and loading it into json format 

        system_instructions = (
            "You are an objective academic assessment engine. Read the context snippet provided "
            "and generate exactly ONE multiple-choice question. You must obey these rules:\n"
            "1. The question and factual answer must rely strictly on the facts within the context.\n"
            "2. The 'options' key must contain exactly 4 unique and distinct alternative string choices.\n"
            "3. Do not include markdown code wrappers like ```json. Return purely raw structural JSON text.\n\n"
            "Format Schema Matrix:\n"
            "{\n"
            "  \"question\": \"Targeted assessment question?\",\n"
            "  \"options\": [\"Choice A\", \"Choice B\", \"Choice C\", \"Choice D\"],\n"
            "  \"correct_answer\": \"The option string that explicitly satisfies the question\",\n"
            "  \"source_quote\": \"The precise sentence pulled word-for-word from the context proving the answer\"\n"
            "}"
        )

        user_prompt = f"Context Material:\n\"{context}\"\n\nGenerate one MCQ centered around the topic: {topic}"

        try:
            response = ollama.generate(
                model=self.model_name,
                system=system_instructions,
                prompt=user_prompt,
                options={"temperature": 0.2}
            )
            raw_text = response['response'].strip()
            return json.loads(raw_text)
        except Exception as e:
            return {"error": f"LLM generation failed: {str(e)}"}
