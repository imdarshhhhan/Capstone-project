import json
import re
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

    def generate_test(self, topic: str, num_questions: int = 6) -> list[dict]:
        """Generates a multiple-choice test on a topic (no uploaded notes needed).
        Returns 5-10 questions shaped like {"question", "options", "answer"}."""
        system_instructions = (
            "You are an objective academic assessment engine. Write multiple-choice questions "
            "that test a student's understanding of the topic you are given. Rules:\n"
            "1. Every question must be clear, factually correct and different from the others.\n"
            "2. Every question has exactly 4 unique options.\n"
            "3. 'answer' must be the exact text of the one correct option.\n"
            "4. Never use 'All of the above' or 'None of the above' as an option.\n"
            "5. Return only raw JSON in this shape:\n"
            "{\"questions\": [{\"question\": \"...\", \"options\": [\"...\", \"...\", \"...\", \"...\"], \"answer\": \"...\"}]}"
        )
        user_prompt = f"Topic: {topic}\nWrite {num_questions} multiple-choice questions."

        for _ in range(2):  # small local models sometimes return bad JSON, so try twice
            try:
                response = ollama.generate(
                    model=self.model_name,
                    system=system_instructions,
                    prompt=user_prompt,
                    format="json",
                    options={"temperature": 0.3},
                )
            except Exception as e:
                raise RuntimeError(
                    f"Could not get a response from the AI model '{self.model_name}'. "
                    f"Make sure Ollama is running and the model is installed. Details: {e}"
                ) from e

            try:
                data = json.loads(response["response"])
            except (json.JSONDecodeError, KeyError, TypeError):
                continue

            questions = self._clean_questions(data)
            if len(questions) >= 5:
                return questions[:10]

        raise RuntimeError("The AI model did not return enough valid questions. Please try again.")

    @staticmethod
    def _clean_questions(data) -> list[dict]:
        """Keeps only well-formed questions: 4 unique options and an answer that is one of them."""
        items = data.get("questions") if isinstance(data, dict) else data
        if not isinstance(items, list):
            return []

        def strip_label(text: str) -> str:  # "A) Process" -> "Process"
            return re.sub(r"^\(?[A-Da-d][\).:]\s+", "", text.strip())

        cleaned = []
        for item in items:
            if not isinstance(item, dict):
                continue
            question = str(item.get("question", "")).strip()
            raw_options = item.get("options")
            if not question or not isinstance(raw_options, list):
                continue

            options = [strip_label(str(o)) for o in raw_options if str(o).strip()]
            if len(options) != 4 or len({o.lower() for o in options}) != 4:
                continue

            raw_answer = str(item.get("answer", item.get("correct_answer", ""))).strip()
            answer = next((o for o in options if o.lower() == strip_label(raw_answer).lower()), None)
            if answer is None:  # the model answered with just a letter like "B"
                letter = re.fullmatch(r"\(?([A-Da-d])[\).:]?", raw_answer)
                if letter:
                    answer = options[ord(letter.group(1).upper()) - ord("A")]
            if answer is None:
                continue

            cleaned.append({"question": question, "options": options, "answer": answer})
        return cleaned
