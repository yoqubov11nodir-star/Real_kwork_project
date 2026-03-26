from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Vakansiyalar
    path('vacancies/', views.vacancy_list_view, name='vacancy_list'),
    path('vacancies/create/', views.vacancy_create_view, name='vacancy_create'),
    path('vacancies/<int:pk>/', views.vacancy_detail_view, name='vacancy_detail'),
    path('vacancies/<int:pk>/edit/', views.vacancy_edit_view, name='vacancy_edit'),
    path('vacancies/<int:pk>/close/', views.vacancy_close_view, name='vacancy_close'),
    path('vacancies/<int:pk>/delete/', views.vacancy_delete_view, name='vacancy_delete'),

    path('order/create/<str:username>/', views.order_create_view, name='order_create'),

    # Profil (TARTIB MUHIM!)
    path('profile/edit/', views.profile_edit_view, name='profile_edit'), 
    path('profile/<str:username>/', views.profile_view, name='profile'),
]