import csv
import os
from collections import defaultdict

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from myapp.models import Consume, Food, UserProfile, WeightLog


class Command(BaseCommand):
    help = "Export clean CSV files for Power BI dashboard"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            help="Export data for a specific username only, example: --username aryan",
        )

    def handle(self, *args, **options):
        username = options.get("username")

        export_dir = os.path.join(settings.BASE_DIR, "powerbi_exports")
        os.makedirs(export_dir, exist_ok=True)

        if username:
            try:
                selected_user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(f"User '{username}' does not exist.")

            users_filter = {"user": selected_user}
            self.stdout.write(self.style.WARNING(f"Exporting data only for user: {username}"))
        else:
            selected_user = None
            users_filter = {}
            self.stdout.write(self.style.WARNING("Exporting data for all users"))

        foods = Food.objects.filter(**users_filter).select_related("user")
        consumption_logs = Consume.objects.filter(**users_filter).select_related(
            "user", "food_consumed"
        )
        user_profiles = UserProfile.objects.filter(**users_filter).select_related("user")
        weight_logs = WeightLog.objects.filter(**users_filter).select_related("user")

        self.export_foods(export_dir, foods)
        self.export_consumption_logs(export_dir, consumption_logs)
        self.export_user_profiles(export_dir, user_profiles)
        self.export_weight_logs(export_dir, weight_logs)
        self.export_daily_nutrition_summary(export_dir, consumption_logs)

        self.stdout.write(self.style.SUCCESS("Power BI CSV export completed successfully."))
        self.stdout.write(self.style.SUCCESS(f"Export folder: {export_dir}"))

    def export_foods(self, export_dir, foods):
        file_path = os.path.join(export_dir, "foods.csv")

        with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "food_id",
                    "user_id",
                    "username",
                    "food_name",
                    "category",
                    "calories_per_100g",
                    "carbs_per_100g",
                    "protein_per_100g",
                    "fat_per_100g",
                    "created_at",
                ]
            )

            for food in foods:
                writer.writerow(
                    [
                        food.id,
                        food.user.id,
                        food.user.username,
                        food.name,
                        food.category,
                        food.calories,
                        food.carbs,
                        food.protein,
                        food.fat,
                        getattr(food, "created_at", ""),
                    ]
                )

    def export_consumption_logs(self, export_dir, consumption_logs):
        file_path = os.path.join(export_dir, "consumption_logs.csv")

        with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "consume_id",
                    "user_id",
                    "username",
                    "food_id",
                    "food_name",
                    "food_category",
                    "date",
                    "meal_type",
                    "quantity_grams",
                    "calories_consumed",
                    "carbs_consumed",
                    "protein_consumed",
                    "fat_consumed",
                    "created_at",
                ]
            )

            for log in consumption_logs:
                food = log.food_consumed

                writer.writerow(
                    [
                        log.id,
                        log.user.id,
                        log.user.username,
                        food.id,
                        food.name,
                        food.category,
                        log.date,
                        log.meal_type,
                        log.quantity_grams,
                        log.calories_consumed(),
                        log.carbs_consumed(),
                        log.protein_consumed(),
                        log.fat_consumed(),
                        getattr(log, "created_at", ""),
                    ]
                )

    def export_user_profiles(self, export_dir, user_profiles):
        file_path = os.path.join(export_dir, "user_profiles.csv")

        with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "profile_id",
                    "user_id",
                    "username",
                    "age",
                    "gender",
                    "height_cm",
                    "current_weight_kg",
                    "target_weight_kg",
                    "goal_type",
                    "activity_level",
                    "bmi",
                    "bmi_category",
                    "bmr",
                    "tdee",
                    "target_calories",
                    "target_carbs",
                    "target_protein",
                    "target_fat",
                    "created_at",
                ]
            )

            for profile in user_profiles:
                writer.writerow(
                    [
                        profile.id,
                        profile.user.id,
                        profile.user.username,
                        profile.age,
                        profile.gender,
                        profile.height_cm,
                        profile.current_weight_kg,
                        profile.target_weight_kg,
                        profile.goal_type,
                        profile.activity_level,
                        profile.bmi(),
                        profile.bmi_category(),
                        profile.bmr(),
                        profile.tdee(),
                        profile.target_calories(),
                        profile.target_carbs(),
                        profile.target_protein(),
                        profile.target_fat(),
                        getattr(profile, "created_at", ""),
                    ]
                )

    def export_weight_logs(self, export_dir, weight_logs):
        file_path = os.path.join(export_dir, "weight_logs.csv")

        with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "weight_log_id",
                    "user_id",
                    "username",
                    "weight_kg",
                    "date",
                    "created_at",
                ]
            )

            for log in weight_logs:
                writer.writerow(
                    [
                        log.id,
                        log.user.id,
                        log.user.username,
                        log.weight_kg,
                        log.date,
                        getattr(log, "created_at", ""),
                    ]
                )

    def export_daily_nutrition_summary(self, export_dir, consumption_logs):
        file_path = os.path.join(export_dir, "daily_nutrition_summary.csv")

        summary = defaultdict(
            lambda: {
                "total_quantity_grams": 0,
                "total_calories": 0,
                "total_carbs": 0,
                "total_protein": 0,
                "total_fat": 0,
                "breakfast_calories": 0,
                "lunch_calories": 0,
                "dinner_calories": 0,
                "snack_calories": 0,
                "log_count": 0,
            }
        )

        for log in consumption_logs:
            key = (log.user.id, log.user.username, log.date)

            calories = log.calories_consumed()
            carbs = log.carbs_consumed()
            protein = log.protein_consumed()
            fat = log.fat_consumed()

            summary[key]["total_quantity_grams"] += log.quantity_grams
            summary[key]["total_calories"] += calories
            summary[key]["total_carbs"] += carbs
            summary[key]["total_protein"] += protein
            summary[key]["total_fat"] += fat
            summary[key]["log_count"] += 1

            if log.meal_type == "breakfast":
                summary[key]["breakfast_calories"] += calories
            elif log.meal_type == "lunch":
                summary[key]["lunch_calories"] += calories
            elif log.meal_type == "dinner":
                summary[key]["dinner_calories"] += calories
            else:
                summary[key]["snack_calories"] += calories

        with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "user_id",
                    "username",
                    "date",
                    "total_quantity_grams",
                    "total_calories",
                    "total_carbs",
                    "total_protein",
                    "total_fat",
                    "breakfast_calories",
                    "lunch_calories",
                    "dinner_calories",
                    "snack_calories",
                    "log_count",
                ]
            )

            for (user_id, username, date), data in summary.items():
                writer.writerow(
                    [
                        user_id,
                        username,
                        date,
                        round(data["total_quantity_grams"], 2),
                        round(data["total_calories"], 2),
                        round(data["total_carbs"], 2),
                        round(data["total_protein"], 2),
                        round(data["total_fat"], 2),
                        round(data["breakfast_calories"], 2),
                        round(data["lunch_calories"], 2),
                        round(data["dinner_calories"], 2),
                        round(data["snack_calories"], 2),
                        data["log_count"],
                    ]
                )