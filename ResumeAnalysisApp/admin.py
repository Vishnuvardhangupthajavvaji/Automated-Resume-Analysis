from django.contrib import admin

from .models import Application, Feedback, Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "created_at", "created_by")
    search_fields = ("title", "company", "required_skills")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "applicant", "score", "submitted_at")
    list_filter = ("job",)
    search_fields = ("applicant__username", "job__title")


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("rating", "user", "created_at")
    list_filter = ("rating",)
