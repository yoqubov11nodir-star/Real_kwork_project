from django.contrib import admin
from .models import Review, Badge, LevelHistory


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['reviewer', 'freelancer', 'stars', 'created_at']
    list_filter = ['stars']


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge_type', 'awarded_at']


@admin.register(LevelHistory)
class LevelHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'old_level', 'new_level', 'reason', 'created_at']
