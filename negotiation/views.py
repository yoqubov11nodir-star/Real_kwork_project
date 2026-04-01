from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User

from reputation.models import Review 
from .models import (
    NegotiationRoom, NegotiationMessage,
    Offer, ProjectChat, Message
)
from marketplace.models import Vacancy, Project

@login_required
def start_negotiation(request, vacancy_pk):
    """Worker vakansiyaga ariza beradi va muzokaralar boshlanadi"""
    vacancy = get_object_or_404(Vacancy, pk=vacancy_pk)

    if vacancy.status not in ['OPEN']:
        messages.error(request, 'Bu vakansiya yopilgan')
        return redirect('marketplace:vacancy_detail', pk=vacancy_pk)

    if request.user == vacancy.company:
        messages.error(request, 'Siz bu vakansiya egasisiz')
        return redirect('marketplace:vacancy_detail', pk=vacancy_pk)

    if request.user.profile.role != 'freelancer':
        messages.error(request, 'Faqat workerlar ariza bera oladi')
        return redirect('marketplace:vacancy_detail', pk=vacancy_pk)

    room, created = NegotiationRoom.objects.get_or_create(
        vacancy=vacancy,
        worker=request.user,
        defaults={'company': vacancy.company}
    )

    if created:
        NegotiationMessage.objects.create(
            room=room,
            sender=request.user,
            content=f"{request.user.get_full_name()} muzokaralarni boshladi",
            message_type='system'
        )

    return redirect('negotiation:negotiation_room', pk=room.pk)


@login_required
def negotiation_room(request, pk):
    """Worker va kompaniya o'rtasidagi muzokaralar xonasi"""
    room = get_object_or_404(NegotiationRoom, pk=pk)

    if request.user not in [room.company, room.worker]:
        messages.error(request, 'Ruxsat yo\'q')
        return redirect('marketplace:vacancy_list')

    neg_messages = room.messages.order_by('created_at')
    offers = room.offers.order_by('-created_at')
    pending_offer = offers.filter(status='pending').first()

    return render(request, 'negotiation/negotiation_room.html', {
        'room': room,
        'neg_messages': neg_messages,
        'offers': offers,
        'pending_offer': pending_offer,
        'is_company': request.user == room.company,
        'is_worker': request.user == room.worker,
    })


@login_required
@require_POST
def send_negotiation_message(request, room_pk):
    room = get_object_or_404(NegotiationRoom, pk=room_pk)
    if request.user not in [room.company, room.worker]:
        return JsonResponse({'error': 'Ruxsat yo\'q'}, status=403)

    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Xabar bo\'sh'}, status=400)

    msg = NegotiationMessage.objects.create(
        room=room,
        sender=request.user,
        content=content,
        message_type='text'
    )
    return JsonResponse({
        'success': True,
        'message': {
            'id': msg.pk,
            'content': msg.content,
            'sender': request.user.get_full_name(),
            'time': msg.created_at.strftime('%H:%M'),
            'is_own': True,
        }
    })


@login_required
@require_POST
def send_offer(request, room_pk):
    room = get_object_or_404(NegotiationRoom, pk=room_pk, worker=request.user)

    budget = request.POST.get('proposed_budget')
    days = request.POST.get('proposed_days')
    msg_text = request.POST.get('message', '')

    if not budget or not days:
        return JsonResponse({'error': 'Narx va muddat kerak'}, status=400)

    room.offers.filter(status='pending').update(status='rejected')

    offer = Offer.objects.create(
        room=room,
        sender=request.user,
        proposed_budget=budget,
        proposed_days=days,
        message=msg_text
    )

    NegotiationMessage.objects.create(
        room=room,
        sender=request.user,
        content=f"💰 Taklif: ${budget} / {days} kun",
        message_type='offer'
    )

    return JsonResponse({'success': True, 'offer_id': offer.pk})


@login_required
@require_POST
def accept_offer(request, offer_pk):
    offer = get_object_or_404(Offer, pk=offer_pk, room__company=request.user)

    if offer.status != 'pending':
        return JsonResponse({'error': 'Bu taklif allaqachon ko\'rib chiqilgan'}, status=400)

    project = offer.accept()

    NegotiationMessage.objects.create(
        room=offer.room,
        sender=request.user,
        content=f"✅ Taklif qabul qilindi! ${offer.proposed_budget} / {offer.proposed_days} kun",
        message_type='system'
    )

    return JsonResponse({'success': True, 'project_id': project.pk})

@login_required
@require_POST
def reject_offer(request, offer_pk):
    offer = get_object_or_404(Offer, pk=offer_pk, room__company=request.user)
    
    offer.reject()

    offer.room.status = 'rejected'
    offer.room.save()

    NegotiationMessage.objects.create(
        room=offer.room,
        sender=request.user,
        content="❌ Taklif rad etildi",
        message_type='system'
    )
    
    return JsonResponse({'success': True})

@login_required
def vacancy_applications(request, vacancy_pk):
    """Kompaniya barcha arizalarni ko'radi"""
    vacancy = get_object_or_404(Vacancy, pk=vacancy_pk, company=request.user)
    rooms = vacancy.negotiation_rooms.select_related(
        'worker', 'worker__profile'
    ).order_by('-created_at')

    return render(request, 'negotiation/applications.html', {
        'vacancy': vacancy,
        'rooms': rooms,
    })

@login_required
def assign_pm(request, project_pk):
    """Kompaniya PM tayinlaydi — avtomatik 2 ta chat yaratiladi"""
    project = get_object_or_404(Project, pk=project_pk, company=request.user)

    if request.method == 'POST':
        pm_id = request.POST.get('pm_id')
        pm = get_object_or_404(User, pk=pm_id)

        if pm not in project.workers.all():
            messages.error(request, 'PM loyiha workeri bo\'lishi kerak')
            return redirect('negotiation:project_detail', pk=project_pk)

        project.pm = pm
        project.save()

        company_pm_chat, _ = ProjectChat.objects.get_or_create(
            project=project,
            chat_type='company_pm'
        )
        pm_workers_chat, _ = ProjectChat.objects.get_or_create(
            project=project,
            chat_type='pm_workers'
        )

        Message.objects.create(
            chat=company_pm_chat,
            sender=request.user,
            content=f"🎯 {pm.get_full_name()} PM etib tayinlandi. Loyiha chati ochildi.",
            message_type='system'
        )
        Message.objects.create(
            chat=pm_workers_chat,
            sender=pm,
            content=f"👋 Salom! Men {pm.get_full_name()} — bu loyihaning PM iman. Birgalikda ishlaymiz!",
            message_type='system'
        )

        messages.success(request, f"{pm.get_full_name()} PM etib tayinlandi!")
        return redirect('negotiation:project_detail', pk=project_pk)

    return redirect('negotiation:project_detail', pk=project_pk)


@login_required
def project_detail(request, pk):
    """Loyiha sahifasi — chatlar, workerlar, PM va baholash holati"""
    project = get_object_or_404(Project, pk=pk)
    user = request.user

    is_company = user == project.company
    is_pm = user == project.pm
    is_worker = project.workers.filter(id=user.id).exists()

    if not (is_company or is_pm or is_worker):
        messages.error(request, 'Ruxsat yo\'q')
        return redirect('marketplace:vacancy_list')

    rated_users_ids = Review.objects.filter(
        project=project,
        reviewer=user
    ).values_list('freelancer_id', flat=True)

    company_pm_chat = project.chats.filter(chat_type='company_pm').first()
    pm_workers_chat = project.chats.filter(chat_type='pm_workers').first()

    return render(request, 'negotiation/project_detail.html', {
        'project': project,
        'is_company': is_company,
        'is_pm': is_pm,
        'is_worker': is_worker,
        'company_pm_chat': company_pm_chat,
        'pm_workers_chat': pm_workers_chat,
        'rated_users_ids': rated_users_ids,
    })


@login_required
def project_chat(request, chat_pk):
    """Loyiha chati — company_pm yoki pm_workers"""
    chat = get_object_or_404(ProjectChat, pk=chat_pk)

    if not chat.can_access(request.user):
        messages.error(request, 'Bu chatga ruxsatingiz yo\'q')
        return redirect('negotiation:my_projects')

    chat_messages = chat.messages.select_related('sender').order_by('created_at')

    chat.messages.filter(is_read=False).exclude(
        sender=request.user
    ).update(is_read=True)

    project = chat.project
    is_company = request.user == project.company
    is_pm = request.user == project.pm
    is_worker = request.user in project.workers.all()

    return render(request, 'negotiation/project_chat.html', {
        'chat': chat,
        'chat_messages': chat_messages,
        'project': project,
        'is_company': is_company,
        'is_pm': is_pm,
        'is_worker': is_worker,
    })

@login_required
@require_POST
def send_project_message(request, chat_pk):
    chat = get_object_or_404(ProjectChat, pk=chat_pk)

    if not chat.can_access(request.user):
        return JsonResponse({'error': 'Ruxsat yo\'q'}, status=403)

    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Xabar bo\'sh'}, status=400)

    msg = Message.objects.create(
        chat=chat,
        sender=request.user,
        content=content,
        message_type='text'
    )

    return JsonResponse({
        'success': True,
        'message': {
            'id': msg.pk,
            'content': msg.content,
            'sender': request.user.get_full_name(),
            'time': msg.created_at.strftime('%H:%M'),
        }
    })


@login_required
def my_projects(request):
    """Foydalanuvchining barcha loyihalari"""
    user = request.user
    projects = []

    if user.profile.role == 'client':
        qs = Project.objects.filter(company=user)
    else:
        qs = Project.objects.filter(
            workers=user
        ) | Project.objects.filter(pm=user)

    qs = qs.distinct().select_related(
        'vacancy', 'company', 'pm'
    ).prefetch_related('workers', 'chats').order_by('-created_at')

    for project in qs:
        company_pm_chat = project.chats.filter(chat_type='company_pm').first()
        pm_workers_chat = project.chats.filter(chat_type='pm_workers').first()
        projects.append({
            'project': project,
            'company_pm_chat': company_pm_chat,
            'pm_workers_chat': pm_workers_chat,
        })

    return render(request, 'negotiation/my_projects.html', {
        'projects': projects,
        'is_company': user.profile.role == 'client',
    })


@login_required
def complete_project(request, pk):
    project = get_object_or_404(Project, pk=pk, company=request.user)
    if request.method == 'POST':
        project.status = 'COMPLETED'
        project.save()

        project.vacancy.status = 'COMPLETED'
        project.vacancy.save()

        for worker in project.workers.all():
            worker.profile.completed_jobs_count += 1
            worker.profile.save() 
            worker.profile.update_level()

        messages.success(request, 'Loyiha yakunlandi!')
        
        if project.pm:
            return redirect('reputation:create_review_project', project_pk=project.pk, user_pk=project.pm.pk)
        
        return redirect('negotiation:project_detail', pk=project.pk)

    return redirect('negotiation:project_detail', pk=pk)