from .models import Score, Quiz, Question, Answer
from django.contrib.auth.models import User


class GetScoreMixin:
    """
    For each quiz, create an object that gets the score of each user who has
    a score in that quiz
    """
    def get_scores(self, users, quizzes):
        high_scores = []
        for quiz in quizzes:
            quiz_scores = {"Quiz": quiz.name, "Scores": []}
            questions = Question.objects.filter(quiz=quiz)
            quiz_has_score = False
            # Check each quiz
            for u in users:
                user_has_score = False
                score = 0
                # Get questions in quiz
                for q in questions:
                    scores = Score.objects.filter(quiz=quiz, question=q, user=u)
                    # Get scores of each question
                    # If a question has been answered, calculated total
                    if scores.exists():
                        user_has_score = True
                        for s in scores:
                            score += s.correct
                if user_has_score:
                    quiz_has_score = True
                    quiz_scores["Scores"].append({"User": u, "Score": str(score)+"/"+str(len(questions))})
            if quiz_has_score:
                high_scores.append(quiz_scores)
        return high_scores
















