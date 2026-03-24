from django.contrib import admin
from .models import Profile, Vacancy, Application, Project

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'level', 'rating', 'completed_jobs_count', 'created_at']
    list_filter = ['role', 'level']
    search_fields = ['user__username', 'skills', 'bio']

@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    # Modelingizda 'company' bor, 'client' emas. 'budget_min'/'budget_max' bor.
    list_display = [
        'title', 
        'company', 
        'category', 
        'budget_min', 
        'budget_max', 
        'status',
        'is_team_project', 
        'created_at'
    ]
    list_filter = ['status', 'category', 'is_team_project']
    search_fields = ['title', 'description']
    # 'description_embedding' modelda yo'q, shuning uchun readonly bo'sh qoladi
    readonly_fields = []

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['worker', 'vacancy', 'status', 'created_at']
    list_filter = ['status']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['vacancy', 'company', 'pm', 'status', 'created_at']
    list_filter = ['status']