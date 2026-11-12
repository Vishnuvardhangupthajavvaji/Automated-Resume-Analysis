from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="UserLogin.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/<int:job_id>/apply/", views.apply_to_job, name="apply_to_job"),
    path("applications/", views.my_applications, name="my_applications"),
    path("feedback/", views.feedback, name="feedback"),
    path("staff/jobs/new/", views.post_job, name="post_job"),
    path("staff/applications/", views.admin_applications, name="admin_applications"),
    path("staff/feedback/", views.view_feedback, name="view_feedback"),
    path("staff/recruiters/", views.manage_recruiters, name="manage_recruiters"),
    path("recruiter/reapply/", views.reapply_recruiter, name="reapply_recruiter"),
]
