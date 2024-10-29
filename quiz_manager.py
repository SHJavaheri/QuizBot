class QuizManager:
    def __init__(self):
        self.questions = []
        self.is_active = False

    def start_new_quiz(self):
        self.questions = []
        self.is_active = True

    def add_question(self, question_type, question_text, answer_text, options=None, hint=None):
        # Define question structure
        question_data = {
            "type": question_type,
            "question": question_text,
            "answer": answer_text,
            "hint": hint  # Store the hint, even if it's None
        }

        # Add options if it's a multiple-choice question
        if question_type == "multiple_choice" and options:
            question_data["options"] = options

        # Append the question to the quiz
        self.questions.append(question_data)

    def end_quiz(self):
        self.is_active = False

    def get_questions(self):
        return self.questions

    def is_quiz_active(self):
        return self.is_active