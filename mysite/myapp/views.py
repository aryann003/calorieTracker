from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from datetime import datetime

from .models import Consume, Food
from .forms import FoodForm


@login_required
def index(request):
    foods = Food.objects.filter(user=request.user) | Food.objects.filter(user__isnull=True)

    # ✅ DATE HANDLING
    date_str = request.GET.get('date')
    if date_str:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        selected_date = now().date()

    # ✅ ADD FOOD (POST)
    if request.method == 'POST':
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

    # ✅ FETCH CONSUMED FOOD
    consumed_food = Consume.objects.filter(
        user=request.user,
        date=selected_date
    )

    totals = consumed_food.aggregate(
        total_calories=Sum('food_consumed__calories'),
        total_carbs=Sum('food_consumed__carbs'),
        total_protein=Sum('food_consumed__protein'),
        total_fat=Sum('food_consumed__fat'),
    )

   

    # GOALS
    CALORIE_GOAL = 2600
    CARBS_GOAL = 300
    PROTEIN_GOAL = 150
    FAT_GOAL = 70

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
    }

    return render(request, 'myapp/index.html', context)


@login_required
def delete_consume(request, consume_id):
    consume = get_object_or_404(Consume, id=consume_id, user=request.user)
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
