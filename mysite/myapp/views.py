from multiprocessing import context
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from datetime import datetime
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .models import Consume, Food
from .forms import FoodForm



@login_required
def index(request):
    foods = Food.objects.filter(user=request.user) | Food.objects.filter(user__isnull=True)

    # DATE HANDLING
    date_str = request.GET.get('date')
    if date_str:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        selected_date = now().date()

    # ✅ ADD FOOD (POST)
    today = now().date()
    is_today = selected_date == today
    if request.method == 'POST' and request.POST.get('action') == 'add_food':
        food_id = request.POST.get('food_consumed')
        food = get_object_or_404(Food, id=food_id)
        meal = request.POST.get('meal')

        Consume.objects.create(
            user=request.user,
            food_consumed=food,
            date=selected_date,
            meal=meal
        )

        return redirect(f"/?date={selected_date}")

    # HANDLE GOAL UPDATE FORM (weight + journey)
    goal_weight = request.session.get('goal_weight')
    goal_height = request.session.get('goal_height')
    goal_type = request.session.get('goal_type', 'maintain')  # maintain | loss | gain
    if request.method == 'POST' and request.POST.get('action') == 'set_goals':
        weight_str = request.POST.get('goal_weight')
        height_str = request.POST.get('goal_height')
        goal_type = request.POST.get('goal_type') or 'maintain'
        try:
            goal_weight = float(weight_str) if weight_str else None
        except ValueError:
            goal_weight = None
        try:
            goal_height = float(height_str) if height_str else None
        except ValueError:
            goal_height = None
        if not goal_weight or not goal_height:
            messages.error(request, "Please enter a valid weight and height to update goals.")
            return redirect('index')
        request.session['goal_weight'] = goal_weight
        request.session['goal_height'] = goal_height
        request.session['goal_type'] = goal_type
        return redirect('index')

    # FETCH CONSUMED FOOD
    consumed_food = Consume.objects.filter(
        user=request.user,
        date=selected_date
    ).order_by('meal')

    totals = consumed_food.aggregate(
        total_calories=Sum('food_consumed__calories'),
        total_carbs=Sum('food_consumed__carbs'),
        total_protein=Sum('food_consumed__protein'),
        total_fat=Sum('food_consumed__fat'),
    )

   
    # GOALS (derived from weight + journey; fallback defaults)
    def compute_goals(weight, height_cm, journey):
        """
        Estimate TDEE using a simplified Mifflin-St Jeor (assumes age 30, light activity 1.4).
        Then adjust +-400 kcal for loss/gain.
        """
        if weight and height_cm:
            age = 30  # fallback assumption
            bmr = 10 * weight + 6.25 * height_cm - 5 * age + 5  # male default
            tdee = bmr * 1.4  # light activity multiplier
            if journey == 'loss':
                calorie_goal = tdee - 400
            elif journey == 'gain':
                calorie_goal = tdee + 400
            else:
                calorie_goal = tdee
            # macros: 30% protein, 30% fat, 40% carbs (by kcal)
            protein_goal = round((calorie_goal * 0.30) / 4, 1)
            fat_goal = round((calorie_goal * 0.30) / 9, 1)
            carb_goal = round((calorie_goal * 0.40) / 4, 1)
        elif weight:
            # fallback to weight-only heuristic
            if journey == 'loss':
                calorie_goal = weight * 25
            elif journey == 'gain':
                calorie_goal = weight * 35
            else:
                calorie_goal = weight * 30
            protein_goal = round(weight * 1.8, 1)
            fat_goal = round(calorie_goal * 0.25 / 9, 1)
            carb_goal = round((calorie_goal - (protein_goal * 4) - (fat_goal * 9)) / 4, 1)
        else:
            calorie_goal = 2600
            carb_goal = 300
            protein_goal = 150
            fat_goal = 70
        return round(calorie_goal), round(carb_goal), round(protein_goal), round(fat_goal)

    CALORIE_GOAL, CARBS_GOAL, PROTEIN_GOAL, FAT_GOAL = compute_goals(goal_weight, goal_height, goal_type)

    bmi_value = None
    if goal_weight and goal_height and goal_height > 0:
        bmi_value = round(goal_weight / ((goal_height / 100) ** 2), 1)

    remaining_calories = CALORIE_GOAL - (totals['total_calories'] or 0)
    status = "under" if remaining_calories >= 0 else "over"

    # PERCENTAGES
    calPercent = (totals['total_calories'] or 0) / CALORIE_GOAL * 100
    carbPercent = (totals['total_carbs'] or 0) / CARBS_GOAL * 100
    proteinPercent = (totals['total_protein'] or 0) / PROTEIN_GOAL * 100
    fatPercent = (totals['total_fat'] or 0) / FAT_GOAL * 100

    context = {
        'foods': foods,
        'consumed_food': consumed_food,
        'selected_date': selected_date,
        'goal_weight': goal_weight or '',
        'goal_height': goal_height or '',
        'goal_type': goal_type,
        'bmi_value': bmi_value,

        'total_calories': totals['total_calories'] or 0,
        'total_carbs': totals['total_carbs'] or 0,
        'total_protein': totals['total_protein'] or 0,
        'total_fat': totals['total_fat'] or 0,

        'calPercent': round(calPercent, 1),
        'carbPercent': round(carbPercent, 1),
        'proteinPercent': round(proteinPercent, 1),
        'fatPercent': round(fatPercent, 1),
        'remaining_calories': remaining_calories,
        'status': status,
    
        'CALORIE_GOAL': CALORIE_GOAL,
        'CARBS_GOAL': CARBS_GOAL,
        'PROTEIN_GOAL': PROTEIN_GOAL,
        'FAT_GOAL': FAT_GOAL,
        'is_today': is_today,
    }

    return render(request, 'myapp/index.html', context)


def home(request):
    if request.user.is_authenticated:
        return redirect('index')
    return render(request, 'myapp/home.html')


@login_required
def delete_consume(request, consume_id):
    consume = get_object_or_404(Consume, id=consume_id, user=request.user)
    if(consume.date < now().date()):
        messages.warning(request, "You cannot delete entries from previous dates.")
        return redirect(f"/?date={consume.date}")

    date = consume.date
    consume.delete()
    return redirect(f"/?date={date}")


@login_required
def add_food(request):
    if request.method == 'POST':
        form = FoodForm(request.POST)
        if form.is_valid():
            food = form.save(commit=False)
            food.user = request.user
            food.save()
            return redirect('index')
    else:
        form = FoodForm()

    return render(request, 'myapp/add_food.html', {'form': form})


@login_required
def logout_view(request):
    """Log out the current user and send them to the homepage."""
    logout(request)
    return redirect('home')


def register(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
