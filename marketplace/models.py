from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    ROLE_CHOICES = [
        ('client', 'Kompaniya'),
        ('freelancer', 'Worker'),
    ]
    LEVEL_CHOICES = [
        (1, 'Level 1'),
        (2, 'Level 2'),
        (3, 'Level 3'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='freelancer')
    bio = models.TextField(blank=True)
    skills = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    level = models.IntegerField(choices=LEVEL_CHOICES, default=1)
    rating = models.FloatField(default=0.0)
    completed_jobs_count = models.IntegerField(default=0)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    portfolio_url = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"

    def get_skills_list(self):
        if self.skills:
            return [s.strip() for s in self.skills.split(',')]
        return []

    def update_level(self):
        from django.conf import settings
        if self.completed_jobs_count >= settings.LEVEL_3_MIN_JOBS:
            self.level = 3
        elif (self.completed_jobs_count >= settings.LEVEL_2_MIN_JOBS and
              self.rating >= settings.LEVEL_2_MIN_RATING):
            self.level = 2
        else:
            self.level = 1
        self.save(update_fields=['level'])

    class Meta:
        verbose_name = 'Profil'
        verbose_name_plural = 'Profillar'

@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()

class Vacancy(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Ochiq'),
        ('IN_PROGRESS', 'Jarayonda'),
        ('CLOSED', 'Yopildi'),
        ('CANCELLED', 'Bekor'),
        ('COMPLETED', 'Yakunlandi'),
    ]
    CATEGORY_CHOICES = [
        ('development', 'Dasturlash'),
        ('design', 'Dizayn'),
        ('marketing', 'Marketing'),
        ('writing', 'Yozuv'),
        ('video', 'Video'),
        ('other', 'Boshqa'),
    ]

    company = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vacancies')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    required_skills = models.TextField(blank=True)
    budget_min = models.DecimalField(max_digits=12, decimal_places=2)
    budget_max = models.DecimalField(max_digits=12, decimal_places=2)
    deadline_days = models.IntegerField()
    required_workers = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    is_team_project = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} — {self.company.get_full_name()}"

    def get_skills_list(self):
        if self.required_skills:
            return [s.strip() for s in self.required_skills.split(',')]
        return []

    @property
    def hired_count(self):
        return self.projects.filter(status__in=['IN_PROGRESS', 'COMPLETED']).count()

    def is_full(self):
        return self.hired_count >= self.required_workers

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Vakansiya'
        verbose_name_plural = 'Vakansiyalar'

# Application va Project modellarini o'zgartirmasdan saqlab qolamiz...
class Application(models.Model):
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='applications')
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField(blank=True)
    proposed_budget = models.DecimalField(max_digits=12, decimal_places=2)
    proposed_days = models.IntegerField()
    status = models.CharField(max_length=10, choices=[('pending', 'Kutilmoqda'), ('accepted', 'Qabul qilindi'), ('rejected', 'Rad etildi')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['vacancy', 'worker']
        ordering = ['-created_at']

class Project(models.Model):
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='projects')
    company = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_projects')
    pm = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pm_projects')
    workers = models.ManyToManyField(User, related_name='worker_projects', blank=True)
    agreed_budget = models.DecimalField(max_digits=12, decimal_places=2)
    agreed_days = models.IntegerField()
    deadline = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('IN_PROGRESS', 'Jarayonda'), ('COMPLETED', 'Yakunlandi'), ('DELAYED', 'Kechikdi'), ('CANCELLED', 'Bekor')], default='IN_PROGRESS')
    created_at = models.DateTimeField(auto_now_add=True)