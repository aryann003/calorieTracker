"""Nutrition formulas, checked against hand-calculated values (Mifflin-St Jeor)."""
import pytest
from django.contrib.auth.models import User

from myapp.models import Consume, Food, UserProfile


def make(db_user, **kw):
    defaults = dict(age=30, gender="male", height_cm=180, current_weight_kg=80, activity_level="moderate", goal_type="maintain")
    defaults.update(kw)
    return UserProfile(user=db_user, **defaults)


@pytest.mark.django_db
class TestProfileMath:
    def test_bmi(self, user):
        assert make(user, height_cm=175, current_weight_kg=70).bmi() == 22.86

    @pytest.mark.parametrize("weight,category", [(50, "UnderWeight"), (70, "Healthy Weight"), (85, "OverWeight"), (110, "Obesity")])
    def test_bmi_categories(self, user, weight, category):
        assert make(user, height_cm=175, current_weight_kg=weight).bmi_category() == category

    def test_bmr_male(self, user):
        assert make(user).bmr() == 1780.0  # 800 + 1125 - 150 + 5

    def test_bmr_female(self, user):
        assert make(user, gender="female").bmr() == 1614.0  # 800 + 1125 - 150 - 161

    def test_other_gender_uses_the_male_formula(self, user):
        assert make(user, gender="other").bmr() == 1780.0

    @pytest.mark.parametrize("level,expected", [("low", 2136.0), ("moderate", 2759.0), ("high", 3070.5)])
    def test_tdee_by_activity(self, user, level, expected):
        assert make(user, activity_level=level).tdee() == expected

    @pytest.mark.parametrize("goal,expected", [("maintain", 2759.0), ("lose", 2259.0), ("gain", 3259.0)])
    def test_target_calories_by_goal(self, user, goal, expected):
        assert make(user, goal_type=goal).target_calories() == expected

    def test_target_never_drops_below_1200(self, user):
        small = make(user, age=60, gender="female", height_cm=150, current_weight_kg=45, activity_level="low", goal_type="lose")
        assert small.tdee() == 1111.8 and small.target_calories() == 1200.0

    def test_macro_targets_split_25_50_25(self, user):
        p = make(user)
        assert p.target_protein() == 172.44   # 25% of 2759 / 4
        assert p.target_carbs() == 344.88     # 50% / 4
        assert p.target_fat() == 76.64        # 25% / 9

    @pytest.mark.parametrize("missing", ["age", "height_cm", "current_weight_kg"])
    def test_missing_data_gives_none_not_a_crash(self, user, missing):
        p = make(user, **{missing: None})
        assert p.bmr() is None and p.tdee() is None and p.target_calories() is None and p.target_protein() is None

    def test_zero_height_does_not_divide_by_zero(self, user):
        assert make(user, height_cm=0).bmi() is None


@pytest.mark.django_db
class TestConsumeMath:
    def test_quantity_scales_nutrients_from_per_100g(self, user):
        food = Food.objects.create(name="X", calories=200, carbs=40, protein=10, fat=4)
        c = Consume.objects.create(user=user, food_consumed=food, quantity_grams=150)
        assert (c.calories_consumed(), c.carbs_consumed(), c.protein_consumed(), c.fat_consumed()) == (300.0, 60.0, 15.0, 6.0)

    def test_small_quantities_are_rounded_to_two_places(self, user):
        food = Food.objects.create(name="Y", calories=33, carbs=1, protein=1, fat=1)
        assert Consume.objects.create(user=user, food_consumed=food, quantity_grams=7).calories_consumed() == 2.31
