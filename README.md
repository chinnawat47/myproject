# Volunteer System (Django)

A demo Django 5+ project implementing a volunteer-hour system with QR confirmation, registration restricted to `@ubu.ac.th`, activity signups, groups, voting, and a simple chatbot.

---

## Key Features

- Volunteer activity listings with signup, QR confirmation, and pagination
- Idea proposal center with community voting (`/ideas/`) powered by the new `IdeaVote` model
- Custom admin dashboard for activities, ideas, and users
- Floating chatbot widget that answers FAQs and is accessible on every page
- Group management with invite codes and group posts

---

## Requirements

- Python 3.10+ recommended
- pip
- Node.js + npm (for Tailwind CSS)
- Git (optional, for version control)

---

## Setup (local)

1. Clone or copy project files into `volunteer_system/` directory.

```bash
git clone https://github.com/chinnawat47/myproject.git
cd myproject

## Create a virtual environment and activate it:

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

## Install Python dependencies:

pip install -r requirements.txt

## Install Tailwind dependencies and build CSS:

python manage.py tailwind install
python manage.py tailwind build


## Apply database migrations:

python manage.py migrate
python manage.py makemigrations



## (Optional) Create superuser for admin access:

python manage.py createsuperuser


## Run the local development server:

python manage.py runserver



## Project Structure

volunteer_system/
│
├── accounts/            # User registration and authentication
├── volunteer/           # Volunteer activities and groups
├── templates/           # HTML templates
├── static/              # CSS, JS, images
├── manage.py
└── requirements.txt



## คำอธิบายโครงสร้าง

accounts/: แอปที่จัดการผู้ใช้ เช่น การลงทะเบียน, การเข้าสู่ระบบ, และการจัดการโปรไฟล์

volunteer/: แอปที่จัดการกิจกรรมจิตอาสา เช่น การสร้างกิจกรรม, การสมัครเข้าร่วม, และการแสดงผลกิจกรรม

config/: โฟลเดอร์ที่เก็บการตั้งค่าหลักของโปรเจกต์ เช่น การตั้งค่า Django, URL routing, และ WSGI/ASGI

manage.py: สคริปต์หลักที่ใช้สำหรับการจัดการโปรเจกต์ Django

requirements.txt: รายการของ Python packages ที่โปรเจกต์ต้องการ

tailwind.config.js: การตั้งค่าของ Tailwind CSS

package.json: รายการของ Node.js packages ที่โปรเจกต์ต้องการ

.gitignore: ไฟล์ที่ระบุว่า Git จะไม่ติดตามไฟล์หรือโฟลเดอร์ใดบ้าง

README.md: เอกสารที่อธิบายเกี่ยวกับโปรเจกต์ เช่น วิธีการติดตั้ง, การใช้งาน, และการตั้งค่า

static/: โฟลเดอร์ที่เก็บไฟล์ static เช่น CSS, JavaScript, และรูปภาพ