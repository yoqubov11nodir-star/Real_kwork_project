from rest_framework import serializers
from .models import ChatRoom, Message, Offer


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender_username', 'content', 'message_type', 'is_read', 'created_at']


class OfferSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Offer
        fields = [
            'id', 'sender_username', 'proposed_price',
            'delivery_days', 'message', 'status', 'is_accepted', 'created_at'
        ]


class ChatRoomSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    offers = OfferSerializer(many=True, read_only=True)
    order_title = serializers.CharField(source='order.title', read_only=True)

    class Meta:
        model = ChatRoom
        fields = ['id', 'order_title', 'is_active', 'messages', 'offers', 'created_at']
