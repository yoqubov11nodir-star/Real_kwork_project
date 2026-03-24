from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):
    project = models.OneToOneField(
        'marketplace.Project',
        on_delete=models.CASCADE,
        related_name='review'
    )
    reviewer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='given_reviews'
    )
    freelancer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='received_reviews'
    )
    stars = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    communication_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], default=5
    )
    quality_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], default=5
    )
    deadline_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], default=5
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Sharh'
        verbose_name_plural = 'Sharhlar'

    def __str__(self):
        return f"{self.reviewer.get_full_name()} → {self.freelancer.get_full_name()}: {self.stars}⭐"

    def save(self, *args, **kwargs):
        self.stars = round(
            (self.communication_score + self.quality_score + self.deadline_score) / 3
        )
        super().save(*args, **kwargs)
        self._update_rating()

    def _update_rating(self):
        from django.db.models import Avg
        avg = Review.objects.filter(
            freelancer=self.freelancer
        ).aggregate(avg=Avg('stars'))['avg']
        if avg:
            self.freelancer.profile.rating = round(avg, 2)
            self.freelancer.profile.save(update_fields=['rating'])
            self.freelancer.profile.update_level()


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
        User, on_delete=models.CASCADE, related_name='badges'
    )
    badge_type = models.CharField(max_length=30, choices=BADGE_CHOICES)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'badge_type']
        verbose_name = 'Nishon'
        verbose_name_plural = 'Nishonlar'

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.get_badge_type_display()}"


class LevelHistory(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='level_history'
    )
    old_level = models.IntegerField()
    new_level = models.IntegerField()
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Daraja tarixi'

    def __str__(self):
        return f"{self.user.get_full_name()}: {self.old_level} → {self.new_level}"


def award_badges(user):
    profile = user.profile
    existing = set(
        Badge.objects.filter(user=user).values_list('badge_type', flat=True)
    )
    to_award = []
    if profile.completed_jobs_count >= 1 and 'first_job' not in existing:
        to_award.append('first_job')
    if profile.completed_jobs_count >= 5 and 'five_jobs' not in existing:
        to_award.append('five_jobs')
    if profile.rating >= 5.0 and profile.completed_jobs_count >= 3 and 'perfect_rating' not in existing:
        to_award.append('perfect_rating')
    if profile.level == 3 and 'veteran' not in existing:
        to_award.append('veteran')
    for badge_type in to_award:
        Badge.objects.create(user=user, badge_type=badge_type)
    return to_award