import csv
import os
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.conf import settings

from myapp.models import Food, Consume, UserProfile, WeightLog


class Command(BaseCommand):
    help = "Export CalorieTracker data into CSV files for Power BI."

    def handle(self, *args, **options):
        export_dir = os.path.join(settings.BASE_DIR, "powerbi_exports")
        os.makedirs(export_dir, exist_ok=True)

        foods_file_path = os.path.join(export_dir, "foods.csv")

        with open(foods_file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            writer.writerow([
                "food_id",
                "user_id",
                "food_name",
                "category",
                "calories_per_100g",
                "carbs_per_100g",
                "protein_per_100g",
                "fat_per_100g",
                "created_at",
            ])

            foods = Food.objects.all().order_by("id")

            for food in foods:
                writer.writerow([
                    food.id,
                    food.user.id if food.user else "",
                    food.name,
                    food.category,
                    food.calories,
                    food.carbs,
                    food.protein,
                    food.fat,
                    food.created_at,
                ])

        self.stdout.write(
            self.style.SUCCESS(f"Exported foods.csv to {foods_file_path}")
        )

        consumption_file_path = os.path.join(export_dir, "consumption_logs.csv")

        with open(consumption_file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            writer.writerow([
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
            ])

            consumed_items = Consume.objects.select_related(
                "user",
                "food_consumed"
            ).all().order_by("date", "id")

            for item in consumed_items:
                writer.writerow([
                    item.id,
                    item.user.id,
                    item.user.username,
                    item.food_consumed.id,
                    item.food_consumed.name,
                    item.food_consumed.category,
                    item.date,
                    item.meal_type,
                    item.quantity_grams,
                    item.calories_consumed(),
                    item.carbs_consumed(),
                    item.protein_consumed(),
                    item.fat_consumed(),
                    item.created_at,
                ])

        self.stdout.write(
            self.style.SUCCESS(f"Exported consumption_logs.csv to {consumption_file_path}")
        )


        profiles_file_path = os.path.join(export_dir, "user_profiles.csv")

        with open(profiles_file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            writer.writerow([
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
            ])

            profiles = UserProfile.objects.select_related("user").all().order_by("id")

            for profile in profiles:
                writer.writerow([
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
                    profile.created_at,
                ])

        self.stdout.write(
            self.style.SUCCESS(f"Exported user_profiles.csv to {profiles_file_path}")
        )

        weight_logs_file_path = os.path.join(export_dir, "weight_logs.csv")

        with open(weight_logs_file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            writer.writerow([
                "weight_log_id",
                "user_id",
                "username",
                "weight_kg",
                "date",
                "created_at",
            ])

            weight_logs = WeightLog.objects.select_related("user").all().order_by("date", "id")

            for log in weight_logs:
                writer.writerow([
                    log.id,
                    log.user.id,
                    log.user.username,
                    log.weight_kg,
                    log.date,
                    log.created_at,
                ])

        self.stdout.write(
            self.style.SUCCESS(f"Exported weight_logs.csv to {weight_logs_file_path}")
        )

        daily_summary_file_path = os.path.join(
            export_dir,
            "daily_nutrition_summary.csv"
        )

        daily_data = defaultdict(lambda: {
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
        })

        consumed_items = Consume.objects.select_related(
            "user",
            "food_consumed"
        ).all().order_by("date", "id")

        for item in consumed_items:
            key = (item.user.id, item.date)

            daily_data[key]["username"] = item.user.username
            daily_data[key]["date"] = item.date
            daily_data[key]["total_quantity_grams"] += item.quantity_grams
            daily_data[key]["total_calories"] += item.calories_consumed()
            daily_data[key]["total_carbs"] += item.carbs_consumed()
            daily_data[key]["total_protein"] += item.protein_consumed()
            daily_data[key]["total_fat"] += item.fat_consumed()
            daily_data[key]["log_count"] += 1

            if item.meal_type == "breakfast":
                daily_data[key]["breakfast_calories"] += item.calories_consumed()
            elif item.meal_type == "lunch":
                daily_data[key]["lunch_calories"] += item.calories_consumed()
            elif item.meal_type == "dinner":
                daily_data[key]["dinner_calories"] += item.calories_consumed()
            elif item.meal_type == "snack":
                daily_data[key]["snack_calories"] += item.calories_consumed()

        with open(daily_summary_file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            writer.writerow([
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
            ])

            for key, data in daily_data.items():
                user_id, date = key

                writer.writerow([
                    user_id,
                    data["username"],
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
                ])

        self.stdout.write(
            self.style.SUCCESS(
                f"Exported daily_nutrition_summary.csv to {daily_summary_file_path}"
            )
        )