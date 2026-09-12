import json
import uuid
import hashlib
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Avg, Q, Max, Sum
from django.utils import timezone
from django.utils.text import slugify
from django.http import HttpResponseForbidden, JsonResponse

from accounts.models import User, UserRole
from competitions.models import Competition, CompetitionStatus, ParticipantEnrollment
from questions.models import Question, QuestionType, QuestionStatus, QuestionOption, QuestionAttachment
from attempts.models import ExamAttempt, AttemptStatus, AttemptAnswer, AnswerHistoryLog
from grading.models import AttemptGrade, EssayEvaluation
from audit.models import SecurityAuditLog, AuditEventType
from services.scoring_service import ScoringService


def staff_or_admin_required(view_func):
    """Izinkan Admin, Panitia, dan Dewan Juri untuk mengakses area yang relevan."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'status': 'error', 'message': 'Unauthenticated'}, status=401)
            return redirect('login')
        allowed_roles = [
            UserRole.SUPER_ADMIN,
            UserRole.ORGANIZER,
            UserRole.JUDGE,
            UserRole.AUTHOR,
            UserRole.REVIEWER
        ]
        if not (request.user.is_staff or request.user.is_superuser or request.user.role in allowed_roles):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)
            messages.error(request, "Akses ditolak. Halaman Manajemen khusus untuk Panitia, Juri, dan Admin.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def organizer_or_admin_required(view_func):
    """Ketat: HANYA untuk Super Admin dan Organizer (Panitia). Role JUDGE dilarang demi Separation of Duties."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'status': 'error', 'message': 'Unauthenticated'}, status=401)
            return redirect('login')
        allowed_roles = [
            UserRole.SUPER_ADMIN,
            UserRole.ORGANIZER
        ]
        if not (request.user.is_superuser or request.user.role in allowed_roles):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'status': 'error', 'message': 'Forbidden: Aksi ini khusus untuk Panitia/Super Admin (Separation of Duties).'}, status=403)
            messages.error(request, "Akses ditolak. Fitur ini memerlukan wewenang Panitia / Super Admin (Separation of Duties).")
            return redirect('manage_grading' if request.user.role == UserRole.JUDGE else 'manage_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@staff_or_admin_required
def management_dashboard(request):
    """Pusat Komando & Ringkasan Utama Admin/Panitia."""
    # Jika role murni JUDGE, arahkan langsung ke Arena Penilaian Juri
    if request.user.role == UserRole.JUDGE and not (request.user.is_superuser or request.user.role in [UserRole.SUPER_ADMIN, UserRole.ORGANIZER]):
        return redirect('manage_grading')
    total_participants = User.objects.filter(role=UserRole.PARTICIPANT).count()
    total_competitions = Competition.objects.count()
    active_attempts = ExamAttempt.objects.filter(status=AttemptStatus.IN_PROGRESS).count()
    completed_attempts = ExamAttempt.objects.filter(status__in=[AttemptStatus.SUBMITTED, AttemptStatus.AUTO_SUBMITTED]).count()
    
    avg_score = AttemptGrade.objects.aggregate(avg=Avg('total_score'))['avg'] or 0.0

    competitions = Competition.objects.annotate(
        questions_count=Count('questions', distinct=True),
        participants_count=Count('enrollments', distinct=True)
    ).order_by('-created_at')

    recent_attempts = ExamAttempt.objects.select_related('participant', 'competition').prefetch_related('grade').order_by('-start_time')[:8]
    recent_audits = SecurityAuditLog.objects.select_related('user').order_by('-created_at')[:8]

    context = {
        'total_participants': total_participants,
        'total_competitions': total_competitions,
        'active_attempts': active_attempts,
        'completed_attempts': completed_attempts,
        'avg_score': round(float(avg_score), 2),
        'competitions': competitions,
        'recent_attempts': recent_attempts,
        'recent_audits': recent_audits,
        'active_tab': 'overview'
    }
    return render(request, 'management/dashboard.html', context)


@staff_or_admin_required
def api_live_stats(request):
    """API Real-time untuk Ringkasan Eksekutif & KPI Dashboard."""
    total_participants = User.objects.filter(role=UserRole.PARTICIPANT).count()
    active_attempts = ExamAttempt.objects.filter(status=AttemptStatus.IN_PROGRESS).count()
    completed_attempts = ExamAttempt.objects.filter(status__in=[AttemptStatus.SUBMITTED, AttemptStatus.AUTO_SUBMITTED]).count()
    avg_score = AttemptGrade.objects.aggregate(avg=Avg('total_score'))['avg'] or 0.0

    recent_attempts_qs = ExamAttempt.objects.select_related('participant', 'competition').prefetch_related('grade').order_by('-start_time')[:8]
    recent_attempts_data = []
    for att in recent_attempts_qs:
        recent_attempts_data.append({
            'id': str(att.id),
            'username': att.participant.username,
            'attempt_number': att.attempt_number,
            'status': att.status,
            'status_display': att.get_status_display(),
            'start_time': att.start_time.strftime('%H:%M:%S'),
            'score': str(att.grade.total_score) if hasattr(att, 'grade') and att.grade else '-'
        })

    recent_audits_qs = SecurityAuditLog.objects.select_related('user').order_by('-created_at')[:8]
    recent_audits_data = []
    for log in recent_audits_qs:
        recent_audits_data.append({
            'id': str(log.id),
            'username': log.user.username if log.user else 'Anonim',
            'event_type_display': log.get_event_type_display(),
            'ip_address': log.ip_address or '-',
            'time': log.created_at.strftime('%H:%M:%S')
        })

    return JsonResponse({
        'status': 'success',
        'kpi': {
            'total_participants': total_participants,
            'active_attempts': active_attempts,
            'completed_attempts': completed_attempts,
            'avg_score': round(float(avg_score), 2)
        },
        'recent_attempts': recent_attempts_data,
        'recent_audits': recent_audits_data
    })


@organizer_or_admin_required
def competition_status_update(request, competition_id):
    """Update status kompetisi secara instan."""
    if request.method == 'POST':
        competition = get_object_or_404(Competition, id=competition_id)
        new_status = request.POST.get('status')
        if new_status in CompetitionStatus.values:
            competition.status = new_status
            competition.save(update_fields=['status', 'updated_at'])
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '') or request.POST.get('ajax') == '1':
                return JsonResponse({
                    'status': 'success',
                    'competition_id': str(competition.id),
                    'new_status': competition.status,
                    'new_status_display': competition.get_status_display(),
                    'message': f"Status kompetisi '{competition.title}' diubah ke {competition.get_status_display()}."
                })
            messages.success(request, f"Status kompetisi '{competition.title}' berhasil diubah ke {competition.get_status_display()}.")
    return redirect('manage_dashboard')


@organizer_or_admin_required
def competition_quick_create(request):
    """
    Endpoint AJAX untuk membuat kompetisi baru secara instan tanpa reload halaman,
    memungkinkan panitia langsung memilih babak kompetisi yang baru dibuat.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Hanya metode POST yang diizinkan.'}, status=405)

    title = request.POST.get('title', '').strip()
    if not title:
        return JsonResponse({'status': 'error', 'message': 'Judul kompetisi wajib diisi.'}, status=400)

    try:
        duration_minutes = int(request.POST.get('duration_minutes', 90))
        if duration_minutes <= 0:
            duration_minutes = 90
    except (ValueError, TypeError):
        duration_minutes = 90

    status = request.POST.get('status', CompetitionStatus.OPEN)
    if status not in CompetitionStatus.values:
        status = CompetitionStatus.OPEN

    description = request.POST.get('description', '').strip()
    
    try:
        max_attempts = int(request.POST.get('max_attempts', 1))
        if max_attempts <= 0:
            max_attempts = 1
    except (ValueError, TypeError):
        max_attempts = 1

    # Default jadwal kompetisi: mulai sekarang, berakhir 7 hari ke depan
    now = timezone.now()
    start_time = now
    end_time = now + timezone.timedelta(days=7)

    # Generate unique slug
    base_slug = slugify(title) or f"comp-{uuid.uuid4().hex[:8]}"
    slug = base_slug
    counter = 1
    while Competition.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    with transaction.atomic():
        competition = Competition.objects.create(
            title=title,
            slug=slug,
            description=description,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            status=status,
            max_attempts=max_attempts,
            created_by=request.user
        )

    return JsonResponse({
        'status': 'success',
        'message': f"Kompetisi '{competition.title}' berhasil dibuat.",
        'competition': {
            'id': str(competition.id),
            'title': competition.title,
            'status': competition.status,
            'status_display': competition.get_status_display(),
            'duration_minutes': competition.duration_minutes
        }
    })


@organizer_or_admin_required
def questions_manage(request):
    """Manajemen Bank Soal & Opsi Jawaban Modern (Mendukung ratusan hingga ribuan soal)."""
    comp_id = request.GET.get('competition_id')
    q_type = request.GET.get('type')
    search_q = request.GET.get('q', '').strip()
    
    questions = Question.objects.select_related('competition', 'created_by').prefetch_related('options', 'attachments')
    
    if comp_id:
        questions = questions.filter(competition_id=comp_id)
    if q_type:
        questions = questions.filter(type=q_type)
    if search_q:
        questions = questions.filter(
            Q(title__icontains=search_q) |
            Q(body__icontains=search_q) |
            Q(rubric_guidelines__icontains=search_q)
        )
        
    questions = questions.order_by('sequence')
    competitions = Competition.objects.all()
    total_points = questions.aggregate(Sum('points'))['points__sum'] or 0

    context = {
        'questions': questions,
        'competitions': competitions,
        'total_points': total_points,
        'selected_comp': comp_id,
        'selected_type': q_type,
        'search_q': search_q,
        'active_tab': 'questions'
    }
    return render(request, 'management/questions.html', context)


@organizer_or_admin_required
def question_create_or_edit(request, question_id=None):
    """Form Pembuatan / Edit Soal Modern."""
    question = get_object_or_404(Question, id=question_id) if question_id else None
    competitions = Competition.objects.all()

    if request.method == 'POST':
        comp_id = request.POST.get('competition')
        title = request.POST.get('title', '').strip()
        body = request.POST.get('body', '').strip()
        rubric_guidelines = request.POST.get('rubric_guidelines', '').strip()
        q_type = request.POST.get('type', QuestionType.MCQ)
        points = request.POST.get('points', '10.00')
        sequence = request.POST.get('sequence', '1')
        status = request.POST.get('status', QuestionStatus.APPROVED)

        competition = get_object_or_404(Competition, id=comp_id)

        with transaction.atomic():
            if question:
                question.competition = competition
                question.title = title
                question.body = body
                question.rubric_guidelines = rubric_guidelines
                question.type = q_type
                question.points = Decimal(points)
                question.sequence = int(sequence)
                question.status = status
                question.save()
            else:
                question = Question.objects.create(
                    competition=competition,
                    title=title,
                    body=body,
                    rubric_guidelines=rubric_guidelines,
                    type=q_type,
                    points=Decimal(points),
                    sequence=int(sequence),
                    status=status,
                    created_by=request.user
                )

            # Process MCQ Options jika tipe MCQ
            if q_type == QuestionType.MCQ:
                option_texts = request.POST.getlist('option_text[]')
                correct_indices = request.POST.getlist('is_correct[]')
                
                # Hapus opsi lama jika edit
                question.options.all().delete()
                
                for idx, text in enumerate(option_texts):
                    clean_text = text.strip()
                    if clean_text:
                        is_correct = str(idx) in correct_indices
                        QuestionOption.objects.create(
                            question=question,
                            option_text=clean_text,
                            is_correct=is_correct,
                            order=idx + 1
                        )

            # Process File Attachment jika ada upload
            uploaded_file = request.FILES.get('attachment_file')
            if uploaded_file:
                content = uploaded_file.read()
                file_hash = hashlib.sha256(content).hexdigest()
                uploaded_file.seek(0)
                QuestionAttachment.objects.create(
                    question=question,
                    file=uploaded_file,
                    display_filename=uploaded_file.name,
                    file_size=uploaded_file.size,
                    sha256_hash=file_hash
                )

        messages.success(request, f"Soal '{question.title}' berhasil disimpan.")
        return redirect('manage_questions')

    context = {
        'question': question,
        'competitions': competitions,
        'active_tab': 'questions'
    }
    return render(request, 'management/question_form.html', context)


@organizer_or_admin_required
def question_delete(request, question_id):
    """Hapus Soal."""
    if request.method == 'POST':
        question = get_object_or_404(Question, id=question_id)
        question.delete()
        messages.success(request, "Soal berhasil dihapus.")
    return redirect('manage_questions')


@organizer_or_admin_required
def questions_batch_create(request):
    """
    Halaman dan endpoint untuk pembuatan pertanyaan dalam jumlah banyak sekaligus (batch creation).
    Mendukung input visual multi-baris interaktif maupun impor format JSON/AI secara langsung.
    """
    competitions = Competition.objects.all().order_by('-created_at')

    if request.method == 'POST':
        comp_id = request.POST.get('competition_id')
        if not comp_id:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'status': 'error', 'message': 'Pilih babak kompetisi terlebih dahulu.'}, status=400)
            messages.error(request, "Pilih babak kompetisi terlebih dahulu.")
            return redirect('manage_questions_batch')

        competition = get_object_or_404(Competition, id=comp_id)
        batch_json_raw = request.POST.get('batch_data', '').strip()

        if not batch_json_raw:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'status': 'error', 'message': 'Data soal batch tidak boleh kosong.'}, status=400)
            messages.error(request, "Data soal batch tidak boleh kosong.")
            return redirect('manage_questions_batch')

        try:
            items = json.loads(batch_json_raw)
            if not isinstance(items, list) or len(items) == 0:
                raise ValueError("Format data harus berupa array daftar soal.")
        except Exception as e:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'status': 'error', 'message': f'Format data batch tidak valid: {str(e)}'}, status=400)
            messages.error(request, f"Format data batch tidak valid: {str(e)}")
            return redirect('manage_questions_batch')

        created_questions = []
        with transaction.atomic():
            # Urutan sequence awal
            max_seq = Question.objects.filter(competition=competition).aggregate(Max('sequence'))['sequence__max'] or 0

            for idx, item in enumerate(items):
                title = str(item.get('title', '')).strip()
                body = str(item.get('body', '')).strip()
                if not title:
                    title = f"Soal Tantangan #{max_seq + 1}"
                if not body:
                    body = title

                q_type = QuestionType.ESSAY if item.get('type') == 'ESSAY' else QuestionType.MCQ
                
                try:
                    points = Decimal(str(item.get('points', 10.0)))
                except Exception:
                    points = Decimal('10.00')

                rubric = str(item.get('rubric_guidelines', item.get('rubric', ''))).strip()

                try:
                    seq = int(item.get('sequence'))
                except (ValueError, TypeError):
                    max_seq += 1
                    seq = max_seq

                question = Question.objects.create(
                    competition=competition,
                    title=title,
                    body=body,
                    rubric_guidelines=rubric,
                    type=q_type,
                    points=points,
                    sequence=seq,
                    status=QuestionStatus.APPROVED,
                    created_by=request.user
                )

                # Opsi pilihan ganda jika MCQ
                if q_type == QuestionType.MCQ:
                    raw_options = item.get('options', [])
                    if isinstance(raw_options, list) and len(raw_options) > 0:
                        has_correct = False
                        for opt_idx, opt in enumerate(raw_options):
                            if isinstance(opt, dict):
                                opt_text = str(opt.get('option_text', opt.get('text', ''))).strip()
                                is_correct = bool(opt.get('is_correct', False))
                            else:
                                opt_text = str(opt).strip()
                                is_correct = (opt_idx == 0)

                            if is_correct:
                                has_correct = True

                            if opt_text:
                                QuestionOption.objects.create(
                                    question=question,
                                    option_text=opt_text,
                                    is_correct=is_correct,
                                    order=opt_idx + 1
                                )
                        # Jika belum ada opsi yang ditandai benar, default opsi pertama
                        if not has_correct:
                            first_opt = question.options.first()
                            if first_opt:
                                first_opt.is_correct = True
                                first_opt.save(update_fields=['is_correct'])

                created_questions.append(question)

            # Audit logging
            ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
            SecurityAuditLog.objects.create(
                user=request.user,
                event_type=AuditEventType.QUESTION_CREATE,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                path=request.path
            )

        success_msg = f"Berhasil membuat {len(created_questions)} soal sekaligus untuk kompetisi '{competition.title}'."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({
                'status': 'success',
                'message': success_msg,
                'count': len(created_questions),
                'competition_id': str(competition.id),
                'redirect_url': f"/manage/questions/?competition_id={competition.id}"
            })

        messages.success(request, success_msg)
        return redirect(f"/manage/questions/?competition_id={competition.id}")

    selected_comp = request.GET.get('competition_id', '')
    context = {
        'competitions': competitions,
        'selected_comp': selected_comp,
        'active_tab': 'questions'
    }
    return render(request, 'management/questions_batch.html', context)


@staff_or_admin_required
def attempts_monitor(request):
    """
    Live Monitoring Sesi Ujian Peserta.
    Dapat diakses oleh Panitia, Super Admin, dan Dewan Juri.
    Mendukung pencarian nama/institusi, filter kompetisi, filter status,
    dan pengurutan berdasarkan poin paling banyak (skor tertinggi).
    """
    competitions = Competition.objects.all().order_by('-created_at')
    
    comp_id = request.GET.get('competition_id', '').strip()
    status = request.GET.get('status', '').strip()
    search_q = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort_by', 'score') # default: poin paling banyak (skor tertinggi)

    attempts = ExamAttempt.objects.select_related('participant', 'competition').prefetch_related('grade', 'answers')

    if comp_id:
        attempts = attempts.filter(competition_id=comp_id)
    if status:
        attempts = attempts.filter(status=status)
    if search_q:
        attempts = attempts.filter(
            Q(participant__username__icontains=search_q) |
            Q(participant__first_name__icontains=search_q) |
            Q(participant__institution__icontains=search_q) |
            Q(competition__title__icontains=search_q)
        )

    if sort_by == 'start_time':
        attempts = attempts.order_by('-start_time')
    else: # default 'score' -> poin paling banyak
        attempts = attempts.order_by('-grade__total_score', 'submitted_at', '-start_time')
    
    now = timezone.now()
    active_count = ExamAttempt.objects.filter(status=AttemptStatus.IN_PROGRESS).count()

    is_judge = (request.user.role == UserRole.JUDGE and not (request.user.is_superuser or request.user.role in [UserRole.SUPER_ADMIN, UserRole.ORGANIZER]))

    context = {
        'attempts': attempts,
        'competitions': competitions,
        'selected_comp': comp_id,
        'selected_status': status,
        'search_q': search_q,
        'sort_by': sort_by,
        'now': now,
        'active_count': active_count,
        'is_judge': is_judge,
        'active_tab': 'attempts'
    }
    return render(request, 'management/attempts.html', context)


@staff_or_admin_required
def ranking_leaderboard(request):
    """
    Pusat Papan Peringkat & Leaderboard Juara Ujian.
    Dapat diakses oleh Panitia, Super Admin, dan Dewan Juri untuk memantau peringkat,
    peserta dengan poin tertinggi, breakdown nilai MCQ vs Essay, dan durasi pengerjaan.
    """
    competitions = Competition.objects.all().order_by('-created_at')
    comp_id = request.GET.get('competition_id', '')
    search_q = request.GET.get('q', '').strip()

    attempts = ExamAttempt.objects.select_related('participant', 'competition').prefetch_related('grade').filter(
        status__in=[AttemptStatus.SUBMITTED, AttemptStatus.AUTO_SUBMITTED]
    )

    if comp_id:
        attempts = attempts.filter(competition_id=comp_id)

    if search_q:
        attempts = attempts.filter(
            Q(participant__username__icontains=search_q) |
            Q(participant__institution__icontains=search_q) |
            Q(competition__title__icontains=search_q)
        )

    # Urutkan berdasarkan total skor tertinggi, lalu waktu submit tercepat (tie-breaker)
    attempts = attempts.order_by('-grade__total_score', 'submitted_at')

    ranked_list = []
    for rank, att in enumerate(attempts, 1):
        grade = getattr(att, 'grade', None)
        duration_str = "-"
        if att.start_time and att.submitted_at:
            delta = att.submitted_at - att.start_time
            m, s = divmod(int(delta.total_seconds()), 60)
            h, m = divmod(m, 60)
            duration_str = f"{h}j {m}m {s}d" if h else f"{m}m {s}d"

        ranked_list.append({
            'rank': rank,
            'attempt': att,
            'grade': grade,
            'duration_str': duration_str,
            'is_top3': rank <= 3
        })

    top_3 = ranked_list[:3]

    context = {
        'ranked_list': ranked_list,
        'top_3': top_3,
        'competitions': competitions,
        'selected_comp': comp_id,
        'search_q': search_q,
        'total_participants_ranked': len(ranked_list),
        'active_tab': 'ranking'
    }
    return render(request, 'management/ranking.html', context)


@staff_or_admin_required
def api_attempts_list(request):
    """API Real-time untuk Live Monitoring Sesi Ujian (mendukung filter & pencarian)."""
    comp_id = request.GET.get('competition_id', '').strip()
    status = request.GET.get('status', '').strip()
    search_q = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort_by', 'score')

    attempts_qs = ExamAttempt.objects.select_related('participant', 'competition').prefetch_related('grade', 'answers')

    if comp_id:
        attempts_qs = attempts_qs.filter(competition_id=comp_id)
    if status:
        attempts_qs = attempts_qs.filter(status=status)
    if search_q:
        attempts_qs = attempts_qs.filter(
            Q(participant__username__icontains=search_q) |
            Q(participant__first_name__icontains=search_q) |
            Q(participant__institution__icontains=search_q) |
            Q(competition__title__icontains=search_q)
        )

    if sort_by == 'start_time':
        attempts_qs = attempts_qs.order_by('-start_time')
    else: # default 'score'
        attempts_qs = attempts_qs.order_by('-grade__total_score', 'submitted_at', '-start_time')

    now = timezone.now()
    data = []
    for idx, att in enumerate(attempts_qs, 1):
        remaining_seconds = max(0, int((att.server_deadline - now).total_seconds())) if att.status == AttemptStatus.IN_PROGRESS else 0
        rem_m, rem_s = divmod(remaining_seconds, 60)
        rem_h, rem_m = divmod(rem_m, 60)
        remaining_formatted = f"{rem_h:02d}:{rem_m:02d}:{rem_s:02d}"

        data.append({
            'rank': idx,
            'id': str(att.id),
            'username': att.participant.username,
            'institution': att.participant.institution or 'Independen',
            'competition_title': att.competition.title,
            'attempt_number': att.attempt_number,
            'status': att.status,
            'status_display': att.get_status_display(),
            'start_time': att.start_time.strftime('%d %b, %H:%M:%S'),
            'server_deadline': att.server_deadline.strftime('%d %b, %H:%M:%S'),
            'remaining_time': remaining_formatted,
            'answers_count': att.answers.count(),
            'score': str(att.grade.total_score) if hasattr(att, 'grade') and att.grade else '-'
        })

    return JsonResponse({
        'status': 'success',
        'active_count': ExamAttempt.objects.filter(status=AttemptStatus.IN_PROGRESS).count(),
        'attempts': data
    })


@organizer_or_admin_required
def attempt_force_submit(request, attempt_id):
    """Paksa Selesai (Force Submit) Sesi Ujian (Khusus Panitia / Super Admin)."""
    if request.method == 'POST':
        attempt = get_object_or_404(ExamAttempt, id=attempt_id)
        if attempt.status == AttemptStatus.IN_PROGRESS:
            with transaction.atomic():
                attempt.status = AttemptStatus.AUTO_SUBMITTED
                attempt.submitted_at = timezone.now()
                attempt.save(update_fields=['status', 'submitted_at'])
                ScoringService.evaluate_and_score_attempt(attempt.id)
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '') or request.POST.get('ajax') == '1':
                return JsonResponse({
                    'status': 'success',
                    'attempt_id': str(attempt.id),
                    'new_status': attempt.status,
                    'new_status_display': attempt.get_status_display(),
                    'message': f"Sesi ujian {attempt.participant.username} berhasil dikumpulkan paksa."
                })
            messages.success(request, f"Sesi ujian peserta {attempt.participant.username} berhasil dikumpulkan paksa.")
    return redirect('manage_attempts')


@staff_or_admin_required
def grading_dashboard(request):
    """
    Panel Penilaian Jawaban Essay untuk Juri:
    - Blind Review Mode (Anonimisasi Identitas Peserta)
    - Multi-Judge Consensus Scoring & Discrepancy Detection
    - Tab-Blur Audit & Indikator Integritas
    - Filter Personal (Belum Saya Nilai, Sengketa/Eskalasi, Selisih Nilai Tinggi)
    """
    status_filter = request.GET.get('status', 'all')  # all, pending, my_pending, graded, disputed, discrepancy
    comp_id = request.GET.get('competition_id')
    question_id = request.GET.get('question_id')
    search_q = request.GET.get('q', '').strip()
    
    # Blind Review Mode: default AKTIF (1) untuk menjamin objektivitas
    blind_mode = request.GET.get('blind', '1') != '0'

    # HANYA ambil jawaban dari attempt yang SUDAH SELESAI (SUBMITTED / AUTO_SUBMITTED)
    base_qs = AttemptAnswer.objects.filter(
        question__type=QuestionType.ESSAY,
        attempt__status__in=[AttemptStatus.SUBMITTED, AttemptStatus.AUTO_SUBMITTED]
    ).select_related(
        'attempt__participant',
        'attempt__competition',
        'question'
    ).prefetch_related(
        'essay_evaluations__judge',
        'question__attachments'
    )

    # Filter Babak Kompetisi
    if comp_id:
        base_qs = base_qs.filter(attempt__competition_id=comp_id)

    # Filter Soal Spesifik
    if question_id:
        base_qs = base_qs.filter(question_id=question_id)

    # Filter Pencarian (Username / Institusi / Title / Pseudonym)
    if search_q:
        base_qs = base_qs.filter(
            Q(attempt__participant__username__icontains=search_q) |
            Q(attempt__participant__institution__icontains=search_q) |
            Q(question__title__icontains=search_q)
        )

    # Urutkan berdasarkan urutan soal dan waktu penyerahan
    all_answers_list = list(base_qs.order_by('question__sequence', 'attempt__submitted_at'))
    
    # Cache tab blur violations count per participant attempt
    # Untuk menghemat query, ambil semua event tab_blur yang relevan
    participant_ids = [a.attempt.participant_id for a in all_answers_list]
    blur_events = SecurityAuditLog.objects.filter(
        user_id__in=participant_ids,
        event_type=AuditEventType.SUSPICIOUS_ACTIVITY
    ).values('user_id').annotate(count=Count('id'))
    blur_dict = {item['user_id']: item['count'] for item in blur_events}

    # Anotasi objek answer dengan metadata cerdas
    for a in all_answers_list:
        # 1. Blind Review Pseudonym: misal Kandidat #B82C4A
        pseudo_hash = hashlib.md5(f"blind_salt_{a.attempt.participant.id}".encode()).hexdigest()[:6].upper()
        a.pseudonym = f"Kandidat #{pseudo_hash}"

        # 2. Multi-Judge Discrepancy Check (Selisih Nilai >= 30%)
        disc = ScoringService.check_score_discrepancy(a)
        a.has_discrepancy = disc['has_discrepancy']
        a.discrepancy_delta = disc['delta']
        a.discrepancy_threshold = disc['threshold']
        a.eval_count = disc['eval_count']

        # 3. Multi-Judge Aggregated Mean Score
        a.aggregated_score = ScoringService.calculate_answer_score(a)

        # 4. Evaluasi Juri yang sedang login
        a.my_evaluation = next((ev for ev in a.essay_evaluations.all() if ev.judge_id == request.user.id), None)

        # 5. Status Eskalasi / Flagged for Discussion
        a.is_disputed = any(ev.is_flagged_for_review for ev in a.essay_evaluations.all())
        a.dispute_reason = next((ev.dispute_reason for ev in a.essay_evaluations.all() if ev.is_flagged_for_review and ev.dispute_reason), "")

        # 6. Tab Blur Violation Count
        a.tab_blur_count = blur_dict.get(a.attempt.participant_id, 0)

    # Metrik KPI
    total_count = len(all_answers_list)
    graded_count = sum(1 for a in all_answers_list if a.essay_evaluations.exists())
    pending_count = total_count - graded_count
    my_pending_count = sum(1 for a in all_answers_list if a.my_evaluation is None)
    disputed_count = sum(1 for a in all_answers_list if a.is_disputed)
    discrepancy_count = sum(1 for a in all_answers_list if a.has_discrepancy)
    progress_percent = round((graded_count / total_count * 100), 1) if total_count > 0 else 100.0

    # Filter Logis
    if status_filter == 'pending':
        filtered_answers = [a for a in all_answers_list if not a.essay_evaluations.exists()]
    elif status_filter == 'my_pending':
        filtered_answers = [a for a in all_answers_list if a.my_evaluation is None]
    elif status_filter == 'graded':
        filtered_answers = [a for a in all_answers_list if a.essay_evaluations.exists()]
    elif status_filter == 'disputed':
        filtered_answers = [a for a in all_answers_list if a.is_disputed]
    elif status_filter == 'discrepancy':
        filtered_answers = [a for a in all_answers_list if a.has_discrepancy]
    else:
        filtered_answers = all_answers_list

    # Dropdown Options
    competitions = Competition.objects.all()
    essay_questions = Question.objects.filter(type=QuestionType.ESSAY).order_by('competition', 'sequence')

    context = {
        'essay_answers': filtered_answers,
        'status_filter': status_filter,
        'blind_mode': blind_mode,
        'selected_comp': comp_id,
        'selected_question': question_id,
        'search_q': search_q,
        'competitions': competitions,
        'essay_questions': essay_questions,
        'total_count': total_count,
        'graded_count': graded_count,
        'pending_count': pending_count,
        'my_pending_count': my_pending_count,
        'disputed_count': disputed_count,
        'discrepancy_count': discrepancy_count,
        'progress_percent': progress_percent,
        'active_tab': 'grading'
    }
    return render(request, 'management/grading.html', context)


@staff_or_admin_required
def grade_essay_submit(request, answer_id):
    """Submit Skor, Catatan Publik, Catatan Rahasia Juri, dan Flag Eskalasi."""
    if request.method == 'POST':
        answer = get_object_or_404(AttemptAnswer, id=answer_id)
        score_val = request.POST.get('score', '0')
        feedback = request.POST.get('feedback', '').strip()
        internal_notes = request.POST.get('internal_notes', '').strip()
        is_flagged = request.POST.get('is_flagged') in ('1', 'true', 'True')
        dispute_reason = request.POST.get('dispute_reason', '').strip()

        try:
            score = Decimal(score_val)
        except Exception:
            score = Decimal('0.00')

        if score < 0 or score > answer.question.points:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '') or request.POST.get('ajax') == '1':
                return JsonResponse({'status': 'error', 'message': f"Nilai harus 0 s/d {answer.question.points} poin."}, status=400)
            messages.error(request, f"Nilai harus berada di rentang 0 hingga {answer.question.points} poin.")
            return redirect('manage_grading')

        with transaction.atomic():
            evaluation = ScoringService.grade_essay(
                answer_id=str(answer.id),
                judge=request.user,
                score=score,
                feedback=feedback,
                internal_notes=internal_notes,
                is_flagged=is_flagged,
                dispute_reason=dispute_reason
            )

        # Cek status konsensus dan disparitas terbaru
        answer.refresh_from_db()
        disc = ScoringService.check_score_discrepancy(answer)
        aggregated_score = ScoringService.calculate_answer_score(answer)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '') or request.POST.get('ajax') == '1':
            return JsonResponse({
                'status': 'success',
                'answer_id': str(answer.id),
                'score_awarded': str(score),
                'aggregated_score': str(aggregated_score),
                'feedback': feedback,
                'internal_notes': internal_notes,
                'is_flagged': is_flagged,
                'dispute_reason': dispute_reason,
                'has_discrepancy': disc['has_discrepancy'],
                'discrepancy_delta': str(disc['delta']),
                'eval_count': disc['eval_count'],
                'judge_name': request.user.username,
                'message': f"Nilai essay ({score}/{answer.question.points} Poin) dan catatan juri berhasil disimpan secara atomik."
            })

        messages.success(request, f"Nilai essay ({score}/{answer.question.points} Poin) berhasil disimpan.")
    return redirect('manage_grading')


@staff_or_admin_required
def api_answer_history(request, answer_id):
    """Mengembalikan rekam jejak autosave & analitik cadence pengetikan dari AnswerHistoryLog."""
    answer = get_object_or_404(AttemptAnswer, id=answer_id)
    history_logs = AnswerHistoryLog.objects.filter(attempt_answer=answer).order_by('revision')
    
    logs_data = []
    prev_time = None
    prev_len = 0
    sudden_paste_alerts = 0

    for log in history_logs:
        current_len = len(log.essay_text)
        delta_chars = current_len - prev_len
        time_delta_sec = int((log.saved_at - prev_time).total_seconds()) if prev_time else 0
        
        # Deteksi lonjakan pengetikan instan (> 250 karakter dalam waktu <= 10 detik)
        is_suspicious_paste = (delta_chars >= 250 and (time_delta_sec <= 10 or prev_time is None))
        if is_suspicious_paste:
            sudden_paste_alerts += 1

        logs_data.append({
            'revision': log.revision,
            'saved_at': log.saved_at.strftime('%H:%M:%S'),
            'saved_at_full': log.saved_at.strftime('%d %b %Y, %H:%M:%S'),
            'char_length': current_len,
            'delta_chars': delta_chars,
            'time_delta_sec': time_delta_sec,
            'ip_address': log.ip_address or '-',
            'is_suspicious_paste': is_suspicious_paste,
            'snippet': (log.essay_text[:140] + '...') if len(log.essay_text) > 140 else log.essay_text
        })
        prev_time = log.saved_at
        prev_len = current_len

    # Tab blur violation count
    tab_blur_count = SecurityAuditLog.objects.filter(
        user=answer.attempt.participant,
        event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
        created_at__gte=answer.attempt.started_at
    ).count()

    return JsonResponse({
        'status': 'success',
        'answer_id': str(answer.id),
        'total_revisions': history_logs.count(),
        'sudden_paste_alerts': sudden_paste_alerts,
        'tab_blur_count': tab_blur_count,
        'final_length': len(answer.essay_text),
        'logs': logs_data
    })


@staff_or_admin_required
def api_toggle_dispute(request, answer_id):
    """Menandai atau membatalkan eskalasi review juri kepala."""
    if request.method == 'POST':
        answer = get_object_or_404(AttemptAnswer, id=answer_id)
        is_flagged = request.POST.get('is_flagged') in ('1', 'true', 'True')
        reason = request.POST.get('dispute_reason', '').strip()

        eval_obj = EssayEvaluation.objects.filter(attempt_answer=answer, judge=request.user).first()
        if not eval_obj:
            eval_obj = EssayEvaluation.objects.create(
                attempt_answer=answer,
                judge=request.user,
                score_awarded=Decimal('0.00'),
                feedback='',
                internal_notes='',
                is_flagged_for_review=is_flagged,
                dispute_reason=reason
            )
        else:
            eval_obj.is_flagged_for_review = is_flagged
            eval_obj.dispute_reason = reason
            eval_obj.save(update_fields=['is_flagged_for_review', 'dispute_reason', 'evaluated_at'])

        any_disputed = any(ev.is_flagged_for_review for ev in answer.essay_evaluations.all())

        return JsonResponse({
            'status': 'success',
            'answer_id': str(answer.id),
            'is_flagged': is_flagged,
            'any_disputed': any_disputed,
            'dispute_reason': reason,
            'message': "Status eskalasi berhasil ditandai." if is_flagged else "Tanda eskalasi dibatalkan."
        })
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


@organizer_or_admin_required
def participants_manage(request):
    """Manajemen Peserta & Reset Password (Khusus Panitia / Super Admin)."""
    participants = User.objects.filter(role=UserRole.PARTICIPANT).annotate(
        attempts_count=Count('exam_attempts')
    ).order_by('username')

    context = {
        'participants': participants,
        'active_tab': 'participants'
    }
    return render(request, 'management/participants.html', context)


@organizer_or_admin_required
def participant_reset_password(request, user_id):
    """Reset password peserta ke password default 'admin123'."""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.set_password('admin123')
        user.save(update_fields=['password'])
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '') or request.POST.get('ajax') == '1':
            return JsonResponse({
                'status': 'success',
                'user_id': str(user.id),
                'username': user.username,
                'message': f"Password untuk peserta '{user.username}' berhasil direset menjadi: admin123"
            })
        messages.success(request, f"Password untuk peserta '{user.username}' berhasil direset menjadi: admin123")
    return redirect('manage_participants')


@staff_or_admin_required
def audit_logs_view(request):
    """Audit Trail & Security Logs Viewer."""
    event_type = request.GET.get('event_type')
    search_q = request.GET.get('q')

    logs = SecurityAuditLog.objects.select_related('user').order_by('-created_at')

    if event_type:
        logs = logs.filter(event_type=event_type)
    if search_q:
        logs = logs.filter(Q(user__username__icontains=search_q) | Q(ip_address__icontains=search_q) | Q(path__icontains=search_q))

    logs = logs[:150]

    context = {
        'logs': logs,
        'event_types': AuditEventType.choices,
        'selected_event': event_type,
        'search_q': search_q,
        'active_tab': 'audit'
    }
    return render(request, 'management/audit.html', context)


@staff_or_admin_required
def export_scores_csv(request):
    """Export Rekap Nilai Peserta & Leaderboard ke format CSV."""
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="rekap_nilai_lomba_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    response.write('\ufeff'.encode('utf8'))  # BOM untuk kompatibilitas Microsoft Excel

    writer = csv.writer(response)
    writer.writerow([
        'Peringkat',
        'Username',
        'Nama Lengkap',
        'Institusi / Tim',
        'Kompetisi',
        'Sesi #',
        'Status Sesi',
        'Skor Pilihan Ganda',
        'Skor Essay',
        'Total Skor Akhir',
        'Waktu Mulai',
        'Waktu Selesai'
    ])

    attempts = ExamAttempt.objects.select_related('participant', 'competition').prefetch_related('grade').filter(
        status__in=[AttemptStatus.SUBMITTED, AttemptStatus.AUTO_SUBMITTED]
    ).order_by('-grade__total_score', 'submitted_at')

    for idx, att in enumerate(attempts, 1):
        grade = getattr(att, 'grade', None)
        mcq_score = str(grade.mcq_score) if grade else '0.00'
        essay_score = str(grade.essay_score) if grade else '0.00'
        total_score = str(grade.total_score) if grade else '0.00'

        writer.writerow([
            idx,
            att.participant.username,
            att.participant.get_full_name() or att.participant.username,
            att.participant.institution or 'Independen',
            att.competition.title,
            att.attempt_number,
            att.get_status_display(),
            mcq_score,
            essay_score,
            total_score,
            att.start_time.strftime('%Y-%m-%d %H:%M:%S') if att.start_time else '-',
            att.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if att.submitted_at else '-'
        ])

    return response

