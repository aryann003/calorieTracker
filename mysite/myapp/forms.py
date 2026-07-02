from django import forms
from .models import Food, Consume, UserProfile,WeightLog



class FoodForm(forms.ModelForm):
    class Meta:
        model = Food
        fields = ['name','category', 'calories', 'carbs', 'protein', 'fat']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'calories': forms.NumberInput(attrs={'class': 'form-control','step':'0.01'}),
            'carbs': forms.NumberInput(attrs={'class': 'form-control', 'step':'0.01'}),
            'protein': forms.NumberInput(attrs={'class': 'form-control','step':'0.01'}),
            'fat': forms.NumberInput(attrs={'class': 'form-control','step':'0.01'}),
        }



class ConsumeForm(forms.ModelForm):
    class Meta:
        model = Consume
        fields = ['food_consumed','quantity_grams','meal_type','date']
        widgets = {
            'food_consumed' : forms.Select(attrs={'class': 'form-control'}),
            'quantity_grams' : forms.NumberInput(attrs={'class': 'form-control', 'step':'0.01'}),
            'meal_type' : forms.Select(attrs={'class': 'form-control'}),    
            'date' : forms.DateInput(attrs={'class': 'form-control','type':'date'}),
        }



class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['age','gender','height_cm','current_weight_kg','target_weight_kg','goal_type','activity_level']
        widgets = {
            'age':forms.NumberInput(attrs={'class':'form-control','min':'1'}),
            'gender':forms.Select(attrs={'class':'form-control'}),
            'height_cm':forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'current_weight_kg':forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'target_weight_kg':forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'goal_type':forms.Select(attrs={'class':'form-control'}),
            'activity_level':forms.Select(attrs={'class':'form-control'}),
        }



class WeightLogForm(forms.ModelForm):
    class Meta:
        model = WeightLog
        fields = ['weight_kg','date']
        widgets = {
            'weight_kg':forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'date':forms.DateInput(attrs={'class':'form-control','type':'date'}),   
        }






