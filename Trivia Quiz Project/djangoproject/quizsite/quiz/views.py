from .models import QuizCategory, Quiz, Question, Answer
from django.views import generic
from django.views.generic import View
from django.shortcuts import render, HttpResponseRedirect, reverse
from .score import GetScoreMixin
from .quiz import CreateQuizMixin, GetQuizzesMixin
from .play_quiz import PlayQuiz
from .categories import UpdateCategoriesMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
import random


class LoginMixin(LoginRequiredMixin):
    redirect_field_name = 'home'


class QuizListView(LoginMixin, GetQuizzesMixin, generic.ListView):

    context_object_name = 'quizzes'
    template_name = "quiz/quiz_list.html"

    def get_queryset(self):
        return self.get_unentered(self.request.user)


class CreateQuiz(UserPassesTestMixin, generic.ListView):

    def test_func(self):
        return self.request.user.is_staff

    model = QuizCategory
    template_name = "quiz/create.html"
    context_object_name = 'categories'
    login_url = 'home'
    redirect_field_name = ""


class Created(LoginMixin, GetQuizzesMixin, CreateQuizMixin, View):

    def post(self, request):
        feedback = self.create_quiz(request)
        quizzes = self.get_unentered(request.user)
        return render(request, 'quiz/created.html', {'feedback': feedback, 'quizzes': quizzes})


class HighScores(LoginMixin, GetScoreMixin, generic.ListView):

    template_name = "quiz/highscores.html"
    context_object_name = "highscores"

    def get_queryset(self):
        return self.get_scores(User.objects.all(), Quiz.objects.all())


class UpdateCategories(UserPassesTestMixin, CreateQuizMixin, UpdateCategoriesMixin, generic.ListView):

    def test_func(self):
        return self.request.user.is_staff

    template_name = "quiz/updated.html"
    context_object_name = "count"

    def get_queryset(self):
        string = "https://opentdb.com/api_category.php"
        json = self.get_json(string)
        count = self.update_categories(json)
        return count


class Play(PlayQuiz, LoginMixin, View):
    """
        This method is the logic of taking the quiz.
        It gets the question and previous question
        Gets answer for question
        Gets response base on last question
        If last question, go to results, else display next question
    """
    def get(self, request, **kwargs):
        quiz = Quiz.objects.get(pk=kwargs["pk"])
        questions = Question.objects.filter(quiz=quiz)
        question, last_question = self.get_questions(request, quiz, questions)
        answers = list(Answer.objects.filter(question=question))
        random.shuffle(answers)  # Make sure correct answer is in different spot each question
        question_count = self.get_question_count(quiz, request)
        response = self.get_response(last_question, request.user)
        template, context = self.check_if_last_question(question_count, request, quiz, response, question, answers, len(questions))
        return render(request, template, context)

    def post(self, request, **kwargs):
        self.update_score(request)
        return HttpResponseRedirect(reverse('play', kwargs={'pk': kwargs["pk"]}))