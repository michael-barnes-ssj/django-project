
from .models import QuizCategory

class UpdateCategoriesMixin:

    def update_categories(self, json):
        count = 0
        # If '&' is passe dto api it returns all
        QuizCategory.objects.get_or_create(title="No Preference", number="&")
        for q in json["trivia_categories"]:
            category, created = QuizCategory.objects.get_or_create(title=q["name"], number=q["id"])
            if created:
                count += 1

        return count
