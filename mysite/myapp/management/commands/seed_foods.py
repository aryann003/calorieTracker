"""Create the shared food catalogue (foods with no owner, visible to every user).

Idempotent: foods that already exist (by name) are left untouched, so an admin's
edits are never overwritten. Values are approximate, per 100 g, taken from common
nutrition tables (USDA FoodData Central and Indian food composition tables).
"""
from django.core.management.base import BaseCommand

from myapp.models import Food

# (name, category, calories, carbs, protein, fat) per 100 g
FOODS = [
    # grains and staples
    ("White rice, cooked", "grains", 130, 28.2, 2.7, 0.3),
    ("Brown rice, cooked", "grains", 112, 23.5, 2.3, 0.8),
    ("Chapati / roti (wheat)", "grains", 297, 46.0, 9.0, 7.5),
    ("Whole wheat bread", "grains", 247, 41.3, 13.0, 3.4),
    ("White bread", "grains", 265, 49.0, 9.0, 3.2),
    ("Oats, dry", "grains", 389, 66.3, 16.9, 6.9),
    ("Pasta, cooked", "grains", 158, 30.9, 5.8, 0.9),
    # legumes
    ("Dal (lentils), cooked", "other", 116, 20.1, 9.0, 0.4),
    ("Chickpeas, cooked", "other", 164, 27.4, 8.9, 2.6),
    ("Rajma (kidney beans), cooked", "other", 127, 22.8, 8.7, 0.5),
    # dairy
    ("Milk, whole", "dairy", 61, 4.8, 3.2, 3.3),
    ("Curd / plain yogurt", "dairy", 61, 4.7, 3.5, 3.3),
    ("Paneer", "dairy", 265, 1.2, 18.3, 20.8),
    ("Cheddar cheese", "dairy", 403, 1.3, 24.9, 33.1),
    ("Butter", "dairy", 717, 0.1, 0.9, 81.1),
    ("Ghee", "dairy", 876, 0.0, 0.3, 99.5),
    # fruits
    ("Banana", "fruits", 89, 22.8, 1.1, 0.3),
    ("Apple", "fruits", 52, 13.8, 0.3, 0.2),
    ("Orange", "fruits", 47, 11.8, 0.9, 0.1),
    ("Mango", "fruits", 60, 15.0, 0.8, 0.4),
    ("Grapes", "fruits", 69, 18.1, 0.7, 0.2),
    ("Papaya", "fruits", 43, 10.8, 0.5, 0.3),
    # vegetables
    ("Potato, boiled", "vegetables", 87, 20.1, 1.9, 0.1),
    ("Tomato", "vegetables", 18, 3.9, 0.9, 0.2),
    ("Onion", "vegetables", 40, 9.3, 1.1, 0.1),
    ("Spinach", "vegetables", 23, 3.6, 2.9, 0.4),
    ("Carrot", "vegetables", 41, 9.6, 0.9, 0.2),
    ("Cauliflower", "vegetables", 25, 5.0, 1.9, 0.3),
    ("Broccoli", "vegetables", 34, 6.6, 2.8, 0.4),
    ("Cucumber", "vegetables", 15, 3.6, 0.7, 0.1),
    # non-vegetarian
    ("Chicken breast, cooked", "nonvegetarian", 165, 0.0, 31.0, 3.6),
    ("Egg, boiled", "nonvegetarian", 155, 1.1, 12.6, 10.6),
    ("Salmon, cooked", "nonvegetarian", 206, 0.0, 22.1, 12.4),
    ("Mutton / lamb, cooked", "nonvegetarian", 294, 0.0, 25.6, 20.9),
    # snacks
    ("Peanuts", "snacks", 567, 16.1, 25.8, 49.2),
    ("Almonds", "snacks", 579, 21.6, 21.2, 49.9),
    ("Potato chips", "snacks", 536, 52.9, 7.0, 34.6),
    ("Dark chocolate", "snacks", 598, 45.9, 7.8, 42.6),
    # fast food
    ("Cheese pizza", "fast_food", 266, 33.0, 11.4, 10.4),
    ("French fries", "fast_food", 312, 41.4, 3.4, 14.7),
    # beverages
    ("Coffee, black", "beverages", 1, 0.0, 0.1, 0.0),
    ("Orange juice", "beverages", 45, 10.4, 0.7, 0.2),
    ("Coconut water", "beverages", 19, 3.7, 0.7, 0.2),
    ("Cola", "beverages", 42, 10.6, 0.0, 0.0),
    # other
    ("Sugar", "other", 387, 99.8, 0.0, 0.0),
    ("Honey", "other", 304, 82.4, 0.3, 0.0),
    ("Vegetable oil", "other", 884, 0.0, 0.0, 100.0),
]


class Command(BaseCommand):
    help = "Create the shared food catalogue (idempotent; never overwrites existing foods)."

    def handle(self, *args, **options):
        created = 0
        for name, category, calories, carbs, protein, fat in FOODS:
            _, was_created = Food.objects.get_or_create(
                user=None, name=name,
                defaults={"category": category, "calories": calories,
                          "carbs": carbs, "protein": protein, "fat": fat},
            )
            created += was_created
        self.stdout.write(self.style.SUCCESS(
            f"Shared foods ready: {created} created, {len(FOODS) - created} already existed."))
