from django.urls import path
from . import views

app_name = 'negotiation'

urlpatterns = [
    # Muzokaralar (vakansiya bosqichi)
    path('negotiate/<int:vacancy_pk>/', views.start_negotiation, name='start_negotiation'),
    path('room/<int:pk>/', views.negotiation_room, name='negotiation_room'),
    path('room/<int:room_pk>/message/', views.send_negotiation_message, name='send_negotiation_message'),
    path('room/<int:room_pk>/offer/', views.send_offer, name='send_offer'),
    path('offer/<int:offer_pk>/accept/', views.accept_offer, name='accept_offer'),
    path('offer/<int:offer_pk>/reject/', views.reject_offer, name='reject_offer'),

    # Kompaniya: arizalar va PM tayinlash
    path('vacancy/<int:vacancy_pk>/applications/', views.vacancy_applications, name='vacancy_applications'),
    path('project/<int:project_pk>/assign-pm/', views.assign_pm, name='assign_pm'),

    # Loyiha chatlari
    path('projects/', views.my_projects, name='my_projects'),
    path('project/<int:pk>/', views.project_detail, name='project_detail'),
    path('project/<int:pk>/complete/', views.complete_project, name='complete_project'),
    path('chat/<int:chat_pk>/', views.project_chat, name='project_chat'),
    path('chat/<int:chat_pk>/message/', views.send_project_message, name='send_project_message'),
]