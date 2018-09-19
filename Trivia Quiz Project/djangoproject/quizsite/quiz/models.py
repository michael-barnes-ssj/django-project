from django.db import models
from django.contrib.auth.models import User

# Create your models here.

Difficulty = (
    ('&', 'No preference'), # if you pass '&' to api, it returns all
    ('e', 'Easy'),
    ('m', 'Medium'),
    ('h', 'Hard'),
)

"""
    Storing quiz categories in model so it doesn't have to call api every time a quiz is being created.
    Instead, admin has access to an update categories link the fills the category list form the api
"""
class QuizCategory(models.Model):
    title = models.CharField(max_length=255)
    number = models.CharField(null=True, blank=True, max_length=2)

    def __str__(self):
        return self.title

class Quiz(models.Model):
    name = models.CharField(max_length=255)
    start_date = models.DateField(auto_now=False)
    end_date = models.DateField(auto_now=False)
    category = models.ForeignKey(QuizCategory, on_delete=models.CASCADE)
    difficulty = models.CharField(
        max_length=1,
        choices=Difficulty,
        default='&'
    )

    def __str__(self):
        return self.name


class Question(models.Model):
    question = models.CharField(max_length=255)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    correct_answer = models.CharField(max_length=255)

    def __str__(self):
        return self.question

    class Meta:
        ordering = ['question']


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.CharField(max_length=255)

    def __str__(self):
        return str(self.question) + ": " + str(self.answer)


class Score(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    correct = models.PositiveSmallIntegerField(default=0)
    answered = models.BooleanField(default=False)

    def __str__(self):
        return str(self.quiz) + ": " + str(self.user) + ": " + str(self.correct)







