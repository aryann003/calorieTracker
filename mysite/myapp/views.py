from urllib import request
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from .models import Consume, Food
from django.contrib.auth.decorators import login_required
from .forms import FoodForm


@login_required 
def index(request):
    foods = Food.objects.filter(user=request.user) | Food.objects.filter(user__isnull=True)

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
    CARBS_GOAL = 300
    PROTEIN_GOAL = 150
    FAT_GOAL = 70   

    calPercent =0
    if totals['total_calories']:
        calPercent = (totals['total_calories'] / CALORIE_GOAL) * 100
    
    carbPercent =0
    if totals['total_carbs']:
        carbPercent = (totals['total_carbs'] / CARBS_GOAL) * 100
    
    proteinPercent =0
    if totals['total_protein']:
        proteinPercent = (totals['total_protein'] / PROTEIN_GOAL) * 100

    fatPercent =0
    if totals['total_fat']: 
        fatPercent = (totals['total_fat'] / FAT_GOAL) * 100

    context = {
        'foods': foods,
        'consumed_food': consumed_food,
        'total_calories': totals['total_calories'] or 0,
        'total_carbs': totals['total_carbs'] or 0,
        'total_protein': totals['total_protein'] or 0,
        'total_fat': totals['total_fat'] or 0,
        'calPercent': round(calPercent,2),
        'carbPercent': round(carbPercent,2),
        'proteinPercent': round(proteinPercent,2),
        'fatPercent': round(fatPercent,2),
        'CALORIE_GOAL': CALORIE_GOAL,
        'CARBS_GOAL': CARBS_GOAL,
        'PROTEIN_GOAL': PROTEIN_GOAL,
        'FAT_GOAL': FAT_GOAL,
    }

    return render(request, 'myapp/index.html', context)

@login_required
def delete_consume(request, consume_id):
    consume = get_object_or_404(Consume, id=consume_id, user=request.user)
    consume.delete()
    return redirect('index')


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