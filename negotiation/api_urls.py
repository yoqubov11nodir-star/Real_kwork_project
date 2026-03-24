from django.urls import path
from .api_views import ChatRoomListAPIView, OfferListAPIView

urlpatterns = [
    path('rooms/', ChatRoomListAPIView.as_view(), name='api_chat_rooms'),
    path('offers/', OfferListAPIView.as_view(), name='api_offers'),
]
