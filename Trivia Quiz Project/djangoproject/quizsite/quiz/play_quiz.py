from .models import QuizCategory, Quiz, Question, Score, Answer
from .score import GetScoreMixin


class PlayQuiz(GetScoreMixin):

    """
        Updates score based on post data
    """
    def update_score(self, request):
        question = Question.objects.get(id=request.POST.get('last_question'))
        score = Score.objects.get(question=question, user=request.user)
        if score.answered is False:
            if request.POST.get('answer') == question.correct_answer:
                score.correct = 1
                score.answered = True
                score.save()
            else:
                score.answered = True
                score.save()

    """ 
        Returns current question and last question
        Loop through all questions, and break when question is created
        Also break if question hasn't been answered
        This will bring the user back to the last question they were on if they exit quiz
    """
    def get_questions(self, request, quiz, questions):
        question = None
        last_question = None
        for q in questions:
            last_question = question
            question = q
            s, c = Score.objects.get_or_create(user=request.user, quiz=quiz, question=question)
            if c or s.answered is False:
                break
        return question, last_question

    """
        Gets count of current question 
    """
    def get_question_count(self, quiz, request):
        scores = Score.objects.filter(quiz=quiz, user=request.user)
        score_count = 0
        for s in scores:
            if s.answered is True:
                score_count += 1
        return score_count

    """
        Gets response based on last question score
    """
    def get_response(self, last_question, user):
        response = None
        if last_question:
            score = Score.objects.get(question=last_question, user=user)
            if score.correct == 1:
                response = "Correct!!"
            else:
                response = "Incorrect, the answer was: " + last_question.correct_answer

        return response

    """
        If last question, get score and go to final score page.
        Else, display question
    """
    def check_if_last_question(self, question_count, request, quiz, response, question, answers, questions_length):
        if question_count == questions_length:
            score = self.get_scores([request.user], [quiz])
            return 'quiz/final_score.html', {"score": score[0]["Scores"][0]["Score"], "response": response}
        else:
            return 'quiz/quiz_detail.html', {"quiz": quiz,
                                             "question": question,
                                             "answers": answers,
                                             "response": response,
                                             "number": (question_count + 1)}
