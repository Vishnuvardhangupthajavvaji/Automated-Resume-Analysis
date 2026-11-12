import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group, User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import ApplicationForm, FeedbackForm, JobForm, SignUpForm
from .models import Application, Feedback, Job
from .services import calculate_match, extract_resume_text

PENDING_RECRUITER = "Pending_Recruiter"
APPROVED_RECRUITER = "Recruiter"
REJECTED_RECRUITER = "Rejected_Recruiter"


def set_recruiter_status(user, status):
    """Ensure a user belongs to at most one recruiter-status group."""
    group_names = [
        PENDING_RECRUITER,
        APPROVED_RECRUITER,
        REJECTED_RECRUITER,
    ]

    user.groups.remove(*Group.objects.filter(name__in=group_names))

    if status:
        group, _ = Group.objects.get_or_create(name=status)
        user.groups.add(group)


def is_recruiter(user):
    return user.groups.filter(name=APPROVED_RECRUITER).exists()


def deny_access(request, message):
    messages.error(request, message)
    return redirect("home")


@require_GET
def home(request):
    return render(request, "index.html", {"job_count": Job.objects.count()})


@require_http_methods(["GET", "POST"])
def signup(request):
    if request.user.is_authenticated:
        return redirect("job_list")

    form = SignUpForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()

        if form.cleaned_data["user_type"] == "recruiter":
            set_recruiter_status(user, PENDING_RECRUITER)
            messages.success(
                request,
                "Your account is ready. Your recruiter request is awaiting admin approval.",
            )
        else:
            messages.success(
                request, "Your applicant account is ready. You can now apply for jobs."
            )

        login(request, user)
        return redirect("job_list")

    return render(request, "Signup.html", {"form": form})


@login_required
@require_POST
def reapply_recruiter(request):
    if not request.user.groups.filter(name=REJECTED_RECRUITER).exists():
        messages.info(
            request, "You do not have a rejected recruiter request to reapply for."
        )
        return redirect("job_list")

    set_recruiter_status(request.user, PENDING_RECRUITER)

    messages.success(
        request,
        "Your recruiter request has been submitted again and is awaiting admin approval.",
    )
    return redirect("job_list")


@login_required
@require_http_methods(["GET", "POST"])
def manage_recruiters(request):
    if not request.user.is_staff:
        return deny_access(
            request, "You do not have permission to access recruiter management."
        )

    pending_group, _ = Group.objects.get_or_create(name=PENDING_RECRUITER)

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        action = request.POST.get("action")

        target_user = get_object_or_404(
            User,
            pk=user_id,
            is_staff=False,
            is_superuser=False,
        )

        if not target_user.groups.filter(name=PENDING_RECRUITER).exists():
            messages.warning(
                request, "This user no longer has a pending recruiter request."
            )
            return redirect("manage_recruiters")

        if action == "approve":
            set_recruiter_status(target_user, APPROVED_RECRUITER)
            messages.success(
                request, f"{target_user.username} has been approved as a recruiter."
            )

        elif action == "reject":
            set_recruiter_status(target_user, REJECTED_RECRUITER)
            messages.success(
                request, f"{target_user.username} has been rejected as a recruiter."
            )

        else:
            messages.error(request, "Invalid action.")

        return redirect("manage_recruiters")

    pending_users = User.objects.filter(
        groups=pending_group,
        is_staff=False,
        is_superuser=False,
    ).order_by("date_joined")

    return render(
        request,
        "admin_users.html",
        {"pending_users": pending_users},
    )


@require_GET
def job_list(request):
    query = request.GET.get("q", "").strip()
    jobs = Job.objects.all()

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query)
            | Q(company__icontains=query)
            | Q(required_skills__icontains=query)
        )

    return render(
        request,
        "UserScreen.html",
        {"jobs": jobs, "query": query},
    )


@login_required
@require_http_methods(["GET", "POST"])
def apply_to_job(request, job_id):
    if is_recruiter(request.user):
        messages.error(
            request, "Recruiters cannot apply for jobs using a recruiter account."
        )
        return redirect("job_list")

    job = get_object_or_404(Job, pk=job_id)

    if Application.objects.filter(
        job=job,
        applicant=request.user,
    ).exists():
        messages.info(request, "You have already applied to this role.")
        return redirect("job_list")

    form = ApplicationForm(
        request.POST or None,
        request.FILES or None,
    )

    if request.method == "POST" and form.is_valid():
        application = form.save(commit=False)
        application.job = job
        application.applicant = request.user

        try:
            application.save()

            resume_text = extract_resume_text(application.resume.path)
            score, matched = calculate_match(
                job.skills_list,
                resume_text,
            )

            application.parsed_data = json.dumps(
                {"text": resume_text},
                ensure_ascii=False,
            )
            application.score = score
            application.matched_skills = ", ".join(matched)

            application.save(
                update_fields=[
                    "parsed_data",
                    "score",
                    "matched_skills",
                ]
            )

        except Exception:
            application.resume.delete(save=False)
            application.delete()

            form.add_error(
                "resume",
                "We could not read this file. Please upload a valid PDF or DOCX resume.",
            )

        else:
            messages.success(
                request,
                "Application submitted. Match score: {}%.".format(score),
            )
            return redirect("my_applications")

    return render(
        request,
        "UploadResume.html",
        {"form": form, "job": job},
    )


@login_required
@require_GET
def my_applications(request):
    applications = Application.objects.filter(applicant=request.user).select_related(
        "job"
    )

    return render(
        request,
        "applications.html",
        {"applications": applications},
    )


@login_required
@require_http_methods(["GET", "POST"])
def post_job(request):
    if not (request.user.is_staff or is_recruiter(request.user)):
        return deny_access(request, "Only approved recruiters can post jobs.")

    form = JobForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        job = form.save(commit=False)
        job.created_by = request.user
        job.save()

        messages.success(request, "Job posted successfully.")
        return redirect("admin_applications")

    return render(request, "PostJobs.html", {"form": form})


@login_required
@require_GET
def admin_applications(request):
    if request.user.is_staff:
        applications = Application.objects.select_related(
            "job",
            "applicant",
        ).all()

    elif is_recruiter(request.user):
        applications = Application.objects.filter(
            job__created_by=request.user
        ).select_related("job", "applicant")

    else:
        return deny_access(
            request,
            "Only administrators and approved recruiters can view applications.",
        )

    return render(
        request,
        "ViewFeedback.html",
        {"applications": applications},
    )


@require_http_methods(["GET", "POST"])
def feedback(request):
    form = FeedbackForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.user = request.user if request.user.is_authenticated else None
        item.save()

        messages.success(request, "Thank you for your feedback.")
        return redirect("feedback")

    return render(request, "Feedback.html", {"form": form})


@login_required
@permission_required("ResumeAnalysisApp.view_feedback", raise_exception=True)
@require_GET
def view_feedback(request):
    feedback_items = Feedback.objects.select_related("user").all()

    return render(
        request,
        "feedback_list.html",
        {"feedback_items": feedback_items},
    )
