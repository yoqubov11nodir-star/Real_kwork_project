from django.urls import path
from .api_views import ReviewListAPIView

urlpatterns = [
    path('reviews/', ReviewListAPIView.as_view(), name='api_reviews'),
]
