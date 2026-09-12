from django.contrib import admin
from .models import ExamAttempt, AttemptAnswer, AnswerHistoryLog


class AttemptAnswerInline(admin.TabularInline):
    model = AttemptAnswer
    extra = 0
    readonly_fields = ('question', 'selected_option', 'essay_text', 'saved_at', 'revision_count', 'is_flagged_for_review')
    can_delete = False


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ('participant', 'competition', 'attempt_number', 'status', 'start_time', 'server_deadline', 'submitted_at', 'ip_address')
    list_filter = ('status', 'competition')
    search_fields = ('participant__username', 'ip_address')
    readonly_fields = ('start_time', 'server_deadline', 'submitted_at', 'ip_address', 'user_agent', 'created_at', 'updated_at')
    inlines = [AttemptAnswerInline]


@admin.register(AttemptAnswer)
class AttemptAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_option', 'saved_at', 'revision_count', 'is_flagged_for_review')
    list_filter = ('is_flagged_for_review', 'attempt__competition')
    search_fields = ('attempt__participant__username', 'question__title')
    readonly_fields = ('saved_at', 'revision_count')


@admin.register(AnswerHistoryLog)
class AnswerHistoryLogAdmin(admin.ModelAdmin):
    list_display = ('attempt_answer', 'revision', 'ip_address', 'saved_at')
    readonly_fields = ('attempt_answer', 'selected_option_id', 'essay_text', 'saved_at', 'ip_address', 'revision')
