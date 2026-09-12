from django.urls import path
from . import views

urlpatterns = [
    # Dashboard & Overview
    path('', views.management_dashboard, name='manage_dashboard'),
    path('api/live-stats/', views.api_live_stats, name='manage_api_live_stats'),
    path('competitions/<uuid:competition_id>/status/', views.competition_status_update, name='manage_competition_status'),

    # Question Bank & Editor
    path('competitions/quick-create/', views.competition_quick_create, name='manage_competition_quick_create'),
    path('questions/', views.questions_manage, name='manage_questions'),
    path('questions/create/', views.question_create_or_edit, name='manage_question_create'),
    path('questions/batch/', views.questions_batch_create, name='manage_questions_batch'),
    path('questions/<uuid:question_id>/edit/', views.question_create_or_edit, name='manage_question_edit'),
    path('questions/<uuid:question_id>/delete/', views.question_delete, name='manage_question_delete'),

    # Real-time Exam Attempts Monitor & Leaderboard
    path('attempts/', views.attempts_monitor, name='manage_attempts'),
    path('ranking/', views.ranking_leaderboard, name='manage_ranking'),
    path('api/attempts/', views.api_attempts_list, name='manage_api_attempts'),
    path('attempts/<uuid:attempt_id>/force-submit/', views.attempt_force_submit, name='manage_attempt_force_submit'),

    # Essay Grading for Judges
    path('grading/', views.grading_dashboard, name='manage_grading'),
    path('grading/<uuid:answer_id>/submit/', views.grade_essay_submit, name='manage_grade_essay_submit'),
    path('grading/<uuid:answer_id>/history/', views.api_answer_history, name='manage_api_answer_history'),
    path('grading/<uuid:answer_id>/dispute/', views.api_toggle_dispute, name='manage_api_toggle_dispute'),

    # Participants Management
    path('participants/', views.participants_manage, name='manage_participants'),
    path('participants/<uuid:user_id>/reset-password/', views.participant_reset_password, name='manage_participant_reset_password'),

    # Security & Audit Logs
    path('audit/', views.audit_logs_view, name='manage_audit'),

    # Export Rekap Nilai CSV
    path('export/scores/', views.export_scores_csv, name='manage_export_scores_csv'),

    # Disaster Recovery, Backup & Restore (Exclusive for Lead Developer)
    path('system/backup/', views.system_backup_view, name='manage_system_backup'),
    path('system/backup/create/', views.system_backup_create, name='manage_system_backup_create'),
    path('system/backup/upload/', views.system_backup_upload, name='manage_system_backup_upload'),
    path('system/backup/<str:filename>/download/', views.system_backup_download, name='manage_system_backup_download'),
    path('system/backup/<str:filename>/restore/', views.system_backup_restore, name='manage_system_backup_restore'),
    path('system/backup/<str:filename>/delete/', views.system_backup_delete, name='manage_system_backup_delete'),
]
