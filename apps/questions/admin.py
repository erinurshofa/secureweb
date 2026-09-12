from django.contrib import admin
from .models import Question, QuestionOption, QuestionAttachment, AttachmentDownloadToken


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4


class QuestionAttachmentInline(admin.TabularInline):
    model = QuestionAttachment
    extra = 1
    readonly_fields = ('download_count', 'created_at')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'title', 'competition', 'type', 'points', 'status', 'version')
    list_filter = ('competition', 'type', 'status')
    search_fields = ('title', 'body')
    inlines = [QuestionOptionInline, QuestionAttachmentInline]


@admin.register(QuestionAttachment)
class QuestionAttachmentAdmin(admin.ModelAdmin):
    list_display = ('display_filename', 'question', 'mime_type', 'file_size', 'sha256_hash', 'download_count', 'created_at')
    list_filter = ('question__competition',)
    search_fields = ('display_filename', 'original_filename', 'sha256_hash')
    readonly_fields = ('download_count', 'created_at')


@admin.register(AttachmentDownloadToken)
class AttachmentDownloadTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'user', 'attachment', 'expires_at', 'is_used', 'created_at')
    list_filter = ('is_used', 'expires_at')
    search_fields = ('token', 'user__username')
    readonly_fields = ('token', 'created_at')
