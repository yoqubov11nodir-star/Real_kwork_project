import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
# Yangi modellarni import qildik
from .models import ProjectChat, NegotiationRoom, Message

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_pk = self.scope['url_route']['kwargs']['room_pk']
        self.room_group_name = f'chat_{self.room_pk}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        # Foydalanuvchi ruxsatini tekshirish
        has_access = await self.check_room_access()
        if not has_access:
            await self.close()
            return

        # Guruhga qo'shilish
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Online bo'lganini bildirish
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'username': self.user.username,
                'status': 'online'
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'username': self.user.username if self.user.is_authenticated else 'unknown',
                    'status': 'offline'
                }
            )
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'text')

        if message_type == 'chat_message':
            content = data.get('content', '').strip()
            if not content:
                return

            # Xabarni saqlash
            message = await self.save_message(content, 'TEXT')

            # Guruhga yuborish
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message_id': message.pk,
                    'content': content,
                    'sender': self.user.username,
                    'sender_full_name': self.user.get_full_name() or self.user.username,
                    'timestamp': message.created_at.strftime('%H:%M'),
                }
            )

        elif message_type == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'username': self.user.username,
                    'is_typing': data.get('is_typing', False),
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message_id': event['message_id'],
            'content': event['content'],
            'sender': event['sender'],
            'sender_full_name': event['sender_full_name'],
            'timestamp': event['timestamp'],
            'is_own': event['sender'] == self.user.username,
        }))

    async def typing_indicator(self, event):
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'username': event['username'],
                'is_typing': event['is_typing'],
            }))

    async def user_status(self, event):
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'user_status',
                'username': event['username'],
                'status': event['status'],
            }))

    async def offer_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'offer_update',
            'offer_id': event['offer_id'],
            'status': event['status'],
            'message': event.get('message', ''),
        }))

    @database_sync_to_async
    def check_room_access(self):
        try:
            # ChatRoom o'rniga NegotiationRoom ishlatildi
            room = NegotiationRoom.objects.get(pk=self.room_pk)
            # Modelingizga qarab buyer va seller tekshiriladi
            return self.user in [room.buyer, room.seller]
        except NegotiationRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content, message_type='TEXT'):
        # ChatRoom o'rniga NegotiationRoom ishlatildi
        room = NegotiationRoom.objects.get(pk=self.room_pk)
        return Message.objects.create(
            chat=room, # Modelingizda 'room' emas, 'chat' deb nomlangan edi
            sender=self.user,
            content=content,
            message_type=message_type
        )