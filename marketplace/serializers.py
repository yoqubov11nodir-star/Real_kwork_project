from rest_framework import serializers
from .models import Order, Profile
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    skills_list = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'role', 'bio', 'skills', 'skills_list',
            'level', 'rating', 'completed_jobs_count',
            'hourly_rate', 'location', 'created_at'
        ]

    def get_skills_list(self, obj):
        return obj.get_skills_list()


class OrderSerializer(serializers.ModelSerializer):
    client = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'client', 'title', 'description',
            'initial_budget', 'final_budget', 'status', 'status_display',
            'category', 'category_display', 'required_skills',
            'deadline_days', 'agreed_deadline', 'created_at'
        ]
        read_only_fields = ['client', 'final_budget', 'agreed_deadline']
