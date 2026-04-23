# 📧 ตั้งค่า Email สำหรับ @ubu.ac.th

## สำหรับอีเมลมหาวิทยาลัย (@ubu.ac.th)

### วิธีที่ 1: ใช้ Gmail (แนะนำ - ง่ายที่สุด)

แม้คุณจะมีอีเมล @ubu.ac.th แต่คุณสามารถใช้ Gmail ในการส่งอีเมลได้:

#### ขั้นตอน:

1. **สร้าง Gmail Account** (ถ้ายังไม่มี) หรือใช้ Gmail ที่มีอยู่

2. **สร้าง App Password**:
   - ไปที่: https://myaccount.google.com/apppasswords
   - เปิด **2-Step Verification** ก่อน
   - สร้าง App Password → คัดลอกรหัส 16 ตัวอักษร

3. **สร้างไฟล์ `.env`** ในโฟลเดอร์ `C:\project\myproject\`:

```env
# Email Configuration - Gmail
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
DEFAULT_FROM_EMAIL=noreply@ubu.ac.th
```

**หมายเหตุ:** 
- `EMAIL_HOST_USER` = Gmail ของคุณ
- `EMAIL_HOST_PASSWORD` = App Password
- `DEFAULT_FROM_EMAIL` = ตั้งเป็น noreply@ubu.ac.th หรืออีเมลที่ต้องการ

---

### วิธีที่ 2: ใช้ SMTP Server ของมหาวิทยาลัย (ถ้ามี)

ติดต่อฝ่าย IT ของมหาวิทยาลัยเพื่อขอข้อมูล SMTP server:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.ubu.ac.th
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=chinnawat.ng.66@ubu.ac.th
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@ubu.ac.th
```

---

### วิธีที่ 3: ใช้ Outlook (รองรับ @ubu.ac.th)

ถ้ามหาวิทยาลัยใช้ Microsoft 365/Outlook:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=chinnawat.ng.66@ubu.ac.th
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=chinnawat.ng.66@ubu.ac.th
```

---

## 📝 ตัวอย่างไฟล์ .env ที่สมบูรณ์

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Email Configuration - Gmail (ส่งอีเมลไปที่ @ubu.ac.th)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
DEFAULT_FROM_EMAIL=noreply@ubu.ac.th

# QR Token Secret
QR_SECRET=your-qr-secret-key
```

---

## ✅ การทดสอบ

### ทดสอบการส่งอีเมล:

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail

send_mail(
    subject='ทดสอบการส่งอีเมล',
    message='นี่คือข้อความทดสอบ',
    from_email='noreply@ubu.ac.th',
    recipient_list=['chinnawat.ng.66@ubu.ac.th'],
    fail_silently=False,
)
```

### ทดสอบผ่านเว็บ:

1. ไปที่: http://127.0.0.1:8000/accounts/register/
2. สมัครสมาชิกด้วยอีเมล `chinnawat.ng.66@ubu.ac.th`
3. ตรวจสอบอีเมลที่ `chinnawat.ng.66@ubu.ac.th`
4. คลิกลิงก์ยืนยันในอีเมล
5. หลังจากยืนยันแล้วจึงจะสามารถ login และใช้งานได้

---

## ⚠️ หมายเหตุสำคัญ

1. **ไฟล์ .env อย่า commit ลง Git** (มีใน .gitignore แล้ว)
2. **ใช้ App Password สำหรับ Gmail** (ไม่ใช่รหัสผ่านปกติ)
3. **ตรวจสอบ Spam folder** ถ้าไม่เห็นอีเมล
4. **สำหรับ localhost** - ต้องใช้ Gmail หรือ SMTP server ที่รองรับการส่งจาก localhost

---

## 🔧 แก้ปัญหา

### "SMTPAuthenticationError"
→ ใช้ App Password แทนรหัสผ่านปกติ (สำหรับ Gmail)

### "Connection refused"
→ ตรวจสอบ Firewall หรือ Network
→ ลองเปลี่ยน port เป็น 465 และ EMAIL_USE_TLS=False, EMAIL_USE_SSL=True

### อีเมลไปอยู่ใน Spam
→ ใช้บริการ email service ที่มี reputation ดี (SendGrid, Mailgun)
→ ตั้งค่า SPF/DKIM records

---

## 🎯 สรุป

**สำหรับ localhost + @ubu.ac.th:**
- ใช้ Gmail + App Password (แนะนำ)
- ตั้ง `DEFAULT_FROM_EMAIL=noreply@ubu.ac.th`
- อีเมลจะถูกส่งไปที่ `chinnawat.ng.66@ubu.ac.th` ตามที่ผู้ใช้กรอกตอนสมัคร

