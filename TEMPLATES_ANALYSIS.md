# การวิเคราะห์ Django Templates โปรเจค Volunteer System

เอกสารนี้อธิบายทุกไฟล์ HTML ใน `volunteer_app/templates/` การเชื่อมกับ View/URL Forms และ JavaScript รวมถึง flow ภาพรวม Frontend → Backend

---

## สารบัญ

1. [รายการ Template แยกตามไฟล์](#1-รายการ-template-แยกตามไฟล์)
2. [ความสัมพันธ์ extends / include](#2-ความสัมพันธ์-extends--include)
3. [Form action, method และ Backend View](#3-form-action-method-และ-backend-view)
4. [JavaScript และการเรียก Endpoint/API](#4-javascript-และการเรียก-endpointapi)
5. [Flow สรุป Frontend → Backend](#5-flow-สรุป-frontend--backend)

---

## 1. รายการ Template แยกตามไฟล์

### 1.1 base.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | Layout หลักของเว็บ: navbar, footer, โหลด CSS/JS, กำหนด block (`title`, `head`, `content`, `scripts`) |
| **View ที่ render** | ไม่ถูก render โดยตรง — ใช้ผ่าน `extends` จาก template อื่น |
| **URL** | - |
| **extends** | ไม่มี (เป็นฐาน) |
| **include** | `{% include "chatbot_widget.html" %}` (เมื่อ user login และไม่ใช่หน้า admin) |

**Form ใน base.html:**
- Logout (desktop + mobile): `method="POST"` `action="{% url 'volunteer_app:logout' %}"` → View: `logout_view` → URL: `/accounts/logout/`

---

### 1.2 index.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | หน้าแรก: Hero, กิจกรรมล่าสุด (6 รายการ), โหวตไอเดีย (3 อันดับ), CTA |
| **View** | `index` |
| **URL** | `/` (name: `index`) |

**extends:** `base.html`  
**include:** ไม่มี  

**Form:**
- โหวตไอเดีย (ในบล็อก top_ideas): `method="post"` `action="{% url 'volunteer_app:vote_idea' idea.pk %}"` → View: `vote_idea` → URL: `/ideas/<pk>/vote/`  
  - fields: `csrf_token`, `action` (vote/unvote), `next`

---

### 1.3 registration/login.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | หน้าเข้าสู่ระบบ (username/email + password, จดจำการเข้าสู่ระบบ) |
| **View** | `login_view` |
| **URL** | `/accounts/login/` (name: `login`) |

**extends:** `base.html`  
**include:** ไม่มี  

**Form:**
- Login: `method="post"` (action = current URL = `/accounts/login/`) → View: `login_view`  
  - fields: `csrf_token`, `username`, `password`, `remember-me`  
- ลิงก์ "ลืมรหัสผ่าน" ชี้ไป `#` (ยังไม่ implement)

**JavaScript:** validation ฝั่ง client (required, email format, password length), toggle แสดง/ซ่อนรหัสผ่าน ไม่มีการเรียก API เพิ่ม

---

### 1.4 registration/register.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | หน้าสมัครสมาชิก (อีเมล @ubu.ac.th เท่านั้น) |
| **View** | `register` |
| **URL** | `/accounts/register/` (name: `register`) |

**extends:** `base.html`  
**include:** ไม่มี  

**Form:**
- Register: `method="post"` (action = current URL) → View: `register`  
  - ใช้ Django form (`form`) จาก view  
- ลิงก์ "เข้าสู่ระบบ" ชี้ไป `#` (ควรเป็น `{% url 'volunteer_app:login' %}`)

**JavaScript:** ตรวจสอบ domain อีเมล @ubu.ac.th แบบ real-time และก่อน submit, ไม่มี fetch/API

---

### 1.5 profile.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | แสดงโปรไฟล์ผู้ใช้: ข้อมูลส่วนตัว, ชั่วโมงรวม, ประวัติการสมัครกิจกรรม |
| **View** | `profile` |
| **URL** | `/profile/` (name: `profile`) |

**extends:** `base.html`  
**include:** ไม่มี  

**Form:** ไม่มี (มีแค่ลิงก์ไปแก้ไขโปรไฟล์และเปลี่ยนรหัสผ่าน)

---

### 1.6 edit_profile.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | แก้ไขข้อมูลผู้ใช้ (ชื่อ, นามสกุล, คำนำหน้า, คณะ, สาขา, ชั้นปี ฯลฯ) |
| **View** | `edit_profile` |
| **URL** | `/profile/edit/` (name: `edit_profile`) |

**extends:** `base.html`  
**include:** ไม่มี  

**Form:**
- แก้ไขโปรไฟล์: `method="post"` (action = current URL) → View: `edit_profile`  
  - fields: first_name, last_name, title, faculty, department, year ฯลฯ

---

### 1.7 change_password.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | เปลี่ยนรหัสผ่าน (รหัสเก่า, รหัสใหม่, ยืนยันรหัสใหม่) |
| **View** | `change_password` |
| **URL** | `/profile/change-password/` (name: `change_password`) |

**extends:** `base.html`  
**include:** ไม่มี  

**Form:**
- เปลี่ยนรหัสผ่าน: `method="post"` (action = current URL) → View: `change_password`  
  - fields: old_password, new_password1, new_password2

---

### 1.8 activities.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | รายการกิจกรรมทั้งหมด + ค้นหา/กรอง (ชื่อ, หมวดหมู่, วันที่, สถานที่ ฯลฯ) + แบ่งหน้า |
| **View** | `activities` |
| **URL** | `/activities/` (name: `activities`) |

**extends:** `base.html`  
**include:** ไม่มี  

**Form:**
- ค้นหา/กรอง: `method="get"` (action = current URL) → View: `activities`  
  - params: q, category, date_from, date_to, location, faculty, hours, page  

ไม่มี form POST; ปุ่ม "สร้างกิจกรรม" เป็นลิงก์ไป `/activity/create/` (สำหรับ staff/superuser)

---

### 1.9 activity_detail.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | รายละเอียดกิจกรรมเดียว: ข้อมูล, ปุ่มสมัคร, QR สำหรับยืนยันชั่วโมง (token/URL), หมายเหตุ |
| **View** | `activity_detail` |
| **URL** | `/activity/<int:pk>/` (name: `activity_detail`) |

**extends:** `base.html`  
**include:** ไม่มี  

**Form:**
- สมัครกิจกรรม: `method="post"` `action="{% url 'volunteer_app:activity_signup' activity.pk %}"` → View: `activity_signup` → URL: `/activity/<pk>/signup/`  
  - fields: csrf_token, note  

ไม่มี JavaScript เรียก API ใน template นี้ (Check-in/Check-out ใช้ที่หน้า qr_scan หรือลิงก์โดยตรงไป endpoint)

---

### 1.10 create_activity.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | สร้างกิจกรรมใหม่ (title, description, category, datetime, location, capacity, hours_reward, image) |
| **View** | `create_activity` |
| **URL** | `/activity/create/` (name: `create_activity`) |

**extends:** `base.html`  
**include:** ไม่มี  

**Form:**
- สร้างกิจกรรม: `method="post"` `enctype="multipart/form-data"` (action = current URL) → View: `create_activity`  
  - ใช้ Django `ActivityForm` จาก view

---

### 1.11 qr_scan.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | หน้ารวมการยืนยันชั่วโมง: สแกน QR (กล้อง), อัปโหลดรูป QR, กรอกโทเค็นมือ |
| **View** | `qr_scan_page` |
| **URL** | `/qr/scan/` (name: `qr_scan`) |

**extends:** `base.html`  
**include:** ไม่มี  

**Form (HTML):**
- อัปโหลดรูป QR: `id="qr-upload-form"` `enctype="multipart/form-data"` — ส่งผ่าน JavaScript fetch ไป `qr_upload` (ไม่ submit ธรรมดา)
- กรอกโทเค็นมือ: `id="manual-token-form"` — ส่งผ่าน JS (ใช้ verifyUrl) ไป `qr_verify`

**JavaScript / Endpoint:**
- `initQrScanner("{% url 'volunteer_app:qr_verify' %}")` → สแกนได้ token แล้ว POST ไป `qr_verify`
- อัปโหลดรูป: `fetch(uploadUrl)` โดย `uploadUrl = "{% url 'volunteer_app:qr_upload' %}"` (POST, FormData มี image)
- กรอกโทเค็นมือ: ใช้ `verifyUrl` (qr_verify) ผ่าน logic ใน qr_scanner_main.js หรือ inline script

→ **Endpoints ที่เรียก:** `/qr/verify/` (POST token), `/qr/upload/` (POST ไฟล์รูป)

---

### 1.12 qr_confirm_result.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | แสดงผลหลังยืนยัน (ผ่านลิงก์ qr/confirm/<token>/): สำเร็จ หรือข้อผิดพลาด + รายละเอียดกิจกรรม |
| **View** | `qr_confirm` (และ branch อื่นที่ render template เดียวกัน) |
| **URL** | ไม่ใช่ path โดยตรง — ใช้เมื่อเปิด `/qr/confirm/<str:token>/` (name: `qr_confirm`) |

**extends:** `base.html`  
**include:** ไม่มี  

**Form:** ไม่มี (เป็นหน้าแสดงผลอย่างเดียว)

---

### 1.13 ideas_list.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | รายการไอเดีย + ค้นหา/กรอง (q, status) + ปุ่มโหวต/ยกเลิกโหวต |
| **View** | `idea_list` |
| **URL** | `/ideas/` (name: `idea_list`) |

**extends:** `base.html`  
**include:** ไม่มี  

**Form:**
- ค้นหา: `method="get"` (action = current URL) → View: `idea_list` (params: q, status)
- โหวตไอเดีย: แต่ละไอเดียมี form `method="post"` `action="{% url 'volunteer_app:vote_idea' idea.pk %}"` → View: `vote_idea` → URL: `/ideas/<pk>/vote/`  
  - fields: csrf_token, action (vote/unvote)

**JavaScript:** มีการส่ง form โหวตแบบ AJAX (fetch form.action) เพื่ออัปเดตคะแนนโดยไม่ reload — ยังคง POST ไปที่ `vote_idea` เหมือนเดิม

---

### 1.14 propose_idea.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | แบบฟอร์มเสนอไอเดียกิจกรรม (title, description, target_hours ฯลฯ) |
| **View** | `propose_idea` |
| **URL** | `/ideas/propose/` (name: `propose_idea`) |

**extends:** `base.html`  
**include:** ไม่มี  

**Form:**
- เสนอไอเดีย: `method="post"` (action = current URL) → View: `propose_idea`  
  - ใช้ Django `IdeaForm` จาก view

---

### 1.15 notifications.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | รายการการแจ้งเตือน + ปุ่มทำเครื่องหมายว่าอ่านแล้ว (รายการ/ทั้งหมด) |
| **View** | `notification_list` |
| **URL** | `/notifications/` (name: `notifications`) |

**extends:** `base.html`  
**include:** ไม่มี  

**Form:**
- อ่านทั้งหมด: `method="post"` `action="{% url 'volunteer_app:notification_mark_all' %}"` → View: `notification_mark_all` → URL: `/notifications/read-all/`
- อ่านแล้ว (แต่ละรายการ): `method="post"` `action="{% url 'volunteer_app:notification_mark_read' notification.pk %}"` → View: `notification_mark_read` → URL: `/notifications/<pk>/read/`

---

### 1.16 groups.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | รายการกลุ่ม + ปุ่มเข้าร่วมกลุ่ม |
| **View** | `groups_list` |
| **URL** | `/groups/` (name: `groups`) |

**extends:** `base.html`  
**include:** ไม่มี  

**Form:**
- เข้าร่วมกลุ่ม (แต่ละกลุ่ม): `method="post"` `action="{% url 'volunteer_app:join_group' g.pk %}"` → View: `join_group` → URL: `/group/<pk>/join/`

---

### 1.17 create_group.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | สร้างกลุ่มใหม่ (ชื่อ, รายละเอียด) |
| **View** | `create_group` |
| **URL** | `/group/create/` (name: `create_group`) |

**extends:** `base.html`  
**include:** ไม่มี  

**Form:**
- สร้างกลุ่ม: `method="post"` (action = current URL) → View: `create_group`  
  - ใช้ Django `GroupForm` จาก view

---

### 1.18 group_detail.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | รายละเอียดกลุ่ม: รหัสเชิญ, เข้าร่วมกลุ่ม, เชิญเพื่อน (username), แชทกลุ่ม (โพสต์ข้อความ) |
| **View** | `group_detail` |
| **URL** | `/group/<int:pk>/` (name: `group_detail`) |

**extends:** `base.html`  
**include:** ไม่มี  

**Form (ทั้งหมด POST ไปที่ URL ปัจจุบัน = group_detail):**
- เข้าร่วมกลุ่ม: `method="post"` ไม่ระบุ action → POST ไป `/group/<pk>/` โดยส่ง `join_group=1` → View: `group_detail` (รับ POST join_group)
- เชิญเพื่อน: `method="post"` `id="inviteForm"` → POST ไป `/group/<pk>/` โดยส่ง `invite_username` → View: `group_detail`
- โพสต์ข้อความ: `method="post"` `action=""` `id="postForm"` → POST ไป `/group/<pk>/` โดยส่ง `content` → View: `group_detail`

**JavaScript:**  
- ส่ง form ข้างบนด้วย `fetch("", { method: "POST", body: formData })` และตั้ง header `X-Requested-With: XMLHttpRequest` เพื่อให้ view คืน JSON  
- Endpoint ที่เรียกคือ **URL ปัจจุบัน** (group_detail) ไม่ใช่ join_group URL

---

### 1.19 chatbot_widget.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | วิดเจ็ตแชทบอท (FAQ): input ข้อความ, ปุ่มส่ง, คำถามยอดนิยม |
| **View** | ไม่มี — ถูก include จาก `base.html` |
| **URL** | - |

**extends:** ไม่มี  
**include:** ถูก include ใน `base.html`  

**Form:** ไม่มี form submit ธรรมดา — การส่งข้อความทำผ่าน JavaScript

**JavaScript:**  
- `initChatbot("{% url 'volunteer_app:chatbot_api' %}")` ใน chatbot_app.js  
- ส่งข้อความ: `fetch(apiUrl, { method: "POST", body: new URLSearchParams({ q: q }) })` พร้อม CSRF  
→ **Endpoint:** `/chatbot/` (name: `chatbot_api`) → View: `chatbot_api`

---

### 1.20 admin_login.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | หน้า login สำหรับแอดมิน (custom admin) |
| **View** | `admin_login` |
| **URL** | `/custom-admin/login/` (name: `admin_login`) |

**extends:** `base.html` (หรือ admin base ถ้ามี)  
**include:** ไม่มี  

**Form:**
- Admin login: `method="post"` `action="{% url 'volunteer_app:admin_login' %}"` → View: `admin_login`

---

### 1.21 admin_dashboard.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | แดชบอร์ดแอดมิน: สรุปกิจกรรม/ไอเดีย/ผู้ใช้, ไอเดียรออนุมัติ, ลิงก์จัดการ, ลบ QR scan |
| **View** | `admin_dashboard` |
| **URL** | `/custom-admin/dashboard/` (name: `admin_dashboard`) |

**extends:** `base.html` (หรือ admin layout)  
**include:** ไม่มี  

**Form:**
- อนุมัติไอเดีย: `method="post"` `action="{% url 'volunteer_app:admin_approve_idea' idea.pk %}"` → View: `admin_approve_idea` → URL: `/custom-admin/idea/<pk>/approve/`
- ปฏิเสธไอเดีย: `method="post"` `action="{% url 'volunteer_app:admin_reject_idea' idea.pk %}"` → View: `admin_reject_idea` → URL: `/custom-admin/idea/<pk>/reject/`
- ลบ QR scan: `method="post"` `action="{% url 'volunteer_app:admin_delete_qr_scan' scan.pk %}"` → View: `admin_delete_qr_scan` → URL: `/custom-admin/qr-scan/<pk>/delete/`

---

### 1.22 admin_manage_activities.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | รายการกิจกรรมสำหรับแอดมิน แก้ไข/ลบ |
| **View** | `admin_manage_activities` |
| **URL** | `/custom-admin/activities/` (name: `admin_manage_activities`) |

**extends:** base (หรือ admin)  
**include:** ไม่มี  

**Form:**
- ลบกิจกรรม: `method="post"` `action="{% url 'volunteer_app:admin_delete_activity' activity.pk %}"` → View: `admin_delete_activity` → URL: `/custom-admin/activity/<pk>/delete/`

---

### 1.23 admin_edit_activity.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | แก้ไขกิจกรรม (ฟิลด์เดียวกับสร้าง + status ฯลฯ) |
| **View** | `admin_edit_activity` |
| **URL** | `/custom-admin/activity/<int:pk>/edit/` (name: `admin_edit_activity`) |

**extends:** base (หรือ admin)  
**include:** ไม่มี  

**Form:**
- แก้ไขกิจกรรม: `method="post"` `enctype="multipart/form-data"` (action = current URL) → View: `admin_edit_activity`

---

### 1.24 admin_manage_ideas.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | รายการไอเดียสำหรับแอดมิน อนุมัติ/ปฏิเสธ |
| **View** | `admin_manage_ideas` |
| **URL** | `/custom-admin/ideas/` (name: `admin_manage_ideas`) |

**extends:** base (หรือ admin)  
**include:** ไม่มี  

**Form:**
- อนุมัติ: `method="post"` `action="{% url 'volunteer_app:admin_approve_idea' idea.pk %}"`
- ปฏิเสธ: `method="post"` `action="{% url 'volunteer_app:admin_reject_idea' idea.pk %}"`

---

### 1.25 admin_manage_users.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | รายการผู้ใช้สำหรับแอดมิน ลบผู้ใช้ |
| **View** | `admin_manage_users` |
| **URL** | `/custom-admin/users/` (name: `admin_manage_users`) |

**extends:** base (หรือ admin)  
**include:** ไม่มี  

**Form:**
- ลบผู้ใช้: `method="post"` `action="{% url 'volunteer_app:admin_delete_user' user.pk %}"` → View: `admin_delete_user` → URL: `/custom-admin/user/<pk>/delete/`

---

### 1.26 admin_edit_user.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | แก้ไขผู้ใช้ (ชื่อ, สิทธิ์ staff/superuser, roles ฯลฯ) |
| **View** | `admin_edit_user` |
| **URL** | `/custom-admin/user/<int:pk>/edit/` (name: `admin_edit_user`) |

**extends:** base (หรือ admin)  
**include:** ไม่มี  

**Form:**
- แก้ไขผู้ใช้: `method="post"` (action = current URL) → View: `admin_edit_user`

---

### 1.27 admin_user_hours.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | ดูชั่วโมงจิตอาสาของผู้ใช้ + ลบ QR scan (ปรับชั่วโมง) |
| **View** | `admin_view_user_hours` |
| **URL** | `/custom-admin/user/<user_id>/hours/` (name: `admin_view_user_hours`) |

**extends:** base (หรือ admin)  
**include:** ไม่มี  

**Form:**
- ลบ QR scan: `method="post"` `action="{% url 'volunteer_app:admin_delete_qr_scan' scan.pk %}"` → View: `admin_delete_qr_scan`

---

### 1.28 admin_add_hours.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | เพิ่มชั่วโมงจิตอาสาให้ผู้ใช้ (เลือก user + activity) |
| **View** | `admin_add_volunteer_hours` |
| **URL** | `/custom-admin/hours/add/` (name: `admin_add_volunteer_hours`) |

**extends:** `base.html`  
**include:** ไม่มี  

**Form:**
- เพิ่มชั่วโมง: `method="post"` (action = current URL) → View: `admin_add_volunteer_hours`  
  - fields: user_id, activity_id, csrf_token

---

### 1.29 404.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | หน้า Not Found (404) |
| **View** | `error_404` (handler404) |
| **URL** | ใช้เมื่อเกิด 404 ทั่วทั้งไซต์ |

**extends:** `base.html`  
**include:** ไม่มี  

**Form:** ไม่มี

---

### 1.30 500.html
| รายการ | รายละเอียด |
|--------|-------------|
| **หน้าที่** | หน้า Server Error (500) |
| **View** | `error_500` (handler500) |
| **URL** | ใช้เมื่อเกิด 500 ทั่วทั้งไซต์ |

**extends:** `base.html`  
**include:** ไม่มี  

**Form:** ไม่มี

---

## 2. ความสัมพันธ์ extends / include

### โครงสร้าง extends
- **ฐาน:** `base.html` (ไม่มี extends)
- **extends base.html:**  
  index, registration/login, registration/register, profile, edit_profile, change_password, activities, activity_detail, create_activity, qr_scan, qr_confirm_result, ideas_list, propose_idea, notifications, groups, create_group, group_detail, admin_login, admin_dashboard, admin_manage_activities, admin_edit_activity, admin_manage_ideas, admin_manage_users, admin_edit_user, admin_user_hours, admin_add_hours, 404, 500

### Include
- **base.html** → `{% include "chatbot_widget.html" %}` (เมื่อ user login และไม่ใช่หน้า admin)
- **chatbot_widget.html** ไม่ extend ใคร (เป็น partial)

---

## 3. Form action, method และ Backend View

สรุปเฉพาะ form ที่ส่งข้อมูลไป backend (POST/GET ที่มีผลต่อข้อมูล):

| Template | Form เรื่อง | Method | Action / URL | View |
|----------|-------------|--------|--------------|------|
| base.html | Logout | POST | volunteer_app:logout | logout_view |
| index.html | โหวตไอเดีย | POST | vote_idea (pk) | vote_idea |
| registration/login.html | Login | POST | (current) | login_view |
| registration/register.html | สมัครสมาชิก | POST | (current) | register |
| edit_profile.html | แก้ไขโปรไฟล์ | POST | (current) | edit_profile |
| change_password.html | เปลี่ยนรหัสผ่าน | POST | (current) | change_password |
| activities.html | ค้นหา/กรอง | GET | (current) | activities |
| activity_detail.html | สมัครกิจกรรม | POST | activity_signup (pk) | activity_signup |
| create_activity.html | สร้างกิจกรรม | POST | (current) | create_activity |
| qr_scan.html | อัปโหลดรูป QR | POST (fetch) | qr_upload | qr_upload |
| qr_scan.html | ยืนยันโทเค็น | POST (fetch) | qr_verify | qr_verify |
| ideas_list.html | ค้นหา | GET | (current) | idea_list |
| ideas_list.html | โหวตไอเดีย | POST | vote_idea (pk) | vote_idea |
| propose_idea.html | เสนอไอเดีย | POST | (current) | propose_idea |
| notifications.html | อ่านทั้งหมด | POST | notification_mark_all | notification_mark_all |
| notifications.html | อ่านแล้ว (รายการ) | POST | notification_mark_read (pk) | notification_mark_read |
| groups.html | เข้าร่วมกลุ่ม | POST | join_group (pk) | join_group |
| create_group.html | สร้างกลุ่ม | POST | (current) | create_group |
| group_detail.html | เข้าร่วม / เชิญ / โพสต์ | POST | (current = group_detail) | group_detail |
| admin_login.html | Admin login | POST | admin_login | admin_login |
| admin_dashboard.html | อนุมัติ/ปฏิเสธไอเดีย, ลบ QR scan | POST | admin_approve_idea, admin_reject_idea, admin_delete_qr_scan | ตาม name |
| admin_manage_activities.html | ลบกิจกรรม | POST | admin_delete_activity (pk) | admin_delete_activity |
| admin_edit_activity.html | แก้ไขกิจกรรม | POST | (current) | admin_edit_activity |
| admin_manage_ideas.html | อนุมัติ/ปฏิเสธไอเดีย | POST | admin_approve_idea, admin_reject_idea | ตาม name |
| admin_manage_users.html | ลบผู้ใช้ | POST | admin_delete_user (pk) | admin_delete_user |
| admin_edit_user.html | แก้ไขผู้ใช้ | POST | (current) | admin_edit_user |
| admin_user_hours.html | ลบ QR scan | POST | admin_delete_qr_scan (pk) | admin_delete_qr_scan |
| admin_add_hours.html | เพิ่มชั่วโมง | POST | (current) | admin_add_volunteer_hours |

---

## 4. JavaScript และการเรียก Endpoint/API

| ที่มา | Endpoint ที่เรียก | Method | ใช้ทำอะไร |
|-------|-------------------|--------|-----------|
| **qr_scanner_main.js** (ใน qr_scan.html) | `{% url 'volunteer_app:qr_verify' %}` = `/qr/verify/` | POST | หลังสแกน QR ส่ง token ไปยืนยัน |
| **qr_scan.html** (inline) | `{% url 'volunteer_app:qr_upload' %}` = `/qr/upload/` | POST | อัปโหลดรูป QR แล้วยืนยันโทเค็น |
| **qr_scan.html** (manual token) | เหมือน qr_verify | POST | กรอกโทเค็นมือแล้วยืนยัน |
| **chatbot_app.js** (ใน chatbot_widget) | `{% url 'volunteer_app:chatbot_api' %}` = `/chatbot/` | POST | ส่งข้อความ q รับคำตอบ (reply) |
| **group_detail.html** (inline) | `""` (current URL = group_detail) | POST | เข้าร่วมกลุ่ม, เชิญเพื่อน, โพสต์ข้อความ (AJAX, คาดหวัง JSON) |
| **ideas_list.html** (inline) | `form.action` = vote_idea URL | POST | โหวต/ยกเลิกโหวตแบบ AJAX อัปเดตคะแนน |

หมายเหตุ:  
- Check-in / Check-out ใช้ที่ URL `/check-in/` และ `/check-out/` (POST เท่านั้น) — ไม่มี template เฉพาะ; มักเรียกจากลิงก์หรือ QR ที่ชี้ไปที่ endpoint เหล่านี้หรือผ่าน flow ที่ decode token แล้วส่งไปที่ check_in/check_out view  
- การยืนยันผ่านลิงก์ `/qr/confirm/<token>/` เป็น GET ไปที่ `qr_confirm` แล้ว render `qr_confirm_result.html`

---

## 5. Flow สรุป Frontend → Backend

### 5.1 แผนภาพ URL → View → Template (หลัก)

```
/ (index)                    → views.index                    → index.html
/accounts/login/             → views.login_view                → registration/login.html
/accounts/register/          → views.register                  → registration/register.html
/profile/                    → views.profile                   → profile.html
/profile/edit/               → views.edit_profile              → edit_profile.html
/profile/change-password/    → views.change_password           → change_password.html
/activities/                 → views.activities                → activities.html
/activity/<pk>/              → views.activity_detail          → activity_detail.html
/activity/create/            → views.create_activity           → create_activity.html
/activity/<pk>/signup/       → views.activity_signup           (redirect, no template)
/qr/scan/                    → views.qr_scan_page              → qr_scan.html
/qr/verify/                  → views.qr_verify                 (JSON only)
/qr/upload/                  → views.qr_upload                 (JSON only)
/qr/confirm/<token>/         → views.qr_confirm                → qr_confirm_result.html
/check-in/                   → views.check_in                  (JSON only, POST)
/check-out/                  → views.check_out                 (JSON only, POST)
/notifications/              → views.notification_list         → notifications.html
/notifications/read-all/     → views.notification_mark_all     (POST, redirect/JSON)
/notifications/<pk>/read/    → views.notification_mark_read    (POST, redirect/JSON)
/chatbot/                    → views.chatbot_api               (JSON only, POST)
/ideas/                      → views.idea_list                 → ideas_list.html
/ideas/propose/              → views.propose_idea              → propose_idea.html
/ideas/<pk>/vote/            → views.vote_idea                (POST, redirect/JSON)
/groups/                     → views.groups_list               → groups.html
/group/create/                → views.create_group              → create_group.html
/group/<pk>/                 → views.group_detail              → group_detail.html
/group/<pk>/join/            → views.join_group                (POST, redirect/JSON)
/custom-admin/login/          → views.admin_login               → admin_login.html
/custom-admin/dashboard/      → views.admin_dashboard           → admin_dashboard.html
/custom-admin/activities/     → views.admin_manage_activities   → admin_manage_activities.html
/custom-admin/activity/<pk>/edit/   → views.admin_edit_activity   → admin_edit_activity.html
/custom-admin/activity/<pk>/delete/ → views.admin_delete_activity (POST, redirect)
/custom-admin/ideas/          → views.admin_manage_ideas        → admin_manage_ideas.html
/custom-admin/idea/<pk>/approve/    → views.admin_approve_idea  (POST)
/custom-admin/idea/<pk>/reject/    → views.admin_reject_idea    (POST)
/custom-admin/users/          → views.admin_manage_users        → admin_manage_users.html
/custom-admin/user/<pk>/edit/ → views.admin_edit_user          → admin_edit_user.html
/custom-admin/user/<pk>/delete/    → views.admin_delete_user    (POST)
/custom-admin/user/<id>/hours/     → views.admin_view_user_hours → admin_user_hours.html
/custom-admin/hours/add/     → views.admin_add_volunteer_hours  → admin_add_hours.html
/custom-admin/qr-scan/<pk>/delete/ → views.admin_delete_qr_scan (POST)
handler404                    → views.error_404                 → 404.html
handler500                    → views.error_500                 → 500.html
```

### 5.2 Flow การทำงานหลัก (สั้นๆ)

1. **ผู้ใช้ทั่วไป**  
   หน้าแรก (index) → กิจกรรม (activities, activity_detail) → สมัคร (activity_signup) → ยืนยันชั่วโมง (qr_scan → qr_verify / qr_upload หรือ qr_confirm). โปรไฟล์/แก้ไข/เปลี่ยนรหัสผ่านใช้ profile, edit_profile, change_password. แจ้งเตือนใช้ notifications + mark read/mark all.

2. **ไอเดีย**  
   ideas_list (GET ค้นหา) → propose_idea (POST ส่งไอเดีย) → vote_idea (POST โหวต/ยกเลิก, ได้จาก index หรือ ideas_list, บางที่ส่งแบบ AJAX).

3. **กลุ่ม**  
   groups_list → เข้าร่วม (join_group POST หรือจาก group_detail POST) → group_detail: เข้าร่วม/เชิญ/โพสต์ (POST ไปที่ group_detail, AJAX คืน JSON).

4. **แชทบอท**  
   เปิดจาก base (include chatbot_widget) → ส่งข้อความผ่าน JS ไป chatbot_api (POST /chatbot/) → ได้ JSON reply.

5. **แอดมิน**  
   admin_login → admin_dashboard → จัดการกิจกรรม/ไอเดีย/ผู้ใช้/ชั่วโมง ผ่าน form ต่างๆ ตามตารางด้านบน (approve/reject idea, delete activity/user/qr_scan, edit activity/user, add hours).

---

*เอกสารนี้อ้างอิงจากโครงสร้างใน volunteer_app (templates, views, urls) ณ เวลาที่วิเคราะห์*
