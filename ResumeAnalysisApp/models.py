from django.conf import settings
from django.core.validators import (
    FileExtensionValidator,
    MaxLengthValidator,
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models


class Job(models.Model):
    title = models.CharField(max_length=150)
    company = models.CharField(max_length=150)
    description = models.TextField()
    required_skills = models.CharField(
        max_length=500, help_text="Comma-separated skills"
    )
    salary = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="posted_jobs",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} — {self.company}"

    @property
    def skills_list(self):
        return [
            skill.strip() for skill in self.required_skills.split(",") if skill.strip()
        ]


class Application(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    resume = models.FileField(
        upload_to="resumes/%Y/%m/",
        validators=[FileExtensionValidator(["pdf", "docx"])],
    )
    parsed_data = models.TextField(blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    matched_skills = models.CharField(max_length=500, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["job", "applicant"], name="unique_job_applicant"
            )
        ]
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.applicant} / {self.job}"


class Feedback(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    message = models.TextField(max_length=1000)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Feedback ({self.rating}/5) by {self.user or 'Anonymous'}"
