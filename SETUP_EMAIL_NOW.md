# 🚀 ตั้งค่า Email ให้ส่งอีเมลยืนยันไปที่ Gmail ของคุณ

## ขั้นตอนที่ 1: สร้าง Gmail App Password

1. ไปที่: https://myaccount.google.com/apppasswords
2. **เปิด 2-Step Verification ก่อน** (ถ้ายังไม่เปิด):
   - ไปที่: https://myaccount.google.com/security
   - เปิด "2-Step Verification"
3. กลับไปที่ App Passwords:
   - เลือก **Mail**
   - เลือก **Other (Custom name)**
   - ตั้งชื่อ: "Volunteer System"
   - คัดลอกรหัส 16 ตัวอักษร (เช่น: `abcd efgh ijkl mnop`)

## ขั้นตอนที่ 2: สร้างไฟล์ .env

สร้างไฟล์ `.env` ในโฟลเดอร์ `C:\project\myproject\` (ถ้ายังไม่มี):

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

**เปลี่ยน:**
- `your-gmail@gmail.com` = Gmail ของคุณที่ใช้สร้าง App Password
- `xxxx xxxx xxxx xxxx` = App Password 16 ตัวอักษรที่ได้จากขั้นตอนที่ 1

## ขั้นตอนที่ 3: Restart Server

```bash
# หยุด server (Ctrl+C)
python manage.py runserver
```

## ขั้นตอนที่ 4: ทดสอบ

1. ไปที่: http://127.0.0.1:8000/accounts/register/
2. สมัครสมาชิกด้วยอีเมล `chinnawat.ng.66@ubu.ac.th`
3. ระบบจะส่งอีเมลยืนยันไปที่ `chinnawat.ng.66@ubu.ac.th`
4. ตรวจสอบ Gmail inbox ของคุณ
5. คลิกลิงก์ยืนยันในอีเมล

---

## ⚠️ หมายเหตุสำคัญ

1. **ใช้ App Password ไม่ใช่รหัสผ่าน Gmail ปกติ**
2. **ตรวจสอบ Spam folder** ถ้าไม่เห็นอีเมล
3. **ไฟล์ .env อย่า commit ลง Git**

---

## 🔧 แก้ปัญหา

### "SMTPAuthenticationError"
→ ใช้ App Password แทนรหัสผ่านปกติ

### อีเมลไปอยู่ใน Spam
→ ตรวจสอบ Spam folder
→ ใช้ Gmail ที่มี reputation ดี

