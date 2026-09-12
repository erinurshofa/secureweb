from django.contrib import admin
from .models import Competition, ParticipantEnrollment


class ParticipantEnrollmentInline(admin.TabularInline):
    model = ParticipantEnrollment
    extra = 1
    raw_id_fields = ('participant',)


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'start_time', 'end_time', 'duration_minutes', 'max_attempts', 'created_at')
    list_filter = ('status', 'start_time', 'end_time')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ParticipantEnrollmentInline]


@admin.register(ParticipantEnrollment)
class ParticipantEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('participant', 'competition', 'enrolled_at', 'is_disqualified')
    list_filter = ('competition', 'is_disqualified')
    search_fields = ('participant__username', 'participant__email', 'competition__title')
    raw_id_fields = ('participant', 'competition')
