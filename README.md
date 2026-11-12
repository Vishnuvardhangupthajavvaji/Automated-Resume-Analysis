# Automated Resume Analysis

A Django-based job portal that connects job applicants with recruiters.
Applicants can browse job openings, upload PDF or DOCX resumes, and
receive a skill-match score. Recruiters can request access, wait for
administrator approval, post jobs after approval, and review
applications submitted to their own jobs.

## Features

### Applicant

- Register and log in.
- Browse and search available jobs.
- Apply for a job by uploading a PDF or DOCX resume.
- View submitted applications.
- Receive a skill-match score based on the job's required skills and
  extracted resume text.
- Submit feedback.

### Recruiter

- Register with the **Recruiter** account type.
- Wait for an administrator to review the recruiter-access request.
- Post jobs after approval.
- View applications for jobs they personally posted.
- Reapply for recruiter access if a previous request was rejected.

### Administrator

- Access the recruiter-request dashboard.
- Approve or reject pending recruiter requests.
- View applications across the platform.
- Manage platform data through Django Admin, subject to the configured
  permissions.

## Recruiter approval workflow

Recruiter status is represented using Django's built-in Groups. The
registration dropdown is a form-only field; it is not stored as a
separate database column.

---

Group membership Meaning Access

---

No recruiter-status Applicant Browse and apply for
group jobs

`Pending_Recruiter` Request awaiting review Applicant access while
waiting

`Recruiter` Approved recruiter Post jobs and view
applications for own
jobs

`Rejected_Recruiter` Request rejected Applicant access; can
reapply

---

Administrator actions: - **Approve:** remove the pending status and add
the user to `Recruiter`. - **Reject:** remove the pending status and add
the user to `Rejected_Recruiter`. - **Reapply:** remove the rejected
status and add the user to `Pending_Recruiter`.

A user should have no more than one of these three recruiter-status
groups at a time. The application uses group membership as the source of
truth; no custom `UserProfile` model is required for this workflow.

## Technology

- Python
- Django
- Django Templates
- JavaScript
- MySQL
- PDF text extraction through `pdfminer.six`
- DOCX text extraction through `docx2txt`

Check `requirements.txt` for the exact dependency versions used by this
checkout.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Vishnuvardhangupthajavvaji/Automated-Resume-Analysis.git
cd Automated-Resume-Analysis
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
python -m venv venv
venv\Scripts\activate
```

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure the database

For MySQL, configure the environment variables expected by the project's
settings:

```text
DB_ENGINE=mysql
DB_NAME=<database_name>
DB_HOST=<database_host>
DB_PORT=<database_port>
DB_USER=<database_user>
DB_PASSWORD=<database_password>
```

Use a dedicated database and least-privilege database account. Do not
commit passwords, database dumps, or production credentials. Confirm the
exact environment-variable handling in `ResumeAnalysis/settings.py`
before deployment.

### 5. Apply migrations

For a new local installation:

```bash
python manage.py migrate
```

The recruiter workflow uses Django's built-in authentication Groups and
does not require a custom recruiter-status model or a new migration,
provided the built-in authentication migrations have been applied.

If this is an existing database, back it up before applying migrations.
Do not run migrations against an unrelated or legacy database.

### 6. Create an administrator account

```bash
python manage.py createsuperuser
```

Use this account to access Django Admin and the custom recruiter-request
dashboard. The account must have `is_staff=True` to access the custom
dashboard.

### 7. Run the development server

```bash
python manage.py runserver
```

Open:

- Application: `http://127.0.0.1:8000/`
- Django Admin: `http://127.0.0.1:8000/admin/`
- Recruiter requests: `http://127.0.0.1:8000/staff/recruiters/` (staff
  users only)

## Resume matching

The application accepts PDF and DOCX resumes. It extracts text and
compares that text with the comma-separated required skills saved for a
job.

The score is calculated as:

```text
(number of required skills found in resume text / total required skills) * 100
```
