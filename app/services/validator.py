
class QuestionValidator:

    @staticmethod
    def validate_mcq_structure(quiz_data: dict) -> tuple[bool, list[str]]:
        """
        Checks whether the generated MCQ has the required fields,
        four valid options, and a valid correct answer.
        """

        errors = []

        # Check that all required fields are present
        required_fields = [
            "question",
            "options",
            "correct_answer",
            "source_quote"
        ]

        for field in required_fields:
            if field not in quiz_data or not quiz_data[field]:
                errors.append(f"Missing or empty field: '{field}'")
                return False, errors

        question = quiz_data["question"]
        options = quiz_data["options"]
        correct_answer = quiz_data["correct_answer"]
        source_quote = quiz_data["source_quote"]

        # An MCQ should have exactly 4 options
        if len(options) != 4:
            errors.append(
                f"Expected 4 options, but got {len(options)}"
            )

        # Check for duplicate options
        normalized_options = {
            option.strip().lower()
            for option in options
            if isinstance(option, str)
        }

        if len(normalized_options) != len(options):
            errors.append("Duplicate options found")

        # The correct answer should be one of the given options
        if correct_answer not in options:
            errors.append(
                f"Correct answer '{correct_answer}' is not in the options"
            )

        # Avoid common weak MCQ choices
        weak_options = {
            "all of the above",
            "none of the above",
            "both a and b",
            "neither a nor b"
        }

        for option in options:
            if str(option).strip().lower() in weak_options:
                errors.append(
                    f"Weak option found: '{option}'"
                )

        # If there are no errors, the question is valid
        return len(errors) == 0, errors