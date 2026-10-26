import pytest
from django.contrib.auth.models import User
from django.test import Client

from myapp.models import Consume, Food, UserProfile


@pytest.fixture
def user(db):
    return User.objects.create_user("alice", password="StrongPass123!")


@pytest.fixture
def other_user(db):
    return User.objects.create_user("bob", password="StrongPass123!")


@pytest.fixture
def client(user):
    c = Client()
    c.force_login(user)
    return c


@pytest.fixture
def anon():
    return Client()


@pytest.fixture
def rice(db):
    """A shared (ownerless) food: 130 kcal, 28 g carbs, 2.7 g protein, 0.3 g fat per 100 g."""
    return Food.objects.create(user=None, name="Rice", category="grains", calories=130, carbs=28, protein=2.7, fat=0.3)


@pytest.fixture
def private_food(other_user):
    return Food.objects.create(user=other_user, name="Bob's secret shake", category="beverages",
                               calories=200, carbs=20, protein=20, fat=5)


@pytest.fixture
def profile(user):
    return UserProfile.objects.create(user=user, age=30, gender="male", height_cm=180, current_weight_kg=80,
                                      target_weight_kg=75, goal_type="maintain", activity_level="moderate")
