from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from .models import Profile, Vacancy
from .forms import VacancyForm, ProfileForm, RegisterForm
from .ai_matching import get_top_workers_for_vacancy, calculate_match_score

def register_view(request):
    if request.user.is_authenticated:
        return redirect('marketplace:dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Xush kelibsiz, {user.first_name}! Tizimda sizning username: {user.username}")
            return redirect('marketplace:dashboard')
    else:
        form = RegisterForm()
    return render(request, 'marketplace/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('marketplace:dashboard')
    
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        
        # 1. Email yoki Username ekanini aniqlash
        if '@' in username_or_email:
            try:
                user_obj = User.objects.get(email=username_or_email)
                username = user_obj.username
            except User.DoesNotExist:
                username = None
        else:
            username = username_or_email

        # 2. Authenticate qilish
        if username:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect(request.GET.get('next', 'marketplace:dashboard'))
        
        messages.error(request, "Email/Username yoki parol noto'g'ri")
        
    return render(request, 'marketplace/login.html')

def logout_view(request):
    logout(request)
    return redirect('marketplace:home')

def home_view(request):
    recent_vacancies = Vacancy.objects.filter(status='OPEN').order_by('-created_at')[:6]
    top_workers = Profile.objects.filter(role='freelancer').order_by('-rating', '-completed_jobs_count')[:8]
    return render(request, 'marketplace/home.html', {'recent_vacancies': recent_vacancies, 'top_workers': top_workers})

@login_required
def dashboard_view(request):
    profile = request.user.profile
    context = {'profile': profile}
    if profile.role == 'client':
        context['my_vacancies'] = Vacancy.objects.filter(company=request.user).order_by('-created_at')[:5]
        context['active_projects'] = request.user.company_projects.filter(status='IN_PROGRESS')[:5]
    else:
        context['available_vacancies'] = Vacancy.objects.filter(status='OPEN').order_by('-created_at')[:5]
        context['my_projects'] = request.user.worker_projects.filter(status='IN_PROGRESS')[:5]
        if hasattr(request.user, 'worker_negotiations'):
            context['my_negotiations'] = request.user.worker_negotiations.filter(status='active').select_related('vacancy')[:5]
    return render(request, 'marketplace/dashboard.html', context)

def vacancy_list_view(request):
    vacancies = Vacancy.objects.filter(status='OPEN')
    q = request.GET.get('q', '')
    category = request.GET.get('category', '')
    if q:
        vacancies = vacancies.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if category:
        vacancies = vacancies.filter(category=category)
    vacancies = vacancies.order_by('-created_at')
    
    vacancies_with_scores = []
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            if profile.role == 'freelancer':
                for v in vacancies:
                    score = calculate_match_score(profile, v)
                    vacancies_with_scores.append({'vacancy': v, 'match_score': round(score * 100, 1)})
        except: pass
    return render(request, 'marketplace/vacancy_list.html', {
        'vacancies': vacancies if not vacancies_with_scores else None,
        'vacancies_with_scores': vacancies_with_scores,
        'q': q, 'category': category, 'categories': Vacancy.CATEGORY_CHOICES
    })

@login_required
def vacancy_create_view(request):
    if request.user.profile.role != 'client':
        messages.error(request, 'Faqat kompaniyalar vakansiya yarata oladi')
        return redirect('marketplace:vacancy_list')
    if request.method == 'POST':
        form = VacancyForm(request.POST)
        if form.is_valid():
            vacancy = form.save(commit=False)
            vacancy.company = request.user
            vacancy.save()
            messages.success(request, 'Vakansiya yaratildi!')
            return redirect('marketplace:vacancy_detail', pk=vacancy.pk)
    else: form = VacancyForm()
    return render(request, 'marketplace/vacancy_form.html', {'form': form})

def vacancy_detail_view(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk)
    top_workers, user_match_score, user_negotiation = [], None, None
    if request.user.is_authenticated:
        profile = request.user.profile
        if profile.role == 'client' and vacancy.company == request.user:
            top_workers = get_top_workers_for_vacancy(vacancy, limit=5)
        elif profile.role == 'freelancer':
            user_match_score = round(calculate_match_score(profile, vacancy) * 100, 1)
            user_negotiation = vacancy.negotiation_rooms.filter(worker=request.user).first() if hasattr(vacancy, 'negotiation_rooms') else None
    
    apps_count = vacancy.negotiation_rooms.filter(status='active').count() if hasattr(vacancy, 'negotiation_rooms') else 0
    return render(request, 'marketplace/vacancy_detail.html', {
        'vacancy': vacancy, 'top_workers': top_workers, 'user_match_score': user_match_score,
        'user_negotiation': user_negotiation, 'applications_count': apps_count
    })

@login_required
def vacancy_edit_view(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk, company=request.user)
    if vacancy.status != 'OPEN':
        messages.error(request, 'Ochiq bo\'lmagan vakansiyani tahrirlab bo\'lmaydi')
        return redirect('marketplace:vacancy_detail', pk=pk)
    if request.method == 'POST':
        form = VacancyForm(request.POST, instance=vacancy)
        if form.is_valid():
            form.save()
            messages.success(request, 'Yangilandi!')
            return redirect('marketplace:vacancy_detail', pk=pk)
    else: form = VacancyForm(instance=vacancy)
    return render(request, 'marketplace/vacancy_form.html', {'form': form, 'vacancy': vacancy})

@login_required
def vacancy_close_view(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk, company=request.user)
    if request.method == 'POST':
        vacancy.status = 'CLOSED'
        vacancy.save()
        messages.success(request, 'Vakansiya yopildi')
        return redirect('marketplace:dashboard')
    return render(request, 'marketplace/vacancy_confirm_close.html', {'vacancy': vacancy})

@login_required
def vacancy_delete_view(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk, company=request.user)
    if vacancy.status not in ['OPEN', 'CLOSED']:
        messages.error(request, 'O\'chirib bo\'lmaydi')
        return redirect('marketplace:vacancy_detail', pk=pk)
    if request.method == 'POST':
        vacancy.delete()
        messages.success(request, 'O\'chirildi')
        return redirect('marketplace:dashboard')
    return render(request, 'marketplace/vacancy_confirm_delete.html', {'vacancy': vacancy})

def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    from reputation.models import Review
    reviews = Review.objects.filter(freelancer=user).order_by('-created_at')[:10]
    return render(request, 'marketplace/profile.html', {'profile_user': user, 'profile': user.profile, 'reviews': reviews})

@login_required
def profile_edit_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid(): 
            form.save()
            user = request.user
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.save()
            messages.success(request, 'Profil muvaffaqiyatli yangilandi!')
            return redirect('marketplace:profile', username=user.username)
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'marketplace/profile_edit.html', {'form': form})

@login_required
def order_create_view(request, username):
    messages.info(request, "Buyurtma berish tizimi tez kunda ishga tushadi.")
    return redirect('marketplace:profile', username=username)