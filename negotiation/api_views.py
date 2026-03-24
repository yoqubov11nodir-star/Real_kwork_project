from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import ChatRoom, Offer
from .serializers import ChatRoomSerializer, OfferSerializer


class ChatRoomListAPIView(generics.ListAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ChatRoom.objects.filter(
            client=user
        ) | ChatRoom.objects.filter(freelancer=user)


class OfferListAPIView(generics.ListAPIView):
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Offer.objects.filter(
            room__client=user
        ) | Offer.objects.filter(room__freelancer=user)
