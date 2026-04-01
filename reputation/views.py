from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from django.contrib.auth.models import User

from .models import Review, Badge, award_badges
from .forms import ReviewForm
from marketplace.models import Project

def create_review_project(request, project_pk, user_pk):
    project = get_object_or_404(Project, pk=project_pk)
    freelancer = get_object_or_404(User, pk=user_pk)

    already_reviewed = Review.objects.filter(
        project=project, 
        reviewer=request.user, 
        freelancer=freelancer
    ).exists()
    
    if already_reviewed:
        messages.warning(request, f"Siz {freelancer.get_full_name()}ga allaqachon baho bergansiz!")
        return redirect('negotiation:project_detail', pk=project.pk)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.project = project
            review.reviewer = request.user
            review.freelancer = freelancer
            
            try:
                review.save()
                messages.success(request, f"{freelancer.get_full_name()} muvaffaqiyatli baholandi!")
                return redirect('negotiation:project_detail', pk=project.pk)
            except Exception as e:
                messages.error(request, f"Xatolik: {e}")
    else:
        form = ReviewForm()
    
    return render(request, 'reputation/create_review.html', {
        'form': form,
        'project': project,
        'freelancer': freelancer
    })

def leaderboard_view(request):
    from marketplace.models import Profile
    profiles = Profile.objects.filter(
        role='freelancer',
        completed_jobs_count__gt=0
    ).select_related('user').order_by('-rating', '-completed_jobs_count')[:20]

    top_workers = []
    for i, profile in enumerate(profiles, 1):
        badges = Badge.objects.filter(user=profile.user)
        top_workers.append({
            'rank': i,
            'profile': profile,
            'badges': badges,
        })

    return render(request, 'reputation/leaderboard.html', {
        'top_workers': top_workers,
    })


def freelancer_reviews_view(request, username):
    user = get_object_or_404(User, username=username)
    reviews = Review.objects.filter(
        freelancer=user
    ).select_related('reviewer', 'project').order_by('-created_at')

    avg_scores = reviews.aggregate(
        avg_communication=Avg('communication_score'),
        avg_quality=Avg('quality_score'),
        avg_deadline=Avg('deadline_score'),
        avg_overall=Avg('stars'),
    )

    return render(request, 'reputation/freelancer_reviews.html', {
        'profile_user': user,
        'reviews': reviews,
        'avg_scores': avg_scores,
    })