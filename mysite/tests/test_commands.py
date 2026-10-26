import csv

import pytest
from django.contrib.auth.models import User
from django.core.management import CommandError, call_command

from myapp.models import Consume, Food, UserProfile, WeightLog


def rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


@pytest.mark.django_db
class TestSeedFoods:
    def test_creates_a_valid_shared_catalogue(self):
        call_command("seed_foods")
        foods = Food.objects.filter(user__isnull=True)
        assert foods.count() >= 40
        for f in foods:
            assert 0 <= f.calories <= 900 and f.carbs + f.protein + f.fat <= 100.5, f.name
            f.full_clean()

    def test_is_idempotent_and_never_overwrites_edits(self):
        call_command("seed_foods")
        Food.objects.filter(name="Banana").update(calories=1)
        call_command("seed_foods")
        assert Food.objects.filter(name="Banana").count() == 1
        assert Food.objects.get(name="Banana").calories == 1


@pytest.mark.django_db
class TestSeedDemo:
    def test_creates_a_working_demo_account(self, anon):
        call_command("seed_demo")
        user = User.objects.get(username="demo")
        assert anon.login(username="demo", password="DemoPass123!")
        assert Consume.objects.filter(user=user).count() > 50 and WeightLog.objects.filter(user=user).count() >= 5
        assert UserProfile.objects.get(user=user).target_calories() is not None

    def test_dashboard_has_data_for_the_demo_user(self, anon):
        call_command("seed_demo")
        anon.login(username="demo", password="DemoPass123!")
        assert anon.get("/dashboard/").status_code == 200

    def test_is_idempotent(self):
        call_command("seed_demo")
        n = Consume.objects.count()
        call_command("seed_demo")
        assert Consume.objects.count() == n

    def test_reset_only_touches_the_demo_user(self, other_user, rice):
        Consume.objects.create(user=other_user, food_consumed=rice, quantity_grams=100)
        call_command("seed_demo")
        call_command("seed_demo", "--reset")
        assert Consume.objects.filter(user=other_user).count() == 1 and User.objects.filter(username="bob").exists()


@pytest.mark.django_db
class TestPowerBiExport:
    @pytest.fixture
    def out(self, settings, tmp_path):
        settings.BASE_DIR = tmp_path
        return tmp_path / "powerbi_exports"

    def test_exports_every_file_with_expected_columns(self, out, user, rice, profile):
        Consume.objects.create(user=user, food_consumed=rice, quantity_grams=200, meal_type="lunch")
        WeightLog.objects.create(user=user, weight_kg=80, date="2026-06-01")
        call_command("export_powerbi_data")
        for name in ["foods", "consumption_logs", "user_profiles", "weight_logs", "daily_nutrition_summary"]:
            assert (out / f"{name}.csv").exists(), name
        summary = rows(out / "daily_nutrition_summary.csv")[0]
        assert float(summary["total_calories"]) == 260.0 and float(summary["lunch_calories"]) == 260.0

    def test_per_user_export_includes_the_shared_foods_that_user_ate(self, out, user, other_user, rice, private_food):
        """Regression: foods.csv omitted shared foods, orphaning consumption_logs.food_id in Power BI."""
        Consume.objects.create(user=user, food_consumed=rice, quantity_grams=100)
        call_command("export_powerbi_data", "--username", "alice")
        food_ids = {r["food_id"] for r in rows(out / "foods.csv")}
        logged_food_ids = {r["food_id"] for r in rows(out / "consumption_logs.csv")}
        assert logged_food_ids and logged_food_ids <= food_ids
        assert str(private_food.id) not in food_ids  # another user's private food stays out

    def test_per_user_export_excludes_other_users_logs(self, out, user, other_user, rice):
        Consume.objects.create(user=user, food_consumed=rice, quantity_grams=100)
        Consume.objects.create(user=other_user, food_consumed=rice, quantity_grams=100)
        call_command("export_powerbi_data", "--username", "alice")
        assert {r["username"] for r in rows(out / "consumption_logs.csv")} == {"alice"}

    def test_shared_foods_without_an_owner_export_without_crashing(self, out, rice):
        call_command("export_powerbi_data")
        row = next(r for r in rows(out / "foods.csv") if r["food_name"] == "Rice")
        assert row["user_id"] == "" and row["username"] == "shared"

    def test_unknown_user_is_a_clear_error(self, out):
        with pytest.raises(CommandError, match="does not exist"):
            call_command("export_powerbi_data", "--username", "nobody")
