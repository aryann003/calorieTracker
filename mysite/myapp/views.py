from datetime import datetime

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now

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


@login_required
def logout_view(request):
    logout(request)
    return redirect('home')


def get_selected_date(request):
    date_str = request.GET.get('date')

    if not date_str:
        return now().date()

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return now().date()


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
    today = now().date()
    is_today = selected_date == today

    foods = (
        Food.objects.filter(user=request.user)
        | Food.objects.filter(user__isnull=True)
    ).order_by('name')

    profile = UserProfile.objects.filter(user=request.user).first()

    if request.method == 'POST' and request.POST.get('action') == 'add_food':
        if not is_today:
            messages.warning(request, "You can only add food for today.")
            return redirect(f"/dashboard/?date={selected_date}")

        food_id = request.POST.get('food_consumed')
        food = get_object_or_404(Food, id=food_id)

        quantity_str = request.POST.get('quantity_grams') or '100'
        meal_type = request.POST.get('meal_type') or 'breakfast'

        valid_meals = [choice[0] for choice in Consume.MEAL_CHOICES]

        if meal_type not in valid_meals:
            meal_type = 'breakfast'

        try:
            quantity_grams = float(quantity_str)
        except ValueError:
            quantity_grams = 100

        if quantity_grams <= 0:
            messages.error(request, "Quantity must be greater than 0 grams.")
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

    consumed_food = Consume.objects.filter(
        user=request.user,
        date=selected_date
    ).order_by('meal_type', 'created_at')

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


@login_required
def delete_consume(request, consume_id):
    consume = get_object_or_404(
        Consume,
        id=consume_id,
        user=request.user
    )

    entry_date = consume.date

    if entry_date < now().date():
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

            profile, created = UserProfile.objects.get_or_create(
                user=request.user
            )
            profile.current_weight_kg = weight_log.weight_kg
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