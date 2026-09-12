import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib import messages

from .models import ExamAttempt, AttemptStatus
from questions.models import Question, QuestionAttachment
from grading.models import AttemptGrade
from services.exam_service import ExamService
from services.scoring_service import ScoringService
from services.attachment_service import AttachmentService


@login_required(login_url='login')
def exam_arena_view(request, attempt_id):
    attempt = get_object_or_404(
        ExamAttempt.objects.select_related('competition'),
        id=attempt_id
    )

    # Validasi kepemilikan attempt
    if attempt.participant != request.user and not request.user.is_staff:
        raise PermissionDenied("Anda tidak memiliki izin mengakses attempt ini.")

    # Jika sudah submitted / expired, arahkan ke hasil
    if attempt.status != AttemptStatus.IN_PROGRESS:
        return redirect('result_view', attempt_id=attempt.id)

    if attempt.is_expired():
        # Otomatis submit jika expired
        ExamService.submit_attempt(str(attempt.id), request.user, is_auto=True)
        ScoringService.score_mcq_attempt(attempt)
        return redirect('result_view', attempt_id=attempt.id)

    questions = Question.objects.filter(
        competition=attempt.competition
    ).prefetch_related('options', 'attachments').order_by('sequence')

    return render(request, 'attempts/exam_arena.html', {
        'attempt': attempt,
        'questions': questions
    })


@login_required(login_url='login')
@csrf_protect
def autosave_api_view(request, attempt_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Hanya metode POST yang diizinkan.'}, status=405)

    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        selected_option_id = data.get('selected_option_id')
        essay_text = data.get('essay_text')
        is_flagged = data.get('is_flagged')
        
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))

        answer = ExamService.save_answer(
            attempt_id=str(attempt_id),
            user=request.user,
            question_id=str(question_id),
            selected_option_id=selected_option_id,
            essay_text=essay_text,
            is_flagged=is_flagged,
            ip_address=ip_address
        )

        return JsonResponse({
            'status': 'success',
            'saved_at': answer.saved_at.isoformat(),
            'revision': answer.revision_count
        })
    except (ValidationError, PermissionDenied) as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=403)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': 'Gagal menyimpan jawaban.'}, status=500)


@login_required(login_url='login')
@csrf_protect
def log_exam_integrity_event_view(request, attempt_id):
    """Mencatat indikasi pelanggaran integritas ujian (pindah tab, window blur) ke SecurityAuditLog."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)

    try:
        data = json.loads(request.body)
        event_name = data.get('event', 'TAB_SWITCH')
        details = data.get('details', {})

        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        SecurityAuditLog.objects.create(
            user=request.user,
            event_type=AuditEventType.TOKEN_ANOMALY,
            ip_address=ip_address,
            user_agent=user_agent,
            path=request.path,
            details={
                'attempt_id': str(attempt_id),
                'alert': 'INTEGRITAS_UJIAN_WARNING',
                'event_name': event_name,
                'client_info': details,
                'logged_at': timezone.now().isoformat()
            }
        )
        return JsonResponse({'status': 'logged'})
    except Exception:
        return JsonResponse({'status': 'ignored'}, status=200)


@login_required(login_url='login')
def submit_attempt_view(request, attempt_id):
    if request.method != 'POST':
        return redirect('dashboard')

    ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
    
    try:
        attempt = ExamService.submit_attempt(
            attempt_id=str(attempt_id),
            user=request.user,
            is_auto=False,
            ip_address=ip_address
        )
        # Kalkulasi auto-scoring pilihan ganda
        ScoringService.score_mcq_attempt(attempt)
        return redirect('result_view', attempt_id=attempt.id)
    except Exception as e:
        messages.error(request, str(e))
        return redirect('dashboard')


@login_required(login_url='login')
def result_view(request, attempt_id):
    attempt = get_object_or_404(
        ExamAttempt.objects.select_related('competition'),
        id=attempt_id
    )

    if attempt.participant != request.user and not request.user.is_staff:
        raise PermissionDenied("Anda tidak berhak melihat hasil ini.")

    grade = AttemptGrade.objects.filter(attempt=attempt).first()

    return render(request, 'attempts/result.html', {
        'attempt': attempt,
        'grade': grade
    })


@login_required(login_url='login')
def download_attachment_view(request, attachment_id):
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
    
    try:
        # Generate token berbatas waktu
        token = AttachmentService.generate_download_token(
            user=request.user,
            attachment_id=str(attachment_id),
            ip_address=ip_address
        )
        
        # Validasi dan konsumsi token untuk serving file
        attachment = AttachmentService.consume_download_token(
            token_str=str(token.token),
            user=request.user,
            ip_address=ip_address
        )
        
        if not attachment.file:
            raise Http404("File tantangan tidak ditemukan di server.")
            
        return FileResponse(
            attachment.file.open('rb'),
            as_attachment=True,
            filename=attachment.original_filename
        )
    except (PermissionDenied, ValidationError) as e:
        messages.error(request, str(e))
        return redirect('dashboard')
