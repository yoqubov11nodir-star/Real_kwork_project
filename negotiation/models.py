from django.db import models
from django.contrib.auth.models import User
from marketplace.models import Vacancy, Project


class ProjectChat(models.Model):
    """
    Har bir loyihada 2 ta chat bo'ladi:
    1. company_pm  — Kompaniya ↔ PM
    2. pm_workers  — PM ↔ Workerlar
    """
    CHAT_TYPE_CHOICES = [
        ('company_pm', 'Kompaniya — PM'),
        ('pm_workers', 'PM — Workerlar'),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='chats'
    )
    chat_type = models.CharField(max_length=20, choices=CHAT_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['project', 'chat_type']
        verbose_name = 'Loyiha chati'
        verbose_name_plural = 'Loyiha chatlari'

    def __str__(self):
        return f"{self.project.vacancy.title} — {self.get_chat_type_display()}"

    def get_participants(self):
        project = self.project
        if self.chat_type == 'company_pm':
            users = [project.company]
            if project.pm:
                users.append(project.pm)
            return users
        else:  # pm_workers
            users = []
            if project.pm:
                users.append(project.pm)
            users += list(project.workers.all())
            return users

    def can_access(self, user):
        return user in self.get_participants()


class Message(models.Model):
    TYPE_CHOICES = [
        ('text', 'Matn'),
        ('system', 'Tizim'),
        ('offer', 'Taklif'),
    ]

    chat = models.ForeignKey(
        ProjectChat, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_messages'
    )
    content = models.TextField()
    message_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='text')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.get_full_name()}: {self.content[:40]}"


class NegotiationRoom(models.Model):
    """
    Vakansiya e'lon qilinganida workerlar
    kompaniya bilan kelishish uchun ishlatiladigan xona.
    Loyiha yaratilgandan keyin ProjectChat ishlatiladi.
    """
    vacancy = models.ForeignKey(
        Vacancy, on_delete=models.CASCADE, related_name='negotiation_rooms'
    )
    company = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='company_negotiations'
    )
    worker = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='worker_negotiations'
    )
    status = models.CharField(max_length=20, choices=[
        ('active', 'Aktiv'),
        ('accepted', 'Qabul qilindi'),
        ('rejected', 'Rad etildi'),
        ('cancelled', 'Bekor'),
    ], default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['vacancy', 'worker']
        verbose_name = 'Muzokaralar xonasi'

    def __str__(self):
        return f"{self.worker.get_full_name()} ↔ {self.vacancy.title}"


class NegotiationMessage(models.Model):
    room = models.ForeignKey(
        NegotiationRoom, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='negotiation_messages'
    )
    content = models.TextField()
    message_type = models.CharField(max_length=10, choices=[
        ('text', 'Matn'),
        ('offer', 'Taklif'),
        ('system', 'Tizim'),
    ], default='text')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class Offer(models.Model):
    """Worker yuboradigan narx taklifi"""
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('accepted', 'Qabul'),
        ('rejected', 'Rad'),
    ]

    room = models.ForeignKey(
        NegotiationRoom, on_delete=models.CASCADE, related_name='offers'
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='offers'
    )
    proposed_budget = models.DecimalField(max_digits=12, decimal_places=2)
    proposed_days = models.IntegerField()
    message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def accept(self):
        from django.utils import timezone
        from datetime import timedelta

        self.status = 'accepted'
        self.save()

        vacancy = self.room.vacancy
        worker = self.room.worker

        # Loyiha yaratish yoki mavjudini topish
        project, created = Project.objects.get_or_create(
            vacancy=vacancy,
            company=vacancy.company,
            defaults={
                'agreed_budget': self.proposed_budget,
                'agreed_days': self.proposed_days,
                'deadline': timezone.now() + timedelta(days=self.proposed_days),
            }
        )

        # Workerni loyihaga qo'shish
        project.workers.add(worker)

        # Muzokaralar xonasini yopish
        self.room.status = 'accepted'
        self.room.save()

        # Vakansiya to'ldimi tekshirish
        if vacancy.is_full():
            vacancy.status = 'IN_PROGRESS'
            vacancy.save()

        return project

    def reject(self):
        self.status = 'rejected'
        self.save()
        self.room.status = 'rejected'
        self.room.save()