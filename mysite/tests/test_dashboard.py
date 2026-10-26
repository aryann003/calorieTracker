import datetime as dt
from unittest import mock

import pytest
from django.contrib.messages import get_messages
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from myapp.models import Consume, Food, UserProfile, WeightLog


def messages_of(response):
    return [str(m) for m in get_messages(response.wsgi_request)]


@pytest.mark.django_db
class TestAccess:
    @pytest.mark.parametrize("url", ["/dashboard/", "/profile/", "/weight-log/", "/add-food/"])
    def test_pages_require_login(self, anon, url):
        resp = anon.get(url)
        assert resp.status_code == 302 and "/login/" in resp["Location"]

    @pytest.mark.parametrize("url", ["/dashboard/", "/profile/", "/weight-log/", "/add-food/", "/"])
    def test_pages_render_for_signed_in_users(self, client, url):
        assert client.get(url).status_code in (200, 302)

    def test_home_redirects_signed_in_users_to_the_dashboard(self, client):
        assert client.get("/")["Location"].endswith("/dashboard/")

    def test_register_creates_and_logs_in_the_user(self, anon):
        resp = anon.post("/register/", {"username": "newbie", "password1": "Zx9!qwerty42", "password2": "Zx9!qwerty42"})
        assert resp.status_code == 302 and resp["Location"].endswith("/dashboard/")
        assert anon.get("/dashboard/").status_code == 200

    def test_register_rejects_a_weak_password(self, anon):
        resp = anon.post("/register/", {"username": "weak", "password1": "123", "password2": "123"})
        assert resp.status_code == 200

    def test_logout_requires_post(self, client):
        assert client.get("/logout/").status_code == 405
        assert client.get("/dashboard/").status_code == 200  # still signed in
        assert client.post("/logout/").status_code == 302
        assert client.get("/dashboard/").status_code == 302


@pytest.mark.django_db
class TestLogging:
    def post_food(self, client, food, quantity="150", meal="lunch", date=None):
        url = "/dashboard/" + (f"?date={date}" if date else "")
        return client.post(url, {"action": "add_food", "food_consumed": food.id, "quantity_grams": quantity, "meal_type": meal})

    def test_logging_a_food_for_today(self, client, user, rice):
        resp = self.post_food(client, rice)
        assert resp.status_code == 302
        entry = Consume.objects.get()
        assert (entry.user, entry.quantity_grams, entry.meal_type, entry.date) == (user, 150, "lunch", timezone.localdate())

    def test_empty_quantity_defaults_to_100g(self, client, rice):
        self.post_food(client, rice, quantity="")
        assert Consume.objects.get().quantity_grams == 100

    @pytest.mark.parametrize("bad", ["nan", "inf", "-inf", "-5", "0", "abc", "10001", "1e999"])
    def test_invalid_quantities_are_rejected(self, client, rice, bad):
        """Regression: `nan` and `inf` used to pass the `<= 0` check and corrupt the day's totals."""
        resp = self.post_food(client, rice, quantity=bad)
        assert Consume.objects.count() == 0
        assert any("quantity" in m.lower() for m in messages_of(client.get("/dashboard/")))

    def test_invalid_meal_type_falls_back_to_breakfast(self, client, rice):
        self.post_food(client, rice, meal="midnight")
        assert Consume.objects.get().meal_type == "breakfast"

    def test_cannot_log_for_a_past_date(self, client, rice):
        yesterday = timezone.localdate() - dt.timedelta(days=1)
        self.post_food(client, rice, date=yesterday)
        assert Consume.objects.count() == 0

    def test_cannot_log_someone_elses_private_food(self, client, private_food):
        """Regression: any user could log another user's private food by guessing its id."""
        assert self.post_food(client, private_food).status_code == 404
        assert Consume.objects.count() == 0

    def test_non_numeric_food_id_is_a_404_not_a_crash(self, client):
        resp = client.post("/dashboard/", {"action": "add_food", "food_consumed": "abc", "quantity_grams": "100"})
        assert resp.status_code == 404

    def test_dashboard_only_lists_visible_foods(self, client, rice, private_food, user):
        mine = Food.objects.create(user=user, name="Mine", calories=1, carbs=0, protein=0, fat=0)
        names = {f.name for f in client.get("/dashboard/").context["foods"]}
        assert names == {"Rice", "Mine"}


@pytest.mark.django_db
class TestTotals:
    def test_totals_and_remaining_calories(self, client, user, rice, profile):
        Consume.objects.create(user=user, food_consumed=rice, quantity_grams=200)  # 260 kcal
        ctx = client.get("/dashboard/").context
        assert ctx["total_calories"] == 260.0 and ctx["CALORIE_GOAL"] == 2759.0
        assert ctx["remaining_calories"] == 2499.0 and ctx["status"] == "under"
        assert ctx["calPercent"] == 9.4

    def test_over_target_is_flagged(self, client, user, rice, profile):
        Consume.objects.create(user=user, food_consumed=rice, quantity_grams=3000)  # 3900 kcal
        assert client.get("/dashboard/").context["status"] == "over"

    def test_without_a_profile_default_goals_apply(self, client):
        assert client.get("/dashboard/").context["CALORIE_GOAL"] == 2600

    def test_only_the_selected_days_entries_count(self, client, user, rice):
        today = timezone.localdate()
        Consume.objects.create(user=user, food_consumed=rice, quantity_grams=100, date=today)
        Consume.objects.create(user=user, food_consumed=rice, quantity_grams=100, date=today - dt.timedelta(days=1))
        assert client.get("/dashboard/").context["total_calories"] == 130.0
        assert client.get(f"/dashboard/?date={today - dt.timedelta(days=1)}").context["total_calories"] == 130.0

    def test_other_users_entries_are_never_counted(self, client, other_user, rice):
        Consume.objects.create(user=other_user, food_consumed=rice, quantity_grams=500)
        assert client.get("/dashboard/").context["total_calories"] == 0

    @pytest.mark.parametrize("bad_date", ["garbage", "2026-13-45", "", "31/01/2026"])
    def test_bad_date_parameter_falls_back_to_today(self, client, bad_date):
        assert client.get(f"/dashboard/?date={bad_date}").context["selected_date"] == timezone.localdate()


@pytest.mark.django_db
class TestPerformance:
    def test_dashboard_query_count_does_not_grow_with_entries(self, client, user, rice):
        """Regression: every logged row used to trigger its own food lookup (N+1)."""
        for _ in range(30):
            Consume.objects.create(user=user, food_consumed=Food.objects.create(name="f", calories=1, carbs=1, protein=1, fat=1), quantity_grams=50)
        with CaptureQueriesContext(connection) as ctx:
            assert client.get("/dashboard/").status_code == 200
        assert len(ctx.captured_queries) <= 8, [q["sql"][:80] for q in ctx.captured_queries]


@pytest.mark.django_db
class TestDelete:
    def entry(self, user, rice, day=None):
        return Consume.objects.create(user=user, food_consumed=rice, quantity_grams=100, date=day or timezone.localdate())

    def test_get_cannot_delete(self, client, user, rice):
        """Regression: deleting was a GET link, so any web page could delete entries (CSRF)."""
        e = self.entry(user, rice)
        assert client.get(f"/delete/{e.id}/").status_code == 405
        assert Consume.objects.filter(id=e.id).exists()

    def test_post_deletes_todays_entry(self, client, user, rice):
        e = self.entry(user, rice)
        assert client.post(f"/delete/{e.id}/").status_code == 302
        assert not Consume.objects.filter(id=e.id).exists()

    def test_cannot_delete_another_users_entry(self, client, other_user, rice):
        e = self.entry(other_user, rice)
        assert client.post(f"/delete/{e.id}/").status_code == 404
        assert Consume.objects.filter(id=e.id).exists()

    def test_past_entries_are_locked(self, client, user, rice):
        e = self.entry(user, rice, timezone.localdate() - dt.timedelta(days=1))
        client.post(f"/delete/{e.id}/")
        assert Consume.objects.filter(id=e.id).exists()

    def test_csrf_is_enforced_on_delete(self, user, rice):
        from django.test import Client
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(user)
        e = self.entry(user, rice)
        assert strict.post(f"/delete/{e.id}/").status_code == 403
        assert Consume.objects.filter(id=e.id).exists()

    def test_dashboard_renders_remove_as_a_post_form(self, client, user, rice):
        e = self.entry(user, rice)
        html = client.get("/dashboard/").content.decode()
        assert f'action="/delete/{e.id}/"' in html and 'method="post"' in html.split(f'action="/delete/{e.id}/"')[0][-80:].lower()


@pytest.mark.django_db
class TestTimeZone:
    def test_today_is_the_users_calendar_day_not_utc(self, client):
        """20:00 UTC on 1 June is already 01:30 on 2 June in India."""
        fake_now = dt.datetime(2026, 6, 1, 20, 0, tzinfo=dt.timezone.utc)
        with mock.patch("django.utils.timezone.now", return_value=fake_now):
            assert client.get("/dashboard/").context["selected_date"] == dt.date(2026, 6, 2)


@pytest.mark.django_db
class TestProfileAndWeight:
    def test_profile_update(self, client, user):
        resp = client.post("/profile/", {"age": 28, "gender": "female", "height_cm": 165, "current_weight_kg": 60,
                                         "target_weight_kg": 55, "goal_type": "lose", "activity_level": "low"})
        assert resp.status_code == 302
        p = UserProfile.objects.get(user=user)
        assert (p.age, p.gender, p.goal_type) == (28, "female", "lose")

    @pytest.mark.parametrize("field,value", [("age", 0), ("age", 200), ("height_cm", 10), ("current_weight_kg", -5), ("target_weight_kg", 900)])
    def test_profile_rejects_impossible_values(self, client, user, field, value):
        data = {"age": 28, "gender": "male", "height_cm": 170, "current_weight_kg": 70, "target_weight_kg": 65,
                "goal_type": "lose", "activity_level": "low", field: value}
        assert client.post("/profile/", data).status_code == 200
        assert not UserProfile.objects.filter(user=user, **{field: value}).exists()

    def test_weight_log_updates_current_weight(self, client, user):
        client.post("/weight-log/", {"weight_kg": 79, "date": "2026-06-10"})
        assert UserProfile.objects.get(user=user).current_weight_kg == 79

    def test_backfilling_an_older_weight_does_not_overwrite_the_current_one(self, client, user):
        """Regression: the last ENTERED weight, not the most recent by DATE, became 'current'."""
        client.post("/weight-log/", {"weight_kg": 78, "date": "2026-06-10"})
        client.post("/weight-log/", {"weight_kg": 85, "date": "2026-01-05"})  # older measurement
        assert UserProfile.objects.get(user=user).current_weight_kg == 78
        assert WeightLog.objects.filter(user=user).count() == 2

    @pytest.mark.parametrize("weight", ["5", "-70", "1000", "abc"])
    def test_weight_log_rejects_impossible_weights(self, client, user, weight):
        assert client.post("/weight-log/", {"weight_kg": weight, "date": "2026-06-10"}).status_code == 200
        assert WeightLog.objects.count() == 0

    def test_weight_log_page_only_shows_own_entries(self, client, user, other_user):
        WeightLog.objects.create(user=other_user, weight_kg=99, date="2026-06-01")
        WeightLog.objects.create(user=user, weight_kg=70, date="2026-06-01")
        assert [w.weight_kg for w in client.get("/weight-log/").context["weight_logs"]] == [70]
