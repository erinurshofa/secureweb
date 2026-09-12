from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError, PermissionDenied

from .models import Competition, ParticipantEnrollment, CompetitionStatus
from attempts.models import ExamAttempt, AttemptStatus
from services.exam_service import ExamService


@login_required(login_url='login')
def dashboard_view(request):
    user = request.user
    
    # Ambil kompetisi yang terbuka atau terdaftar
    if user.is_superuser or user.is_staff:
        competitions = Competition.objects.all().order_by('-start_time')
    else:
        enrolled_ids = ParticipantEnrollment.objects.filter(
            participant=user,
            is_disqualified=False
        ).values_list('competition_id', flat=True)
        competitions = Competition.objects.filter(id__in=enrolled_ids).order_by('-start_time')

    competition_items = []
    for comp in competitions:
        # Cek attempt aktif
        active_attempt = ExamAttempt.objects.filter(
            competition=comp,
            participant=user,
            status=AttemptStatus.IN_PROGRESS
        ).first()

        completed_attempt = ExamAttempt.objects.filter(
            competition=comp,
            participant=user,
            status__in=[AttemptStatus.SUBMITTED, AttemptStatus.AUTO_SUBMITTED]
        ).first()

        can_start = comp.status == CompetitionStatus.OPEN and not active_attempt and not completed_attempt

        competition_items.append({
            'competition': comp,
            'question_count': comp.questions.count(),
            'active_attempt': active_attempt,
            'is_completed': bool(completed_attempt),
            'can_start': can_start
        })

    return render(request, 'competitions/dashboard.html', {
        'competitions': competition_items
    })


@login_required(login_url='login')
def start_attempt_view(request, competition_id):
    if request.method != 'POST':
        return redirect('dashboard')
        
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    try:
        attempt = ExamService.start_attempt(
            user=request.user,
            competition_id=str(competition_id),
            ip_address=ip_address,
            user_agent=user_agent
        )
        return redirect('exam_arena', attempt_id=attempt.id)
    except (ValidationError, PermissionDenied) as e:
        messages.error(request, str(e))
        return redirect('dashboard')


@login_required(login_url='login')
def competition_status_api(request):
    """API Real-time Polling untuk Dashboard Peserta."""
    user = request.user
    if user.is_superuser or user.is_staff:
        competitions = Competition.objects.all().order_by('-start_time')
    else:
        enrolled_ids = ParticipantEnrollment.objects.filter(
            participant=user,
            is_disqualified=False
        ).values_list('competition_id', flat=True)
        competitions = Competition.objects.filter(id__in=enrolled_ids).order_by('-start_time')

    data = []
    for comp in competitions:
        active_attempt = ExamAttempt.objects.filter(
            competition=comp,
            participant=user,
            status=AttemptStatus.IN_PROGRESS
        ).first()

        completed_attempt = ExamAttempt.objects.filter(
            competition=comp,
            participant=user,
            status__in=[AttemptStatus.SUBMITTED, AttemptStatus.AUTO_SUBMITTED]
        ).first()

        can_start = comp.status == CompetitionStatus.OPEN and not active_attempt and not completed_attempt

        data.append({
            'id': str(comp.id),
            'title': comp.title,
            'status': comp.status,
            'status_display': comp.get_status_display(),
            'active_attempt_id': str(active_attempt.id) if active_attempt else None,
            'is_completed': bool(completed_attempt),
            'can_start': can_start
        })

    from django.http import JsonResponse
    return JsonResponse({'status': 'success', 'competitions': data})

