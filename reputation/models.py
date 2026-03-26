from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# -------------------------------------------------------------------------
# REVIEW MODELI
# -------------------------------------------------------------------------
class Review(models.Model):
    # DIQQAT: Project modeli 'marketplace' ilovasida bo'lgani uchun manzil o'zgartirildi.
    # Bu 'reputation.Review.project: (fields.E300)' xatosini yo'qotadi.
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
        # MUHIM: Bu qator bitta loyihada bir kishi bir kishiga faqat 1 marta baho berishini ta'minlaydi
        # Bu orqali UNIQUE constraint xatosini ham hal qilamiz
        unique_together = ['project', 'reviewer', 'freelancer']

    def __str__(self):
        return f"{self.reviewer.username} → {self.freelancer.username}: {self.stars}⭐"

    def save(self, *args, **kwargs):
        # Ballarni float (o'nlik son) ko'rinishiga o'tkazish (hisob-kitob uchun)
        c = float(self.communication_score or 0)
        q = float(self.quality_score or 0)
        d = float(self.deadline_score or 0)
        
        # O'rtacha yulduzni (stars) hisoblash
        self.stars = (c + q + d) / 3
        
        # Ma'lumotni bazaga saqlash
        super().save(*args, **kwargs)
        # Foydalanuvchi reytingini va ishlar sonini yangilash
        self._update_rating()

    def _update_rating(self):
        from django.db.models import Avg
        # Freelancerga berilgan barcha yulduzlar o'rtachasini hisoblash
        avg_data = Review.objects.filter(
            freelancer=self.freelancer
        ).aggregate(avg=Avg('stars'))
        
        avg = avg_data['avg']
        profile = self.freelancer.profile
        
        if avg is not None:
            # Profil reytingini yangilash (bir xonali aniqlikda)
            profile.rating = round(float(avg), 1)
            # Bajarilgan ishlar sonini sanash
            profile.completed_jobs_count = Review.objects.filter(
                freelancer=self.freelancer
            ).count()
            profile.save()
            
            # Profil darajasini (level) yangilash metodini chaqirish
            if hasattr(profile, 'update_level'):
                profile.update_level()
            
            # Nishonlarni (Badge) tekshirish va berish
            award_badges(self.freelancer)

# -------------------------------------------------------------------------
# BADGE MODELI
# -------------------------------------------------------------------------
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
        # Bitta foydalanuvchi bitta nishonni ikki marta ololmaydi
        unique_together = ['user', 'badge_type']
        verbose_name = 'Nishon'
        verbose_name_plural = 'Nishonlar'

    def __str__(self):
        return f"{self.user.username} — {self.get_badge_type_display()}"

# -------------------------------------------------------------------------
# LEVEL HISTORY MODELI
# -------------------------------------------------------------------------
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

# -------------------------------------------------------------------------
# BADGE BERISH FUNKSIYASI
# -------------------------------------------------------------------------
def award_badges(user):
    profile = user.profile
    # Foydalanuvchida allaqachon bor bo'lgan nishonlarni aniqlash
    existing = set(Badge.objects.filter(user=user).values_list('badge_type', flat=True))
    to_award = []
    
    # Birinchi ish nishoni
    if profile.completed_jobs_count >= 1 and 'first_job' not in existing:
        to_award.append('first_job')
    
    # 5 ta ish nishoni
    if profile.completed_jobs_count >= 5 and 'five_jobs' not in existing:
        to_award.append('five_jobs')
    
    # Mukammal reyting nishoni (kamida 3 ta ish va 4.9+ reyting)
    if profile.rating >= 4.9 and profile.completed_jobs_count >= 3 and 'perfect_rating' not in existing:
        to_award.append('perfect_rating')
    
    # Veteran nishoni (3-darajaga chiqqanda)
    if hasattr(profile, 'level') and profile.level == 3 and 'veteran' not in existing:
        to_award.append('veteran')
    
    # Ro'yxatdagi yangi nishonlarni bazaga qo'shish
    for badge_type in to_award:
        Badge.objects.get_or_create(user=user, badge_type=badge_type)