from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


app_name = 'recipes'

urlpatterns = [
    path('', views.home, name='home'),
    path('recetas/', views.recipe_list, name='list'),
    path('recipe/<int:pk>/', views.recipe_detail, name='detail'),
    path('recipe/add/', views.recipe_create, name='add'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='recipes/login.html'), name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('recipe/<int:pk>/edit/', views.recipe_edit, name='edit'),
    path('recipe/<int:pk>/delete/', views.recipe_delete, name='delete'),
    path('recipe/<int:pk>/rate/', views.rate_recipe, name='rate'),
    path('recipe/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('recipe/save_ajax/', views.save_recipe_ajax, name='save_ajax'),
    path('recipe/<int:pk>/toggle_save/', views.toggle_save_recipe, name='toggle_save'),
    path('saved/', views.saved_recipes_list, name='saved_list'),
    path('my-recipes/', views.my_recipes, name='my_recipes'),
]
