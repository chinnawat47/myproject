# สถาปัตยกรรมระบบและแนวทางต่อยอดโปรเจค ระบบจัดการอาสาสมัคร ม.อุบลราชธานี

## 1. สถาปัตยกรรมระบบ (System Architecture)

### 1.1 โครงสร้างโดยรวม

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client (Browser)                                │
│  HTML + Tailwind CSS │ JavaScript (QR Scanner, Chatbot, Check-in/out)       │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ HTTP/HTTPS
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Django Application (WSGI)                             │
│  volunteer_system (settings, urls)  ←→  volunteer_app (views, urls)          │
│  Middleware: Security, Session, CSRF, Auth, Messages, BrowserReload          │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
│   volunteer_app       │  │   theme (Tailwind)    │  │   media / static      │
│   - models.py         │  │   - tailwind.config   │  │   - uploads, CSS, JS   │
│   - views.py          │  │   - static_src       │  │   - staticfiles        │
│   - forms.py          │  └───────────────────────┘  └───────────────────────┘
│   - utils.py          │
│   - services/         │
│     notification_     │
│     service.py        │
└───────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     SQLite (db.sqlite3) — ฐานข้อมูล                           │
│  User, Activity, ActivitySignup, QRScan, CheckInOut, IdeaProposal,          │
│  IdeaVote, Notification, NotificationPreference, Group, GroupMembership,    │
│  GroupPost, Role                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 เลเยอร์หลัก

| เลเยอร์ | เทคโนโลยี | หน้าที่ |
|--------|-----------|--------|
| **Presentation** | Django Templates + Tailwind CSS | หน้าเว็บ, UI, responsive |
| **Business Logic** | Django Views (FBV) | จัดการ request, เรียก models/services |
| **Data Access** | Django ORM | อ่าน/เขียนฐานข้อมูล |
| **Services** | `volunteer_app/services/` | Logic แยกส่วน (เช่น แจ้งเตือน) |
| **Utils** | `volunteer_app/utils.py` | QR/Check-in token, อ่าน QR จากรูป |
| **Data** | SQLite + Django Models | เก็บข้อมูล |

### 1.3 โมเดลข้อมูลหลัก (Data Model)

```
User (AbstractUser + ขยาย)
  ├── roles (M2M) → Role
  ├── signups → ActivitySignup → Activity
  ├── qr_scans → QRScan → Activity
  ├── check_ins_outs → CheckInOut → Activity
  ├── ideas → IdeaProposal, idea_votes → IdeaVote
  ├── notifications → Notification
  ├── notification_pref → NotificationPreference
  └── group_memberships → GroupMembership → Group
       Group → GroupPost

Activity
  ├── signups (ActivitySignup)
  ├── qr_scans (QRScan)
  └── check_ins_outs (CheckInOut)
```

### 1.4 การรับส่งข้อมูล

- **Request/Response**: ส่วนใหญ่เป็น server-rendered (Django templates) + บางจุดใช้ `JsonResponse` (QR verify, check-in/out, chatbot, join group)
- **Authentication**: Session-based (Django auth), cookie
- **API**: ยังไม่มี REST API (มีแค่ endpoint แบบ POST สำหรับ chatbot, QR, check-in/out)
- **Real-time**: ยังไม่ใช้ WebSocket (channels ติดตั้งแล้วแต่ไม่ได้ใช้ใน asgi.py)

---

## 2. สิ่งที่โปรเจคยังขาดหรือสามารถต่อยอดได้

### 2.1 ฟีเจอร์ที่ติดตั้งแล้วแต่ยังไม่ได้ใช้เต็มที่

| รายการ | สถานะ | แนวทางต่อยอด |
|--------|--------|----------------|
| **django-allauth** | กำหนดค่าแล้วแต่ไม่ได้รวมใน INSTALLED_APPS/urls | ใช้จัดการ login/register, social login, ยืนยันอีเมลแบบมาตรฐาน |
| **djangorestframework** | มีใน requirements แต่ไม่มี ViewSet/API | สร้าง REST API สำหรับแอปมือถือ, integration กับระบบอื่น |
| **channels** | มีใน requirements แต่ asgi.py ใช้ get_asgi_application() อย่างเดียว | ใช้ WebSocket สำหรับแจ้งเตือน real-time, แชทในกลุ่ม |

### 2.2 การยืนยันอีเมล (Email Verification)

- มีฟิลด์ `User.email_verified`, `email_verified_at` แต่ไม่มี flow ส่งลิงก์ยืนยันอีเมลหลังสมัคร
- อีเมลใช้ backend แบบ console ใน development
- **ต่อยอด**: สร้าง flow ยืนยันอีเมล (ส่งลิงก์ + token), ตั้งค่า SMTP จริง, จำกัดการใช้งานบางส่วนจนกว่าจะ verify

### 2.3 Chatbot

- ตอบคำถามจากคำหลัก (keyword) ในภาษาไทย/อังกฤษ ไม่ได้ใช้ AI/NLP
- **ต่อยอด**: ต่อ LLM (เช่น OpenAI, หรือ model ในไทย) ให้ตอบจาก context กิจกรรม/กฎ, หรือใช้ RAG จากเอกสารช่วยใช้

### 2.4 ฐานข้อมูลและการ deploy

- ใช้ SQLite เหมาะกับ dev เท่านั้น
- **ต่อยอด**: ใช้ PostgreSQL/MySQL ใน production, ตั้งค่าใน settings จาก env

### 2.5 การทดสอบ (Testing)

- มี unit tests ใน `volunteer_app/tests.py` สำหรับ User, Activity, Signup, QR
- ยังไม่มี tests สำหรับ Check-in/Check-out, Notifications, Groups, Chatbot, Admin
- **ต่อยอด**: เพิ่ม tests สำหรับ flow หลักและ edge cases, พิจารณา integration tests

### 2.6 API และแอปมือถือ

- ไม่มี REST API ให้แอปมือถือหรือฝั่งนอกเรียก
- **ต่อยอด**: ใช้ DRF สร้าง API (activities, signup, profile, hours, notifications) + JWT หรือ token auth สำหรับแอป

### 2.7 Real-time และแจ้งเตือน

- แจ้งเตือนเป็น in-app (เก็บใน DB) + อีเมล ผ่าน `notification_service`
- ยังไม่มีการ push แบบ real-time (ต้อง refresh หน้า)
- **ต่อยอด**: ใช้ Django Channels + WebSocket ส่งการแจ้งเตือนทันที, หรือใช้ Service Worker + Web Push

### 2.8 ความปลอดภัยและสิทธิ์

- มี Role และ `user.has_role()`, แอดมินมี custom dashboard
- **ต่อยอด**: กำหนด permission ชัดเจนต่อ view/model (เช่น django-guardian), rate limit สำหรับ login/API, audit log การกระทำสำคัญ

### 2.9 รายงานและสถิติ

- แอดมินดูชั่วโมงผู้ใช้ได้ แต่ไม่มี dashboard สถิติ/กราฟ
- **ต่อยอด**: หน้ารายงาน (จำนวนกิจกรรม, ชั่วโมงรวม, แยกตามคณะ/ประเภท), export CSV/Excel

### 2.10 UX และการเข้าถึง

- มี Tailwind, responsive
- **ต่อยอด**: PWA (offline ดูกิจกรรม), ปรับปรุง accessibility (ARIA, keyboard), หลายภาษา (i18n) ถ้าต้องขยายไปหน่วยงานอื่น

### 2.11 กลุ่ม (Groups)

- มีกลุ่ม, โพสต์, รหัสเชิญ
- **ต่อยอด**: แชทในกลุ่มแบบ real-time (Channels), แนบไฟล์ในโพสต์, สิทธิ์แอดมินกลุ่ม

### 2.12 ไอเดีย (Idea Proposals)

- มีการเสนอไอเดียและโหวต
- **ต่อยอด**: workflow “สร้างกิจกรรมจากไอเดีย” ให้ชัดเจน, แจ้งเตือนเมื่อไอเดียถูก approve/reject

---

## 3. สรุปลำดับความสำคัญในการต่อยอด (แนะนำ)

1. **Email verification flow + SMTP** — เพิ่มความน่าเชื่อถือของ user
2. **REST API (DRF)** — เปิดทางให้แอปมือถือและระบบภายนอก
3. **Tests เพิ่มเติม** — โดยเฉพาะ Check-in/Check-out, notifications
4. **Production DB (PostgreSQL)** — พร้อม deploy จริง
5. **Real-time notifications (Channels)** — UX ดีขึ้น
6. **Dashboard รายงาน/สถิติ** — สำหรับแอดมิน
7. **Chatbot ต่อ LLM** — ตอบคำถามได้ยืดหยุ่นขึ้น

---

*เอกสารนี้สรุปจากโครงสร้างโปรเจค ณ ปัจจุบัน อาจมีการเปลี่ยนแปลงตามการพัฒนาต่อไป*
