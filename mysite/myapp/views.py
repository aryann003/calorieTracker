from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from .models import Consume, Food

def index(request):
    foods = Food.objects.all()

    if request.method == 'POST':
        food_id = request.POST.get('food_consumed')
        food = get_object_or_404(Food, id=food_id)

        Consume.objects.create(
            user=request.user,
            food_consumed=food
        )
        return redirect('index')

    consumed_food = Consume.objects.filter(user=request.user)

    totals = consumed_food.aggregate(
        total_calories=Sum('food_consumed__calories'),
        total_carbs=Sum('food_consumed__carbs'),
        total_protein=Sum('food_consumed__protein'),
        total_fat=Sum('food_consumed__fat'),
    )

    CALORIE_GOAL = 2600

    calPercent =0
    if totals['total_calories']:
        calPercent = (totals['total_calories'] / CALORIE_GOAL) * 100

    context = {
        'foods': foods,
        'consumed_food': consumed_food,
        'total_calories': totals['total_calories'] or 0,
        'total_carbs': totals['total_carbs'] or 0,
        'total_protein': totals['total_protein'] or 0,
        'total_fat': totals['total_fat'] or 0,
        'calPercent': round(calPercent,2),
        'CALORIE_GOAL': CALORIE_GOAL,
    }

    return render(request, 'myapp/index.html', context)
