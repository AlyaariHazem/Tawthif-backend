# Tawthif Backend — توظيف

> **Tawthif** (Arabic: توظيف, meaning "Employment") is a full-featured **Job Portal REST API** built with Django & Django REST Framework. It connects job seekers with employers, handles applications end-to-end, supports AI-powered job summaries, and more.

---

## Table of Contents

- [Overview](#overview)
- [Architecture Diagram](#architecture-diagram)
- [Tech Stack](#tech-stack)
- [Directory Structure](#directory-structure)
- [Features](#features)
- [Data Model Diagram](#data-model-diagram)
- [Authentication Flow](#authentication-flow)
- [API Endpoints Overview](#api-endpoints-overview)
- [Installation & Setup](#installation--setup)
- [Environment Variables](#environment-variables)
- [Running the Project](#running-the-project)
- [API Documentation](#api-documentation)

---

## Overview

Tawthif is a comprehensive backend for a job portal platform. It provides:

- JWT-based authentication and role-based access (job seeker / employer / admin)
- Job posting management with categories, filters, and AI-generated summaries (Google Gemini)
- Company profiles with reviews and follower system
- End-to-end job application tracking with status history, interviews, and in-app messaging
- Custom application forms with dynamic questions
- Media uploads via Cloudinary (logos, resumes, documents)
- Full OpenAPI/Swagger documentation

---

## Architecture Diagram

```mermaid
graph TD
    Client["🌐 Client\n(Web / Mobile App)"]

    subgraph API["Django REST Framework API"]
        Auth["🔐 Auth Module\n(accounts)"]
        Jobs["💼 Jobs Module\n(jobs)"]
        Companies["🏢 Companies Module\n(companies)"]
        Applications["📄 Applications Module\n(applications)"]
        Forms["📋 Job Forms Module\n(job_forms)"]
        Core["⚙️ Core Utilities\n(core)"]
    end

    subgraph External["External Services"]
        DB[(PostgreSQL\nDatabase)]
        Cloudinary["☁️ Cloudinary\nMedia Storage"]
        Gemini["🤖 Google Gemini AI\nJob Summaries"]
    end

    Client -->|JWT Token| Auth
    Client --> Jobs
    Client --> Companies
    Client --> Applications
    Client --> Forms

    Auth --> DB
    Jobs --> DB
    Jobs --> Gemini
    Companies --> DB
    Applications --> DB
    Forms --> DB

    Auth --> Cloudinary
    Applications --> Cloudinary
    Companies --> Cloudinary
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.8+ |
| **Framework** | Django 5.2 + Django REST Framework |
| **Database** | PostgreSQL (hosted on Railway) |
| **Authentication** | JWT via `djangorestframework-simplejwt` |
| **Media Storage** | Cloudinary via `django-cloudinary-storage` |
| **AI Integration** | Google Gemini (`google-generativeai`) |
| **API Docs** | drf-spectacular (Swagger / ReDoc) |
| **Filtering** | `django-filter` |
| **CORS** | `django-cors-headers` |
| **Static Files** | WhiteNoise |
| **Production Server** | Gunicorn |
| **Image Processing** | Pillow |

---

## Directory Structure

```
Tawthif-backend/
├── job_portal_backend/          # Django project configuration
│   ├── settings.py              # Settings (DB, JWT, CORS, Cloudinary, etc.)
│   ├── urls.py                  # Root URL router
│   ├── wsgi.py                  # WSGI entry point
│   └── asgi.py                  # ASGI entry point
│
├── accounts/                    # User management & profiles
│   ├── models.py                # User, JobSeekerProfile, EmployerProfile, ProfileDocument
│   ├── views.py                 # Registration, login, profile endpoints
│   ├── serializers.py
│   └── urls.py
│
├── jobs/                        # Job postings
│   ├── models.py                # Job, JobCategory, JobBookmark, JobAlert
│   ├── views.py                 # Job CRUD, filtering, recommendations
│   ├── ai_utils.py              # Gemini AI summary generation
│   ├── signals.py
│   └── urls.py
│
├── companies/                   # Company profiles & reviews
│   ├── models.py                # Company, CompanyReview, CompanyFollower
│   ├── views.py                 # Company CRUD, reviews, stats
│   └── urls.py
│
├── applications/                # Job applications & interviews
│   ├── models.py                # JobApplication, Interview, ApplicationMessage, StatusHistory
│   ├── views.py                 # Application flow, interviews, messaging
│   └── urls.py
│
├── job_forms/                   # Custom application forms
│   ├── models.py                # JobForm, JobFormQuestion
│   ├── views.py                 # Form ViewSet
│   └── urls.py
│
├── core/                        # Shared utilities
│   └── validators.py            # File/image validators
│
├── manage.py                    # Django CLI
├── requirements.txt             # Python dependencies
├── start.sh                     # Production startup script (gunicorn)
└── create_superuser_script.py   # Utility to create default admin user
```

---

## Features

### 👤 User Accounts
- Custom user model with three roles: **job seeker**, **employer**, **admin**
- Phone-based verification with one-time codes
- Password reset via verification code
- Separate enriched profiles for job seekers (resume, skills, salary expectations) and employers (company info, logo)
- Profile document management (certificates, awards, projects) with visibility controls

### 💼 Jobs
- Full CRUD for job postings (employers)
- Rich filtering: city, category, job type, experience level, salary range, keywords
- Bookmarks and personal job alerts
- AI-generated job summaries using **Google Gemini**
- Personalized job recommendations based on seeker profile
- Similar jobs discovery

### 🏢 Companies
- Company profiles with logo and cover image (Cloudinary)
- Company size / industry classification
- Review & rating system (1–5 stars, pros/cons)
- Follow/unfollow system
- Employer dashboard statistics

### 📄 Applications
- Multiple application methods: platform form, custom form, template file, external link, or email
- Full application status lifecycle: `pending → reviewed → shortlisted → interview_scheduled → accepted / rejected`
- Status change history tracking
- In-app messaging between applicant and employer
- Interview scheduling (phone, video, in-person, technical, HR)
- Document view tracking

### 📋 Custom Forms
- Employers can create custom application forms with dynamic questions
- Supports: text, textarea, number, select, checkbox, file upload, date fields

---

## Data Model Diagram

```mermaid
erDiagram
    User {
        int id
        string username
        string email
        string user_type
        string phone
        bool is_verified
    }

    JobSeekerProfile {
        int id
        string resume
        string skills
        string experience_level
        int expected_salary_min
        int expected_salary_max
    }

    EmployerProfile {
        int id
        string company_name
        string company_logo
        string industry
    }

    ProfileDocument {
        int id
        string document_type
        string title
        string file
        string visibility
    }

    Company {
        int id
        string name
        string slug
        string industry
        string size
        bool is_verified
    }

    Job {
        int id
        string title
        string slug
        string job_type
        string experience_level
        string city
        int salary_min
        int salary_max
        bool is_active
        string ai_summary
    }

    JobCategory {
        int id
        string name
        string slug
    }

    JobApplication {
        int id
        string status
        string cover_letter
        int rating
        bool is_viewed
    }

    Interview {
        int id
        string interview_type
        datetime scheduled_date
        string status
    }

    ApplicationMessage {
        int id
        string message
        bool is_read
    }

    CompanyReview {
        int id
        int rating
        string review_text
        string pros
        string cons
    }

    JobForm {
        int id
        string name
        bool is_active
    }

    JobFormQuestion {
        int id
        string label
        string question_type
        bool required
    }

    User ||--o| JobSeekerProfile : "has"
    User ||--o| EmployerProfile : "has"
    JobSeekerProfile ||--o{ ProfileDocument : "owns"
    User ||--o{ Company : "owns"
    Company ||--o{ Job : "posts"
    Job }o--|| JobCategory : "belongs to"
    User ||--o{ JobApplication : "submits"
    Job ||--o{ JobApplication : "receives"
    JobApplication ||--o{ Interview : "schedules"
    JobApplication ||--o{ ApplicationMessage : "has"
    Company ||--o{ CompanyReview : "receives"
    Company ||--o{ JobForm : "creates"
    JobForm ||--o{ JobFormQuestion : "contains"
```

---

## Authentication Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as Django API
    participant DB as PostgreSQL

    C->>API: POST /api/accounts/register/
    API->>DB: Create User (unverified)
    API-->>C: 201 Created + verification code sent

    C->>API: POST /api/accounts/verify-phone/
    API->>DB: Mark user as verified
    API-->>C: 200 OK

    C->>API: POST /api/accounts/login/
    API->>DB: Validate credentials
    API-->>C: { access_token, refresh_token }

    Note over C,API: Use access_token in Authorization header

    C->>API: GET /api/jobs/ (Authorization: Bearer <token>)
    API->>API: Validate JWT
    API->>DB: Fetch jobs
    API-->>C: 200 OK + job list

    C->>API: POST /api/token/refresh/
    API-->>C: { new_access_token }
```

---

## Application Lifecycle Flow

```mermaid
stateDiagram-v2
    [*] --> pending : Applicant submits application
    pending --> reviewed : Employer views it
    reviewed --> shortlisted : Employer shortlists
    reviewed --> rejected : Employer rejects
    shortlisted --> interview_scheduled : Interview set up
    interview_scheduled --> interview_completed : Interview held
    interview_completed --> accepted : Offer extended
    interview_completed --> rejected : Not selected
    pending --> withdrawn : Applicant withdraws
    reviewed --> withdrawn : Applicant withdraws
    shortlisted --> withdrawn : Applicant withdraws
    accepted --> [*]
    rejected --> [*]
    withdrawn --> [*]
```

---

## API Endpoints Overview

### 🔐 Authentication — `/api/accounts/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register/` | Register new user |
| POST | `/verify-phone/` | Verify phone with code |
| POST | `/login/` | Login and get JWT tokens |
| POST | `/logout/` | Logout |
| POST | `/change-password/` | Change password |
| POST | `/password-reset/request/` | Request password reset |
| POST | `/password-reset/confirm/` | Confirm reset with code |
| GET/PATCH | `/profile/` | View or update user profile |
| PATCH | `/profile/job-seeker/` | Update job seeker profile |
| PATCH | `/profile/employer/` | Update employer profile |
| GET/POST | `/profile/documents/` | List or upload documents |
| GET | `/users/` | List all users (admin) |

### 💼 Jobs — `/api/jobs/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List jobs (filterable, searchable, paginated) |
| POST | `/create/` | Create job posting (employer) |
| GET | `/my-jobs/` | My posted jobs (employer) |
| GET | `/{slug}/` | Job detail |
| PATCH | `/{slug}/update/` | Update job |
| DELETE | `/{slug}/delete/` | Delete job |
| GET | `/categories/` | List categories |
| GET/POST | `/bookmarks/` | Bookmarked jobs |
| POST | `/{job_id}/bookmark/` | Toggle bookmark |
| GET | `/recommended/` | Recommended jobs |
| GET | `/{job_id}/similar/` | Similar jobs |
| GET/POST | `/alerts/` | Job alerts |

### 🏢 Companies — `/api/companies/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List companies |
| POST | `/create/` | Create company |
| GET | `/{slug}/` | Company detail + jobs |
| GET | `/{company_id}/reviews/` | Company reviews |
| POST | `/{company_id}/reviews/create/` | Add review |
| POST | `/{company_id}/follow/` | Follow / unfollow |
| GET | `/followed/` | Followed companies |
| GET | `/top/` | Top companies |
| GET | `/employer-dashboard-stats/` | Employer dashboard stats |

### 📄 Applications — `/api/applications/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/apply/` | Submit application |
| GET | `/my-applications/` | Applicant's applications |
| GET | `/job-applications/` | Applications to employer's jobs |
| PATCH | `/{id}/update/` | Update status / notes |
| POST | `/{id}/withdraw/` | Withdraw application |
| GET/POST | `/interviews/` | List or schedule interviews |
| GET/POST | `/{application_id}/messages/` | In-app messaging |

### 📋 Job Forms — `/api/job-forms/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/forms/` | List or create custom forms |
| GET/PUT/DELETE | `/forms/{id}/` | Manage specific form |

### 📖 Docs

| Endpoint | Description |
|----------|-------------|
| `/api/docs/swagger/` | Swagger UI |
| `/api/docs/redoc/` | ReDoc UI |
| `/api/schema/` | Raw OpenAPI schema |
| `/admin/` | Django admin panel |

---

## Installation & Setup

### Prerequisites

- Python 3.8+
- PostgreSQL
- pip + virtualenv

### 1. Clone the repository

```bash
git clone https://github.com/AlyaariHazem/Tawthif-backend.git
cd Tawthif-backend
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root (or set variables in your shell):

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=postgres://user:password@host:5432/dbname
GEMINI_API_KEY=your-gemini-api-key
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
```

> ⚠️ **Security Note:** All secrets (`SECRET_KEY`, `DATABASE_URL`, `GEMINI_API_KEY`, `CLOUDINARY_URL`) **must** be set via environment variables and must **never** be committed to version control. Set `DEBUG=False` in production.

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Create a superuser (admin account)

```bash
# Option A — interactive Django command
python manage.py createsuperuser

# Option B — using the included script
python create_superuser_script.py
```

### 7. (Optional) Load initial data or seed categories

```bash
python manage.py shell
# then create JobCategory objects as needed
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ | Django secret key — must be a long, random string; **no safe default** |
| `DEBUG` | ✅ | Set to `True` for development, `False` in production |
| `ALLOWED_HOSTS` | ✅ | Comma-separated list of allowed host names |
| `DATABASE_URL` | ✅ | PostgreSQL connection string — **no default; must be configured** |
| `GEMINI_API_KEY` | ✅ | Google Gemini API key for AI summaries — **no default; must be configured** |
| `CLOUDINARY_URL` | ✅ | Cloudinary URL for media storage — **no default; must be configured** |
| `PORT` | — | Port used by gunicorn in `start.sh` (default: `8000`) |

> ⚠️ **Never commit secrets to version control.** Use a `.env` file locally (add `.env` to `.gitignore`) and set secrets via your cloud platform's environment variable management in production.

---

## Running the Project

### Development

```bash
python manage.py runserver
```

The API will be available at **http://localhost:8000**.

### Production (Gunicorn)

```bash
bash start.sh
```

Or manually:

```bash
gunicorn job_portal_backend.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

---

## API Documentation

Once the server is running, visit:

| URL | Interface |
|-----|-----------|
| http://localhost:8000/api/docs/swagger/ | Swagger UI (interactive) |
| http://localhost:8000/api/docs/redoc/ | ReDoc (clean documentation) |
| http://localhost:8000/api/schema/ | Raw OpenAPI 3.0 JSON schema |
| http://localhost:8000/admin/ | Django admin panel |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## License

This project is open-source. See the repository for license details.
