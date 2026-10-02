import random
from datetime import datetime

from sqlalchemy.orm import Session

from  db.models import StudentMastery, QuestionPool, QuizAttempt


class AdaptiveEngine:

    @staticmethod
    def calculateMastery(
        current_mastery: float,
        question_difficulty: float,
        is_correct: bool
    ) -> float:
        """
        Calculate the student's new mastery score based on their answer.

        The score stays between 0.0 and 1.0. A correct answer increases
        mastery, while an incorrect answer decreases it.
        """

        # Controls how quickly the mastery score changes.
        alpha = 0.15

        # Convert the P-value into a difficulty value.
        actual_difficulty = 1.0 - question_difficulty

        if is_correct:
            # Correct answers increase mastery.
            # Harder questions give a slightly larger increase.
            growth_factor = (
                alpha
                * (1.0 - current_mastery)
                * (0.5 + actual_difficulty)
            )

            new_mastery = current_mastery + growth_factor

        else:
            # Incorrect answers decrease mastery.
            # Getting an easier question wrong gives a larger decrease.
            decay_factor = (
                alpha
                * current_mastery
                * (0.5 + question_difficulty)
            )

            new_mastery = current_mastery - decay_factor

        # Keep the score between 0.0 and 1.0.
        return max(0.0, min(1.0, new_mastery))


    @staticmethod
    def updateStudentMastery(
        db: Session,
        student_id: int,
        concept_tag: str,
        question_difficulty: float,
        is_correct: bool
    ) -> float:
        """
        Find or create the student's mastery record for a concept,
        update the score, and save it to the database.
        """

        # Find the student's existing mastery record for this concept.
        mastery_record = db.query(StudentMastery).filter(
            StudentMastery.student_id == student_id,
            StudentMastery.concept_tag == concept_tag
        ).first()

        # Create a new record if the student has not attempted this
        # concept before.
        if not mastery_record:
            mastery_record = StudentMastery(
                student_id=student_id,
                concept_tag=concept_tag,
                mastery_score=0.5
            )

            db.add(mastery_record)
            db.flush()

        # Calculate the new mastery score.
        updated_score = AdaptiveEngine.calculateMastery(
            current_mastery=mastery_record.mastery_score,
            question_difficulty=question_difficulty,
            is_correct=is_correct
        )

        # Update the record with the new score and timestamp.
        mastery_record.mastery_score = updated_score
        mastery_record.last_updated = datetime.utcnow()

        db.commit()

        return updated_score


    @staticmethod
    def selectNextAdtvQ(
        db: Session,
        student_id: int,
        concept_tag: str
    ) -> QuestionPool:
        """
        Select a question whose difficulty is close to the student's
        current mastery level for the given concept.
        """

        # Get the student's current mastery for this concept.
        mastery_record = db.query(StudentMastery).filter(
            StudentMastery.student_id == student_id,
            StudentMastery.concept_tag == concept_tag
        ).first()

        # Start at 0.5 if no mastery record exists yet.
        student_competence = (
            mastery_record.mastery_score
            if mastery_record
            else 0.5
        )

        # Get approved questions for this concept.
        question_candidates = db.query(QuestionPool).filter(
            QuestionPool.concept_tag == concept_tag,
            QuestionPool.is_approved_automatically == True
        ).all()

        if not question_candidates:
            return None

        # Convert mastery into the target P-value.
        target_p_index = 1.0 - student_competence

        # Put the questions closest to the target difficulty first.
        question_candidates.sort(
            key=lambda q: abs(
                q.difficulty_index_p - target_p_index
            )
        )

        # Pick randomly from the two closest questions
        # to avoid showing the exact same question every time.
        top_pool = question_candidates[:2]

        return random.choice(top_pool)


    @staticmethod
    def updateItemDiffMetric(
        db: Session,
        question_id: int,
        is_correct: bool
    ) -> float:
        """
        Update a question's difficulty value based on student attempts.

        P-value = number of correct answers / total attempts.
        """

        # Find the question.
        question = db.query(QuestionPool).filter(
            QuestionPool.id == question_id
        ).first()

        if not question:
            return 1.0

        # Record another attempt.
        question.total_attempts_logged += 1

        # Record the correct answer if applicable.
        if is_correct:
            question.correct_attempts_logged += 1

        # Calculate the new P-value.
        new_p_index = (
            question.correct_attempts_logged
            / question.total_attempts_logged
        )

        question.difficulty_index_p = new_p_index

        db.commit()

        return new_p_index