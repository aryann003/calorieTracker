from django.contrib import admin
from .models import Food, Consume, UserProfile, WeightLog


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'calories', 'protein', 'carbs', 'fat', 'user')
    list_filter = ('category',)
    search_fields = ('name',)


@admin.register(Consume)
class ConsumeAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'food_consumed',
        'quantity_grams',
        'meal_type',
        'date',
        'calories_consumed',
        'protein_consumed',
    )
    list_filter = ('meal_type', 'date')
    search_fields = ('user__username', 'food_consumed__name')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'goal_type',
        'activity_level',
        'current_weight_kg',
        'target_weight_kg',
        'target_calories',
        'target_protein',
    )
    list_filter = ('goal_type', 'activity_level')
    search_fields = ('user__username',)


@admin.register(WeightLog)
class WeightLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'weight_kg', 'date')
    list_filter = ('date',)
    search_fields = ('user__username',)