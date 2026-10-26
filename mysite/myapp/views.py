import math
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import localdate
from django.views.decorators.http import require_POST

from .forms import FoodForm, UserProfileForm, WeightLogForm
from .models import Consume, Food, UserProfile, WeightLog


def home(request):
    if request.user.is_authenticated:
        return redirect('index')

    return render(request, 'myapp/home.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect('index')
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


@require_POST
@login_required
def logout_view(request):
    # POST only: a GET link could log users out from any other web page.
    logout(request)
    return redirect('home')


MAX_QUANTITY_GRAMS = 10000


def visible_foods(user):
    """Foods a user may log: their own plus the shared (user-less) catalogue."""
    return Food.objects.filter(Q(user=user) | Q(user__isnull=True)).order_by('name')


def parse_quantity(raw):
    """Return a valid grams value, or None. Rejects nan, inf, zero and absurd amounts."""
    try:
        value = float(raw or 100)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value) or value <= 0 or value > MAX_QUANTITY_GRAMS:
        return None
    return value


def get_selected_date(request):
    # localdate() is the user's calendar day (settings.TIME_ZONE), not UTC's.
    date_str = request.GET.get('date')

    if not date_str:
        return localdate()

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return localdate()


def get_user_goals(profile):
    default_goals = {
        'calories': 2600,
        'carbs': 300,
        'protein': 150,
        'fat': 70,
    }

    if not profile:
        return default_goals

    calories = profile.target_calories()
    carbs = profile.target_carbs()
    protein = profile.target_protein()
    fat = profile.target_fat()

    if not calories or not carbs or not protein or not fat:
        return default_goals

    return {
        'calories': calories,
        'carbs': carbs,
        'protein': protein,
        'fat': fat,
    }


@login_required
def index(request):
    selected_date = get_selected_date(request)
    today = localdate()
    is_today = selected_date == today

    foods = visible_foods(request.user)

    profile = UserProfile.objects.filter(user=request.user).first()

    if request.method == 'POST' and request.POST.get('action') == 'add_food':
        if not is_today:
            messages.warning(request, "You can only add food for today.")
            return redirect(f"/dashboard/?date={selected_date}")

        # Only foods this user can see: someone else's private food is a 404.
        try:
            food_id = int(request.POST.get('food_consumed'))
        except (TypeError, ValueError):
            food_id = None
        food = get_object_or_404(foods, id=food_id)

        meal_type = request.POST.get('meal_type') or 'breakfast'

        valid_meals = [choice[0] for choice in Consume.MEAL_CHOICES]

        if meal_type not in valid_meals:
            meal_type = 'breakfast'

        quantity_grams = parse_quantity(request.POST.get('quantity_grams'))

        if quantity_grams is None:
            messages.error(
                request,
                f"Enter a quantity between 0 and {MAX_QUANTITY_GRAMS:,} grams.",
            )
            return redirect(f"/dashboard/?date={selected_date}")

        Consume.objects.create(
            user=request.user,
            food_consumed=food,
            quantity_grams=quantity_grams,
            meal_type=meal_type,
            date=selected_date,
        )

        messages.success(request, "Food added successfully.")
        return redirect(f"/dashboard/?date={selected_date}")

    # select_related: one query for all rows instead of one extra per row.
    consumed_food = Consume.objects.filter(
        user=request.user,
        date=selected_date
    ).select_related('food_consumed').order_by('meal_type', 'created_at')

    total_calories = round(
        sum(item.calories_consumed() for item in consumed_food),
        2
    )
    total_carbs = round(
        sum(item.carbs_consumed() for item in consumed_food),
        2
    )
    total_protein = round(
        sum(item.protein_consumed() for item in consumed_food),
        2
    )
    total_fat = round(
        sum(item.fat_consumed() for item in consumed_food),
        2
    )

    goals = get_user_goals(profile)

    calorie_goal = goals['calories']
    carbs_goal = goals['carbs']
    protein_goal = goals['protein']
    fat_goal = goals['fat']

    remaining_calories = round(calorie_goal - total_calories, 2)
    status = "under" if remaining_calories >= 0 else "over"

    cal_percent = (total_calories / calorie_goal * 100) if calorie_goal else 0
    carb_percent = (total_carbs / carbs_goal * 100) if carbs_goal else 0
    protein_percent = (total_protein / protein_goal * 100) if protein_goal else 0
    fat_percent = (total_fat / fat_goal * 100) if fat_goal else 0

    context = {
        'foods': foods,
        'consumed_food': consumed_food,
        'selected_date': selected_date,
        'is_today': is_today,

        'profile': profile,
        'bmi_value': profile.bmi() if profile else None,
        'bmi_category': profile.bmi_category() if profile else None,
        'bmr_value': profile.bmr() if profile else None,
        'tdee_value': profile.tdee() if profile else None,

        'total_calories': total_calories,
        'total_carbs': total_carbs,
        'total_protein': total_protein,
        'total_fat': total_fat,

        'CALORIE_GOAL': calorie_goal,
        'CARBS_GOAL': carbs_goal,
        'PROTEIN_GOAL': protein_goal,
        'FAT_GOAL': fat_goal,

        'calPercent': round(cal_percent, 1),
        'carbPercent': round(carb_percent, 1),
        'proteinPercent': round(protein_percent, 1),
        'fatPercent': round(fat_percent, 1),

        'remaining_calories': remaining_calories,
        'status': status,
    }

    return render(request, 'myapp/index.html', context)


@login_required
def add_food(request):
    if request.method == 'POST':
        form = FoodForm(request.POST)

        if form.is_valid():
            food = form.save(commit=False)
            food.user = request.user
            food.save()

            messages.success(request, "Food created successfully.")
            return redirect('index')
    else:
        form = FoodForm()

    return render(request, 'myapp/add_food.html', {'form': form})


@require_POST
@login_required
def delete_consume(request, consume_id):
    # POST only: a GET link could be triggered from any other web page (CSRF).
    consume = get_object_or_404(
        Consume,
        id=consume_id,
        user=request.user
    )

    entry_date = consume.date

    if entry_date < localdate():
        messages.warning(
            request,
            "You cannot delete entries from previous dates."
        )
        return redirect(f"/dashboard/?date={entry_date}")

    consume.delete()
    messages.success(request, "Food log removed.")
    return redirect(f"/dashboard/?date={entry_date}")


@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)

        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)

    context = {
        'form': form,
        'profile': profile,

        'bmi_value': profile.bmi(),
        'bmi_category': profile.bmi_category(),
        'bmr_value': profile.bmr(),
        'tdee_value': profile.tdee(),

        'target_calories': profile.target_calories(),
        'target_protein': profile.target_protein(),
        'target_carbs': profile.target_carbs(),
        'target_fat': profile.target_fat(),
    }

    return render(request, 'myapp/profile.html', context)


@login_required
def weight_log_view(request):
    if request.method == 'POST':
        form = WeightLogForm(request.POST)

        if form.is_valid():
            weight_log = form.save(commit=False)
            weight_log.user = request.user
            weight_log.save()

            # Current weight is the most recent entry by DATE. Backfilling an
            # older measurement must not overwrite it.
            latest = (
                WeightLog.objects.filter(user=request.user)
                .order_by('-date', '-created_at')
                .first()
            )
            profile, created = UserProfile.objects.get_or_create(
                user=request.user
            )
            profile.current_weight_kg = latest.weight_kg
            profile.save()

            messages.success(request, "Weight log added successfully.")
            return redirect('weight_log')
    else:
        form = WeightLogForm()

    weight_logs = WeightLog.objects.filter(user=request.user)

    context = {
        'form': form,
        'weight_logs': weight_logs,
    }

    return render(request, 'myapp/weight_log.html', context)