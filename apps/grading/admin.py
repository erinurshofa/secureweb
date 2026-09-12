from django.contrib import admin
from .models import AttemptGrade, EssayEvaluation


@admin.register(AttemptGrade)
class AttemptGradeAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'mcq_score', 'essay_score', 'total_score', 'is_finalized', 'graded_at')
    list_filter = ('is_finalized', 'attempt__competition')
    search_fields = ('attempt__participant__username',)
    readonly_fields = ('graded_at',)


@admin.register(EssayEvaluation)
class EssayEvaluationAdmin(admin.ModelAdmin):
    list_display = ('attempt_answer', 'judge', 'score_awarded', 'evaluated_at')
    list_filter = ('judge',)
    search_fields = ('attempt_answer__attempt__participant__username', 'judge__username')
    readonly_fields = ('evaluated_at',)
