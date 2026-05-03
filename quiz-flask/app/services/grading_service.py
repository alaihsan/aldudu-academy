from app.helpers import matching_pair
from app.models import QuestionType


def grade_answer(question, payload):
    points = float(question.points or 0)
    qtype = question.question_type

    if qtype in (QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE, QuestionType.DROPDOWN):
        selected_id = payload.get("selected_option_id")
        selected = next((opt for opt in question.options if opt.id == selected_id), None)
        return points if selected and selected.is_correct else 0

    if qtype == QuestionType.CHECKBOX:
        selected_ids = set(payload.get("selected_option_ids") or [])
        correct_ids = {opt.id for opt in question.options if opt.is_correct}
        return points if correct_ids and selected_ids == correct_ids else 0

    if qtype == QuestionType.MATCHING:
        submitted = {str(k): str(v) for k, v in (payload.get("matching_answers") or {}).items()}
        correct = {}
        for option in question.options:
            left, right = matching_pair(option.option_text)
            if left and right:
                correct[left] = right
        return points if correct and submitted == correct else 0

    return 0


def total_possible_points(questions):
    return sum(float(question.points or 0) for question in questions)
