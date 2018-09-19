from django.test import TestCase
from .models import Question, Quiz, Score, Answer, QuizCategory
from django.test import Client
from django.contrib.auth.models import User
import datetime


class CreateUsersMixin:
    def create_user(self, username, password, client):
        user = User.objects.create(username=username)
        user.set_password(password)
        user.save()
        client.login(username=username, password=password)
        return user

    def create_superuser(self, username, email, password, client):
        user = User.objects.create_superuser(username=username, email=email, password=password)
        user.set_password(password)
        user.save()
        client.login(username=username, password=password)
        return user


class CreateQuizMixin:
    def create_quiz(self, user):
        category = QuizCategory.objects.create(title="Test Category", number=1)
        quiz = Quiz.objects.create(name="Test Quiz", start_date="2000-10-10",
                                        end_date="2000-10-10", category=category, difficulty="&")
        question = Question.objects.create(question="Test Question", quiz=quiz, correct_answer="correct")
        question2 = Question.objects.create(question="Test Question2", quiz=quiz, correct_answer="correct")
        Answer.objects.create(question=question, answer="Test Answer")
        Answer.objects.create(question=question2, answer="Test Answer2")
        Score.objects.create(quiz=quiz, question=question, user=user, answered=False, correct=0)
        return {"quiz": quiz,  "q1": question, "q2": question2}


class TestPermissions(CreateUsersMixin, TestCase):

    def setUp(self):
        self.client = Client()
        self.create_user("testuser", "123456", self.client)

    def test_show_quizzes(self):
        response = self.client.get("")
        # Test that once logged in, allowed to see page
        self.assertEqual(response.status_code, 200)

    def test_redirect(self):
        self.client.logout()
        response = self.client.get("")
        # test that redirects if not logged in
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/?home=/')


class CreateViewTest(CreateUsersMixin, TestCase):

    def setUp(self):
        self.client = Client()
        self.create_user("testuser", "123456", self.client)

    def test_create_permissions_normal_user(self):
        response = self.client.get('/create/')
        # Should redirect if not super user
        self.assertEqual(response.status_code, 302)
        # Redirect to home page
        self.assertEqual(response.url, '/')

    def test_create_permissions_super_user(self):
        self.create_superuser("superuser", "test@email.com", "123456", self.client)
        response = self.client.get('/create/')
        # If super is logged in it should show page
        self.assertEqual(response.status_code, 200)


class CreatedQuizViewTest(CreateUsersMixin, TestCase):

    def setUp(self):
        self.client = Client()
        self.create_superuser("superuser", "test@email.com", "123456", self.client)
        QuizCategory.objects.create(title="Test Category", number=9)

    def test_create_current(self):
        current_date = datetime.date.today()
        response = self.client.post('/created/',
                               {'difficulty': '&', 'category': 1, 'tname': 'Test Quiz', 'sdate': current_date,
                                'edate': current_date})
        questions = Question.objects.all()
        # 10 questions should be created
        self.assertEqual(len(questions), 10)
        # Current quiz should have quiz
        self.assertQuerysetEqual(response.context['quizzes']['current'], ['<Quiz: Test Quiz>'])

    def test_create_coming_soon(self):
        week_away = datetime.date.today() + datetime.timedelta(days=7)
        response = self.client.post('/created/',
                                    {'difficulty': '&', 'category': 1, 'tname': 'Test Quiz', 'sdate': week_away,
                                     'edate': week_away})
        self.assertEqual(response.context['feedback'], 'Tournament successfully created!')
        # Coming soon quizzes should have quiz
        self.assertQuerysetEqual(response.context['quizzes']['coming_soon'], ['<Quiz: Test Quiz>'])

    def test_missed_quiz(self):
        week_ago = datetime.date.today() + datetime.timedelta(days=-7)
        response = self.client.post('/created/',
                                    {'difficulty': '&', 'category': 1, 'tname': 'Test Quiz', 'sdate': week_ago,
                                     'edate': week_ago})
        self.assertEqual(response.context['feedback'], 'Tournament successfully created!')
        # Quiz should not show because it is over
        self.assertQuerysetEqual(response.context['quizzes']['current'], [])


class TakeQuizViewTest(CreateUsersMixin, CreateQuizMixin, TestCase):

    def setUp(self):
        self.client = Client()
        self.normal_user = self.create_user("testuser", "123456", self.client)
        quiz_data = self.create_quiz(self.normal_user)
        self.quiz = quiz_data["quiz"]
        self.question = quiz_data["q1"]
        self.question2 = quiz_data["q2"]

    def test_load_quiz(self):
        response = self.client.get('/' + str(self.quiz.id))
        self.assertEqual(response.context['quiz'].name, 'Test Quiz')
        self.assertEqual(response.context['question'].question, 'Test Question')
        self.assertEqual(response.context['answers'][0].answer, 'Test Answer')

    def test_answer_question(self):

        post_response = self.client.post('/' + str(self.quiz.id),
                                         {'answer': 'correct', 'last_question': self.question.id})
        get_response = self.client.get('/' + str(self.quiz.id))
        updated_score = Score.objects.get(question=self.question)
        # Check that post redirects to get
        self.assertEqual(post_response.status_code, 302)
        # Check that score has been updated
        self.assertEqual(updated_score.correct, 1)
        self.assertEqual(updated_score.answered, True)
        # Check that next question displays
        self.assertEqual(get_response.context['question'].question, 'Test Question2')

    def test_answer_question_wrong(self):
        self.client.post('/' + str(self.quiz.id), {'answer': 'incorrect', 'last_question': self.question.id})
        updated_score = Score.objects.get(question=self.question)
        self.assertEqual(updated_score.correct, 0)

    def test_answer_last_question(self):
        Score.objects.create(quiz=self.quiz, question=self.question2, user=self.normal_user, answered=False, correct=0)
        self.client.post('/' + str(self.quiz.id), {'answer': 'incorrect', 'last_question': self.question.id})
        self.client.post('/' + str(self.quiz.id), {'answer': 'incorrect', 'last_question': self.question2.id})
        get_response = self.client.get('/' + str(self.quiz.id))
        self.assertEqual(get_response.context["score"], '0/2')

    def test_incomplete(self):
        response = self.client.get("")
        self.assertQuerysetEqual(response.context['quizzes']['incomplete'], ['<Quiz: Test Quiz>'])


class HighScoresTest(CreateUsersMixin, CreateQuizMixin, TestCase):
    def setUp(self):
        self.client = Client()
        self.normal_user = self.create_user("testuser", "123456", self.client)
        quiz_data = self.create_quiz(self.normal_user)
        self.quiz = quiz_data["quiz"]
        self.question = quiz_data["q1"]
        self.question2 = quiz_data["q2"]

    def test_high_scores(self):
        Score.objects.create(quiz=self.quiz, question=self.question2, user=self.normal_user, answered=True, correct=1)
        response = self.client.get("/highscores/")
        self.assertEqual(response.context["highscores"][0]["Scores"][0]["Score"], '1/2')

    def test_high_scores_2_users(self):
        self.test_high_scores()
        normal_user2 = self.create_user('testuser2', '123456', self.client)
        Score.objects.create(quiz=self.quiz, question=self.question, user=normal_user2, answered=True, correct=1)
        Score.objects.create(quiz=self.quiz, question=self.question2, user=normal_user2, answered=True, correct=1)
        response = self.client.get("/highscores/")
        self.assertEqual(str(response.context["highscores"][0]["Scores"]),
                         "[{'User': <User: testuser>, 'Score': '1/2'}, {'User': <User: testuser2>, 'Score': '2/2'}]")


class UpdateCategoriesTest(TestCase, CreateUsersMixin):

    def setUp(self):
        self.client = Client()
        self.superuser = self.create_superuser("superuser", "test@email.com", "123456", self.client)


    def test_categories(self):
        response = self.client.get("/update/")
        self.assertEqual(response.context["count"], 24)
        response2 = self.client.get("/update/")
        # Test it doesn't update again
        self.assertEqual(response2.context["count"], 0)

