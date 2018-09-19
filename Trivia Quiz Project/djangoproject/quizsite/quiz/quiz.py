import urllib.request, json, html
from .models import QuizCategory, Quiz, Question, Score, Answer
import datetime


class QuestionData:
    def __init__(self, question, correct_answer, incorrect_answers):
        self.question = html.unescape(question)
        self.correct_answer = html.unescape(correct_answer)
        self.incorrect_answers = []
        for i in incorrect_answers:
            self.incorrect_answers.append(html.unescape(i))


class CreateQuizMixin:

    """
        Create url to api based on post data.
        Get json data. Create quiz and questions from data
        Return message
    """
    def create_quiz(self, request):
        category = QuizCategory.objects.get(id=request.POST['category'])
        difficulty = request.POST['difficulty']
        string = 'https://opentdb.com/api.php?amount=10&category=' + category.number + '&difficulty=' \
                 + str(difficulty) + '&type=multiple'
        json = self.get_json(string)
        feedback = "Error creating tournament. Please try again with a different difficulty."
        # Only create quiz if no error in api call
        if json["response_code"] == 0:
        # Get or create stops same quiz being created twice
            quiz, created = Quiz.objects.get_or_create(name=request.POST['tname'],
                                                       start_date=request.POST['sdate'],
                                                       end_date=request.POST['edate'],
                                                       category=category,
                                                       difficulty=difficulty)
            self.create_questions(json, quiz)
            feedback = "Tournament successfully created!"
        return feedback

    def get_json(self, string):
        with urllib.request.urlopen(string) as url:
            return json.loads(url.read().decode())

    """
        Add questions and answers to database
    """
    def create_questions(self, json_data, quiz):
        questions = []

        for q in json_data["results"]:
            questions.append(QuestionData(q["question"], q["correct_answer"], q["incorrect_answers"]))

        for q in questions:
            created_question = Question.objects.create(quiz=quiz, question=q.question, correct_answer=q.correct_answer)
            Answer.objects.create(question=created_question, answer=q.correct_answer)
            Answer.objects.create(question=created_question, answer=q.incorrect_answers[0])
            Answer.objects.create(question=created_question, answer=q.incorrect_answers[1])
            Answer.objects.create(question=created_question, answer=q.incorrect_answers[2])


class GetQuizzesMixin:

    """
        Gets quizzes to diplay on home page
    """
    def get_unentered(self, user):
        all_quizzes = Quiz.objects.all()

        unentered = []
        for q in all_quizzes:
            scores = Score.objects.filter(user=user, quiz=q)
            if not scores.exists():
                unentered.append(q)

        return {"current": self.get_current(unentered),
                "coming_soon": self.get_coming_soon(unentered),
                "incomplete": self.get_incomplete(all_quizzes, user)}

    """
        If user hasn't answered all question, display in incomplete section
    """
    def get_incomplete(self, quizzes, user):
        incomplete = []

        for q in quizzes:
            scores = Score.objects.filter(quiz=q, user=user)
            answered = 0
            if scores.exists():
                for s in scores:
                    if s.answered:
                        answered += 1
                if 0 <= answered < 10:
                    print(answered)
                    incomplete.append(q)

            print(incomplete)
        return incomplete


    """
        If current date is between start and end date of quiz,
        display in current section
    """
    def get_current(self, quizzes):
        current = []
        current_date = datetime.date.today()
        for q in quizzes:
            if q.start_date <= current_date <= q.end_date:
                current.append(q)
        return current

    """
        If current date before start date, but start date is within a week,
        display in coming soon
    """
    def get_coming_soon(self, quizzes):
        coming_soon = []
        current_date = datetime.date.today()
        week_away = current_date+datetime.timedelta(days=7)
        for q in quizzes:
            if current_date < q.start_date <= week_away:
                coming_soon.append(q)
        return coming_soon

    


