from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

class Food(models.Model):
    CATEGORY_CHOICES = [
        ('grains', 'Grains'),
        ('dairy', 'Dairy'),
        ('fruits', 'Fruits'),
        ('vegetables', 'Vegetables'),
        ('snacks', 'Snacks'),
        ('fast_food', 'Fast Food'),
        ('beverages', 'Beverages'),
        ('nonvegetarian', 'Non-Vegetarian'),
        ('other','Other'),
    ]

    user = models.ForeignKey(
        User,
        on_delete = models.CASCADE,
        db_constraint = False,
        null = True,
        blank = True
    )

    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default = 'other'
    )

    calories = models.FloatField(help_text="Calories per 100 grams")
    carbs = models.FloatField(help_text="Carbs per 100 grams")
    protein = models.FloatField(help_text="Protein per 100 grams")
    fat = models.FloatField(help_text="Fat per 100 grams")
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return self.name
    

class Consume(models.Model):
    MEAL_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ] 

    user = models.ForeignKey(
        User,
        on_delete = models.CASCADE
    )
    food_consumed = models.ForeignKey(Food, on_delete=models.CASCADE)
    meal_type = models.CharField(
        max_length=50,
        choices=MEAL_CHOICES,
        default='breakfast'
    )
    quantity_grams =  models.FloatField(help_text="Quantity consumed in grams",default=100)
    date = models.DateField(default=now)
    created_at = models.DateTimeField(default=now)

    def calories_consumed(self):
        return round((self.quantity_grams * self.food_consumed.calories)/ 100, 2)
    
    def protein_consumed(self):
        return round((self.quantity_grams * self.food_consumed.protein)/ 100,2)
    
    def carbs_consumed(self):
        return round((self.quantity_grams * self.food_consumed.carbs)/ 100,2)
    
    def fat_consumed(self):
        return round((self.quantity_grams * self.food_consumed.fat)/ 100,2)


    def __str__(self):
        return f"{self.user.username} ate {self.quantity_grams} grams of {self.food_consumed.name} for {self.meal_type} on {self.date}"
    


class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    GOAL_CHOICES = [
        ('lose', 'Lose Weight'),
        ('maintain', 'Maintain Weight'),
        ('gain', 'Gain Weight'),
    ]

    ACTIVITY_CHOICES = [
        ('low', 'Low Activity'),
        ('moderate', 'Moderate Activity'),
        ('high', 'High Activity'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.PositiveIntegerField(help_text="Age in years",null = True, blank = True)
    gender = models.CharField(max_length = 10, choices = GENDER_CHOICES, default= 'male')
    height_cm  = models.FloatField(help_text="Height in centimeters",null = True, blank = True)
    current_weight_kg = models.FloatField(help_text="Current weight in kilograms",null = True, blank = True)
    target_weight_kg = models.FloatField(help_text="Target weight in kilograms",null = True, blank = True)  
    goal_type = models.CharField(
        max_length=20,
        choices = GOAL_CHOICES,
        default = 'maintain',
    )
    activity_level = models.CharField(
        max_length=20,
        choices = ACTIVITY_CHOICES,
        default = 'moderate',
    )
    created_at = models.DateTimeField(default=now)

    def bmi(self):
        if not self.height_cm or not self.current_weight_kg:
            return None
        height_m = self.height_cm / 100
        return round(self.current_weight_kg / (height_m ** 2), 2)
    
    def bmi_category(self):
        bmi_value = self.bmi()
        if bmi_value is None:
            return "Not Available"
        if bmi_value < 18.5:
            return "UnderWeight"
        elif bmi_value < 25:
            return "Healthy Weight"
        elif bmi_value < 30:
            return "OverWeight"
        return "Obesity"
    
    def bmr(self):
        if not self.age or not self.height_cm or not self.current_weight_kg:
            return None

        if self.gender == 'female':
            value = (10 * self.current_weight_kg) + (6.25 * self.height_cm) - (5 * self.age) - 161

        else:
            value = (10 * self.current_weight_kg) + (6.25 * self.height_cm) - (5 * self.age) + 5
        return round(value,2)
#total daily energy expenditure
    def tdee(self):
        bmr_value = self.bmr()
        if bmr_value is None:
            return None
        activity_multiplier = {
            'low': 1.2, 
            'moderate': 1.55,
            'high': 1.725,
        }
        return round(bmr_value * activity_multiplier.get(self.activity_level, 1.55),2)



    ## CAlculating target according to goal and current weight

    def target_calories(self):
        tdee_value = self.tdee()
        if tdee_value is None:
            return None
        if self.goal_type == 'lose':
            target = tdee_value - 500
        elif self.goal_type == 'gain':
            target = tdee_value + 500
        else:
            target = tdee_value
        return round(max(target, 1200),2)
        
    def target_protein(self):
        calories = self.target_calories()
        if calories is None:
            return None
        return round((calories *0.25)/4,2)
    
    def target_carbs(self):
        calories = self.target_calories()
        if calories is None:
            return None
        return round((calories *0.50)/4,2)
    def target_fat(self):
        calories = self.target_calories()
        if calories is None:
            return None
        return round((calories *0.25)/9,2)
    def __str__(self):
        return f"{self.user.username}'s profile"
        


class WeightLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    weight_kg = models.FloatField()
    date = models.DateField(default=now)
    created_at = models.DateTimeField(default=now)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.weight_kg} kg on {self.date}"