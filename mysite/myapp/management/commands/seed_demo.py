"""Create a demo account with three weeks of realistic data, for the live demo.

Only ever touches the demo user (default username: demo). Safe to run on every
deploy: it does nothing if the demo user already exists, unless --reset is given.
"""
import os
import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import localdate

from myapp.models import Consume, Food, UserProfile, WeightLog

MEALS = {
    "breakfast": ["Oats, dry", "Banana", "Milk, whole", "Egg, boiled", "Whole wheat bread", "Curd / plain yogurt"],
    "lunch": ["White rice, cooked", "Dal (lentils), cooked", "Chapati / roti (wheat)", "Chicken breast, cooked",
              "Paneer", "Spinach", "Rajma (kidney beans), cooked"],
    "dinner": ["Chapati / roti (wheat)", "Dal (lentils), cooked", "Cauliflower", "Chicken breast, cooked",
               "Potato, boiled", "Curd / plain yogurt"],
    "snack": ["Apple", "Almonds", "Peanuts", "Orange", "Coconut water", "Dark chocolate"],
}
SERVING_GRAMS = (60, 90, 120, 150, 200)


class Command(BaseCommand):
    help = "Create a demo user (demo / DemoPass123!) with profile, 21 days of food logs and weight logs."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="demo")
        parser.add_argument("--days", type=int, default=21)
        parser.add_argument("--seed", type=int, default=7)
        parser.add_argument("--reset", action="store_true",
                            help="Delete this demo user's data and recreate it")

    @transaction.atomic
    def handle(self, *args, **opts):
        username = opts["username"]
        existing = User.objects.filter(username=username).first()
        if existing and not opts["reset"]:
            self.stdout.write(f"Demo user '{username}' already exists, skipping.")
            return
        if existing:
            existing.delete()  # cascades to that user's profile, logs, weight logs

        call_command("seed_foods", verbosity=0)
        rng = random.Random(opts["seed"])
        password = os.environ.get("DEMO_PASSWORD", "DemoPass123!")
        user = User.objects.create_user(username=username, password=password)

        UserProfile.objects.create(user=user, age=24, gender="male", height_cm=175, current_weight_kg=78,
                                   target_weight_kg=72, goal_type="lose", activity_level="moderate")

        foods = {f.name: f for f in Food.objects.filter(user__isnull=True)}
        today = localdate()
        logs = []
        for offset in range(opts["days"], -1, -1):
            day = today - timedelta(days=offset)
            if rng.random() < 0.08 and offset:   # the odd day with nothing logged
                continue
            for meal, names in MEALS.items():
                for name in rng.sample(names, k=rng.randint(1, 3) if meal != "snack" else 1):
                    logs.append(Consume(user=user, food_consumed=foods[name], meal_type=meal,
                                        quantity_grams=rng.choice(SERVING_GRAMS), date=day))
        Consume.objects.bulk_create(logs)

        weights = []
        for i, offset in enumerate(range(opts["days"], -1, -3)):
            weights.append(WeightLog(user=user, weight_kg=round(79.5 - i * 0.28 + rng.uniform(-0.15, 0.15), 1),
                                     date=today - timedelta(days=offset)))
        WeightLog.objects.bulk_create(weights)
        latest = max(weights, key=lambda w: w.date)
        UserProfile.objects.filter(user=user).update(current_weight_kg=latest.weight_kg)

        self.stdout.write(self.style.SUCCESS(
            f"Demo user '{username}' ready: {len(logs)} food logs, {len(weights)} weight logs."))
