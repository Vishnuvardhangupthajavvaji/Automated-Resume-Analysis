from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Application, Feedback, Job
import zipfile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    user_type = forms.ChoiceField(
        choices=[
            ("applicant", "Job Applicant"),
            ("recruiter", "Recruiter"),
        ],
        label="Register as",
        initial="applicant",
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()

        return user


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ("title", "company", "description", "required_skills", "salary")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "required_skills": forms.TextInput(
                attrs={"placeholder": "Python, Django, SQL"}
            ),
        }

    def clean_required_skills(self):
        skills = [
            item.strip()
            for item in self.cleaned_data["required_skills"].split(",")
            if item.strip()
        ]
        if not skills:
            raise forms.ValidationError("Enter at least one skill.")
        return ", ".join(dict.fromkeys(skills))


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ("resume",)

    def clean_resume(self):
        resume = self.cleaned_data["resume"]
        if resume.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Resume files must be 5 MB or smaller.")
        extension = resume.name.rsplit(".", 1)[-1].lower()
        try:
            if extension == "pdf" and resume.read(5) != b"%PDF-":
                raise forms.ValidationError("The PDF file signature is invalid.")
            if extension == "docx":
                with zipfile.ZipFile(resume) as archive:
                    if "[Content_Types].xml" not in archive.namelist():
                        raise forms.ValidationError("The DOCX file is invalid.")
        except zipfile.BadZipFile:
            raise forms.ValidationError("The DOCX file is invalid.")
        finally:
            resume.seek(0)
        return resume


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ("message", "rating")
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}
