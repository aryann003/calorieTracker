"""
URL configuration for mysite project.
"""

from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from myapp import views


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.home, name='home'),
    path('dashboard/', views.index, name='index'),

    path('profile/', views.profile_view, name='profile'),
    path('weight-log/', views.weight_log_view, name='weight_log'),

    path('delete/<int:consume_id>/', views.delete_consume, name='delete_consume'),
    path('add-food/', views.add_food, name='add_food'),

    path(
        'login/',
        auth_views.LoginView.as_view(template_name='registration/login.html'),
        name='login'
    ),

    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),

    path(
        'password/change/',
        auth_views.PasswordChangeView.as_view(
            template_name='registration/password_change_form.html',
            success_url='/password/change/done/'
        ),
        name='password_change'
    ),

    path(
        'password/change/done/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='registration/password_change_done.html'
        ),
        name='password_change_done'
    ),
]