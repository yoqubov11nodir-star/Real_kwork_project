from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import OrderViewSet, ProfileViewSet

router = DefaultRouter()
router.register('orders', OrderViewSet)
router.register('profiles', ProfileViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
