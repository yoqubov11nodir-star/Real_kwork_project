from django.urls import path
from . import views

app_name = 'reputation'

urlpatterns = [
     path('review/project/<int:project_pk>/user/<int:user_pk>/', views.create_review_project, name='create_review_project'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('reviews/<str:username>/',
         views.freelancer_reviews_view, name='freelancer_reviews'),
]