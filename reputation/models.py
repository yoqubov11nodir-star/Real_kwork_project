from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Review(models.Model):

    project = models.ForeignKey(
        'marketplace.Project', 
        on_delete=models.CASCADE, 
        related_name='reviews'
    )
    reviewer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='given_reviews'
    )
    freelancer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_reviews'
    )
    stars = models.FloatField(
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)]
    )
    comment = models.TextField()
    communication_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], 
        default=5
    )
    quality_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], 
        default=5
    )
    deadline_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], 
        default=5
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Sharh'
        verbose_name_plural = 'Sharhlar'

        unique_together = ['project', 'reviewer', 'freelancer']

    def __str__(self):
        return f"{self.reviewer.username} → {self.freelancer.username}: {self.stars}⭐"

    def save(self, *args, **kwargs):
        c = float(self.communication_score or 0)
        q = float(self.quality_score or 0)
        d = float(self.deadline_score or 0)
        
        self.stars = (c + q + d) / 3
        
        super().save(*args, **kwargs)
        self._update_rating()

    def _update_rating(self):
        from django.db.models import Avg
        avg_data = Review.objects.filter(
            freelancer=self.freelancer
        ).aggregate(avg=Avg('stars'))
        
        avg = avg_data['avg']
        profile = self.freelancer.profile
        
        if avg is not None:
            profile.rating = round(float(avg), 1)
            profile.completed_jobs_count = Review.objects.filter(
                freelancer=self.freelancer
            ).count()
            profile.save()
            
            if hasattr(profile, 'update_level'):
                profile.update_level()
            
            award_badges(self.freelancer)

class Badge(models.Model):
    BADGE_CHOICES = [
        ('first_job', '🎯 Birinchi ish'),
        ('five_jobs', '⭐ 5 ta ish'),
        ('perfect_rating', '💎 Mukammal reyting'),
        ('fast_delivery', '⚡ Tez yetkazish'),
        ('top_rated', '🏆 Top worker'),
        ('veteran', '👑 Veteran'),
    ]
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='badges'
    )
    badge_type = models.CharField(max_length=30, choices=BADGE_CHOICES)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'badge_type']
        verbose_name = 'Nishon'
        verbose_name_plural = 'Nishonlar'

    def __str__(self):
        return f"{self.user.username} — {self.get_badge_type_display()}"

class LevelHistory(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='level_history'
    )
    old_level = models.IntegerField()
    new_level = models.IntegerField()
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Daraja tarixi'
        verbose_name_plural = 'Daraja tarixlari'

    def __str__(self):
        return f"{self.user.username}: {self.old_level} -> {self.new_level}"


def award_badges(user):
    profile = user.profile
    existing = set(Badge.objects.filter(user=user).values_list('badge_type', flat=True))
    to_award = []
    
    if profile.completed_jobs_count >= 1 and 'first_job' not in existing:
        to_award.append('first_job')
    
    if profile.completed_jobs_count >= 5 and 'five_jobs' not in existing:
        to_award.append('five_jobs')
    
    if profile.rating >= 4.9 and profile.completed_jobs_count >= 3 and 'perfect_rating' not in existing:
        to_award.append('perfect_rating')
    
    if hasattr(profile, 'level') and profile.level == 3 and 'veteran' not in existing:
        to_award.append('veteran')
    
    for badge_type in to_award:
        Badge.objects.get_or_create(user=user, badge_type=badge_type)