from django import forms
from .models import Recipe
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Comment, RecipeStep

class RecipeForm(forms.ModelForm):
    ingredients_text = forms.CharField(required=False, help_text='Ingrese ingredientes separados por comas')

    class Meta:
        model = Recipe
        fields = ['title', 'description', 'estimated_time', 'preparation', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la receta'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Descripción corta'}),
            'estimated_time': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'Minutos estimados'}),
            'preparation': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Pasos para preparar la receta'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        ingredients_text = self.cleaned_data.pop('ingredients_text', '')
        recipe = super().save(commit=commit)
        if commit:
            ingredient_names = [i.strip() for i in ingredients_text.split(',') if i.strip()]
            from .models import Ingredient
            recipe.ingredients.clear()
            for name in ingredient_names:
                ing, _ = Ingredient.objects.get_or_create(name=name)
                recipe.ingredients.add(ing)
        return recipe


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ej: juan123'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ej: correo@ejemplo.com'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'mínimo 8 caracteres'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'repite la contraseña'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Escribe un comentario...'}),
        }


class RecipeStepForm(forms.ModelForm):
    class Meta:
        model = RecipeStep
        fields = ['order', 'description', 'image']
        widgets = {
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe este paso...'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
