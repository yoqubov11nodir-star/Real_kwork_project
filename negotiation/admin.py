from django.contrib import admin
from .models import ProjectChat, Message, NegotiationRoom, NegotiationMessage, Offer

@admin.register(ProjectChat)
class ProjectChatAdmin(admin.ModelAdmin):
    list_display = ['project', 'chat_type', 'created_at']
    list_filter = ['chat_type']
    search_fields = ['project__vacancy__title']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['chat', 'sender', 'message_type', 'is_read', 'created_at']
    list_filter = ['message_type', 'is_read']
    search_fields = ['content', 'sender__username']

@admin.register(NegotiationRoom)
class NegotiationRoomAdmin(admin.ModelAdmin):
    list_display = ['vacancy', 'company', 'worker', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['vacancy__title', 'worker__username', 'company__username']

@admin.register(NegotiationMessage)
class NegotiationMessageAdmin(admin.ModelAdmin):
    list_display = ['room', 'sender', 'message_type', 'created_at']
    list_filter = ['message_type']

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    # Sizning modelingizda 'proposed_price' emas, 'proposed_budget' deb yozilgan
    # 'is_accepted' o'rniga esa 'status' ishlatilgan
    list_display = ['room', 'sender', 'proposed_budget', 'proposed_days', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['room__vacancy__title', 'sender__username']