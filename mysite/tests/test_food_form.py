import pytest

from myapp.forms import FoodForm
from myapp.models import Food

VALID = {"name": "Dal", "category": "other", "calories": 116, "carbs": 20, "protein": 9, "fat": 0.4}


@pytest.mark.django_db
class TestFoodForm:
    def test_valid_food(self):
        assert FoodForm(VALID).is_valid()

    @pytest.mark.parametrize("field,value", [("calories", -1), ("calories", 901), ("carbs", -0.1), ("protein", 101), ("fat", 150), ("name", "   ")])
    def test_rejects_impossible_values(self, field, value):
        assert not FoodForm({**VALID, field: value}).is_valid()

    def test_macros_cannot_exceed_100g_per_100g(self):
        form = FoodForm({**VALID, "carbs": 60, "protein": 30, "fat": 20})
        assert not form.is_valid() and "cannot exceed 100" in str(form.errors)

    def test_adding_a_food_assigns_it_to_the_user(self, client, user):
        resp = client.post("/add-food/", VALID)
        assert resp.status_code == 302 and Food.objects.get(name="Dal").user == user

    def test_invalid_food_is_not_saved(self, client):
        assert client.post("/add-food/", {**VALID, "calories": -50}).status_code == 200
        assert Food.objects.count() == 0
