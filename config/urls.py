"""
URL configuration for Secure Web Quiz Platform.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from accounts.views import login_view, logout_view
from competitions.views import dashboard_view, start_attempt_view, competition_status_api
from attempts.views import (
    exam_arena_view,
    autosave_api_view,
    log_exam_integrity_event_view,
    submit_attempt_view,
    result_view,
    download_attachment_view
)

# Administrative Mission Control Branding
admin.site.site_header = "SECUREQUIZ • Pusat Komando Admin & Juri"
admin.site.site_title = "Admin Portal — Secure Web Quiz Platform"
admin.site.index_title = "Manajemen Babak Kompetisi & Keamanan Siber"

urlpatterns = [
    # Modern Custom Admin & Management Workspace
    path('manage/', include('management.urls')),

    # Standard Django Admin
    path('admin/', admin.site.urls),

    # Authentication
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # Participant Dashboard (Bisa diakses lewat / maupun /dashboard/)
    path('', dashboard_view, name='dashboard'),
    path('dashboard/', dashboard_view, name='dashboard_alt'),
    path('competitions/<uuid:competition_id>/start/', start_attempt_view, name='start_attempt'),

    # Exam Arena & Workspace
    path('attempts/<uuid:attempt_id>/arena/', exam_arena_view, name='exam_arena'),
    path('attempts/<uuid:attempt_id>/submit/', submit_attempt_view, name='submit_attempt'),
    path('attempts/<uuid:attempt_id>/result/', result_view, name='result_view'),

    # Realtime Autosave & Status API Endpoints
    path('api/attempts/<uuid:attempt_id>/save/', autosave_api_view, name='autosave_api'),
    path('api/attempts/<uuid:attempt_id>/integrity-event/', log_exam_integrity_event_view, name='exam_integrity_event_api'),
    path('api/competitions/status/', competition_status_api, name='api_competitions_status'),

    # Secure Attachment Download Sandbox
    path('attachments/<uuid:attachment_id>/download/', download_attachment_view, name='download_attachment'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
