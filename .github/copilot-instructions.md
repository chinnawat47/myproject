# AI Copilot Instructions for Volunteer System

## Project Overview

This is a **Django 5.0 volunteer management platform** for Ubonratchathani University (`@ubu.ac.th` domain). It manages activities, user signups, QR-based attendance confirmation, groups, idea proposals, and voting.

**Key Constraint**: Registration is restricted to university email addresses (`@ubu.ac.th`). Email validation occurs in `volunteer_app/forms.py` using regex pattern `UBU_EMAIL_REGEX`.

## Architecture

### Core Data Model (volunteer_app/models.py)

- **User** (custom AbstractUser): Extends Django auth with student profile (ID, faculty, department, year, title). Has `is_admin` boolean for role distinction.
- **Activity**: Event with capacity, hours reward, category, QR token. Tracks `signups` and `qr_scans`.
- **ActivitySignup** + **QRScan**: Attendance confirmation via two-step process. QRScan validates actual participation and awards volunteer hours via `User.total_hours()`.
- **Group** + **GroupMembership** + **GroupPost**: Group coordination with secure invitation codes.
- **IdeaProposal**: User-submitted activity ideas awaiting admin review.
- **Vote**: Activity voting mechanism.

**Critical Pattern**: All models use `related_name` for reverse relationships (e.g., `user.signups.all()`). Foreign keys use `on_delete=models.CASCADE` or `SET_NULL` for admin-created content.

### URL Routing (volunteer_app/urls.py)

Named URL patterns with app namespace `"volunteer_app"`. Key patterns:
- Auth: `login`, `logout`, `register`
- Activities: `activities`, `activity_detail`, `create_activity`, `activity_signup`
- QR: `qr_scan`, `qr_verify`, `qr_confirm`
- Groups: `groups`, `create_group`, `group_detail`, `join_group`
- Admin: `admin_dashboard`, `custom-admin/login` (custom admin system, not Django's)

### Frontend Stack

- **CSS**: Tailwind CSS (via CDN in base template, no build required for development). Custom colors in `tailwind.config.js`:
  - `primary: #41A67E` (green)
  - `darkBlue: #05339C`, `blue: #1055C9`
  - `gold: #E5C95F`
- **Font**: Sarabun family for Thai typography
- **Forms**: Django crispy-forms with crispy-tailwind renderer (see `forms.py`)
- **JavaScript**: jQuery 3.6, Font Awesome 6.4.2, qrcode.js for QR generation

### Key External Dependencies

- `django-tailwind`: CSS compilation (setup required via `python manage.py tailwind build`)
- `qrcode` + `opencv-python`: QR generation and scanning
- `django-allauth`: (in requirements.txt but not configured - TODO)
- `channels`: (in requirements.txt but not used - TODO)
- `djangorestframework`: (in requirements.txt but not used - TODO)
- `Pillow`: Image handling for activity uploads

## Developer Workflows

### Local Development Setup

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python manage.py tailwind install
python manage.py tailwind build
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Database Schema

- **No explicit seed command** despite `management/commands/seed.py` existing
- **Migrations**: Apply before running; custom `User` model requires special handling
- Media files store in `media/activities/{activity_id}/`

### Testing

No test infrastructure visible in workspace. Add tests to `volunteer_app/tests.py`.

## Code Patterns & Conventions

### Views (views.py)

1. **Helper functions at top**: `is_admin(user)` checks `is_staff` or `is_superuser`
2. **Decorator stack**: Combine `@login_required`, `@require_POST`, `@user_passes_test(is_admin)`
3. **Form-driven views**: Request.POST → form validation → conditional redirect
4. **Email-based login**: Support both username and email (`User.objects.get(email=...)`)
5. **Thai language strings**: Error messages and context labels use Thai (ภาษาไทย)
6. **QR workflow**:
   - `qr_scan_page`: Renders scanner UI
   - `qr_verify`: Receives scanned token, validates via `QRScan` model
   - `qr_confirm`: Final confirmation, awards hours

### Forms (forms.py)

- Custom validation in `clean_*` methods (e.g., `clean_email()` enforces UBU domain)
- `ActivityForm` validates future `datetime` only
- `RegistrationForm` derives `username` from email prefix (`email.split("@")[0]`)
- Widgets: DateTimeInput with `type="datetime-local"`

### Models

- Use `models.CharField(max_length=...)` for fixed-length strings
- `DecimalField(max_digits=4, decimal_places=1)` for hours (e.g., 1.0, 2.5)
- Helper methods return computed values (e.g., `User.total_hours()`, `Activity.is_full()`)
- UUID-based QR token: `uuid.uuid5(uuid.NAMESPACE_URL, f"activity-{self.id}")`

### Templates

- **Base inheritance**: All templates extend `base.html`
- **Thai lang attribute**: `<html lang="th">`
- **Block structure**: `{% block title %}`, `{% block head %}`, `{% block content %}`
- **Tailwind utility classes**: No custom CSS beyond vendor includes
- **Form rendering**: Use `{{ form.as_p }}` or manual field layout with crispy filters

## Common Tasks

### Adding a New Activity Field

1. Update `Activity` model in `models.py`
2. Create migration: `python manage.py makemigrations`
3. Apply: `python manage.py migrate`
4. Update `ActivityForm` in `forms.py`
5. Adjust templates (`activity_detail.html`, `create_activity.html`)
6. Add to admin if needed: `volunteer_app/admin.py`

### Adding a New View

1. Define in `views.py`, following decorator/form patterns
2. Add URL pattern to `volunteer_app/urls.py` with descriptive name
3. Create or reuse template with proper inheritance
4. Link from nav in `base.html` if publicly visible

### Managing User Roles

- **Superuser/Staff**: Django defaults (`is_superuser`, `is_staff`)
- **Admin flag**: Custom `User.is_admin` boolean (currently unused - consider consolidation)
- Check in views: `if request.user.is_superuser:` or custom `is_admin(user)` helper

## File Organization

```
volunteer_app/
├── models.py           # All data models; ~150 lines
├── views.py            # 400+ lines; 8 main sections (helpers, user, activity, QR, group, etc.)
├── forms.py            # 60 lines; 6 form classes with custom validation
├── urls.py             # Route definitions with app namespace
├── admin.py            # Django admin registration (if configured)
├── templates/          # HTML templates (base + feature-specific)
└── static/volunteer_app/  # CSS, JS, images by feature
volunteer_system/       # Django project config (settings, urls, wsgi, asgi)
theme/                  # Tailwind build target (CSS output)
theme/static_src/       # Tailwind source (postcss.config.js, src/styles.css)
```

## Admin & Superuser

- Django `/admin/` route available for superusers
- **Custom admin interface**: `custom-admin/` routes for custom dashboard (see `admin_dashboard` view)
- Both systems coexist; prefer Django admin for data CRUD, custom dashboard for business logic

## Known Limitations & TODOs

1. **django-allauth** in requirements but not configured → Remove or complete setup
2. **channels** and **djangorestframework** unused → Plan WebSocket features or API endpoints
3. No automated tests → Add unit tests for models, form validation, QR logic
4. QR token uniqueness: `uuid.uuid5` deterministic; consider `secrets` for true randomness
5. Group invite code: Uses `secrets.token_urlsafe()` (secure) but no expiry
6. Thai localization: Mixed Thai/English in forms; consider `django-modeltranslation` for full i18n

## Quick Reference

| Task | Location |
|------|----------|
| Add custom user field | `User` model in `models.py`, migrate, update `RegistrationForm` |
| Add admin check | Use `@user_passes_test(is_admin)` or inline `if is_admin(request.user):` |
| Update styling | Tailwind classes in templates; rebuild CSS if using theme app |
| Change QR logic | `qr_verify`, `qr_confirm` views + `QRScan` model |
| Manage hours | `User.total_hours()` aggregates from `QRScan.activity.hours_reward` |
| Email validation | `UBU_EMAIL_REGEX` in `forms.py` registration |
