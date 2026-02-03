from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now


class Food(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100)
    calories = models.FloatField()
    carbs = models.FloatField()
    protein = models.FloatField()
    fat = models.FloatField()

    def __str__(self):
        return self.name


class Consume(models.Model):
    MEAL_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food_consumed = models.ForeignKey(Food, on_delete=models.CASCADE)
    date = models.DateField(default=now)
    meal = models.CharField(
        max_length=20,
        choices=MEAL_CHOICES,
        default='breakfast'
    )

    def __str__(self):
        return f"{self.user} ate {self.food_consumed} ({self.meal}) on {self.date}"
