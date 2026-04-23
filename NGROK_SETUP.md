# คู่มือการตั้งค่า Django สำหรับใช้งานผ่าน ngrok (iPhone/HTTPS)

## สรุปการแก้ไข

การแก้ไขนี้ทำให้ Django app สามารถใช้งานผ่าน ngrok บน iPhone ได้ โดยไม่กระทบการทำงานบน localhost และยังคงความปลอดภัย (CSRF, Auth)

## ไฟล์ที่แก้ไข

### 1. `volunteer_system/settings.py`

#### บรรทัด 14-17: ALLOWED_HOSTS
- **เดิม**: รองรับ `.ngrok-free.app` อยู่แล้ว
- **ไม่ต้องแก้**: ใช้ค่าเดิมได้

#### บรรทัด 19-35: เพิ่ม CSRF_TRUSTED_ORIGINS และ Cookie Settings
- **เพิ่ม**: `CSRF_TRUSTED_ORIGINS` เพื่อระบุ domain ที่ Django ไว้ใจสำหรับ CSRF
- **เพิ่ม**: Cookie settings (`SESSION_COOKIE_SAMESITE`, `CSRF_COOKIE_SAMESITE`, `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_SECURE`)
- **เพิ่ม**: `SECURE_PROXY_SSL_HEADER` เพื่อให้ Django รู้ว่า request มาจาก HTTPS (ngrok)

### 2. `volunteer_app/templates/base.html`

#### บรรทัด 46-47: เพิ่ม CSRF Token Meta Tag
- **เพิ่ม**: `{% csrf_token %}` และ `<meta name="csrf-token" content="{{ csrf_token }}">`
- **เหตุผล**: เพื่อให้ JavaScript สามารถอ่าน CSRF token ได้ (รองรับ Safari/iOS)

### 3. `volunteer_app/static/volunteer_app/js/qr_scanner_main.js`

#### บรรทัด 99-132: ปรับปรุง getCookie function
- **เพิ่ม**: Fallback mechanism 3 ระดับ
  1. อ่านจาก cookie (วิธีหลัก)
  2. อ่านจาก meta tag (fallback สำหรับ Safari)
  3. อ่านจาก hidden input (fallback สำหรับ Django form)

### 4. `volunteer_app/templates/qr_scan.html`

#### บรรทัด 299-332: ปรับปรุง getCookie function
- **เพิ่ม**: Fallback mechanism เหมือนกับ qr_scanner_main.js

### 5. `volunteer_app/static/volunteer_app/js/chatbot_app.js`

#### บรรทัด 155-188: ปรับปรุง getCookie function
- **เพิ่ม**: Fallback mechanism เหมือนกับไฟล์อื่นๆ

## วิธีใช้งาน

### ขั้นตอนที่ 1: ตั้งค่า ngrok

1. เปิด ngrok tunnel:
```bash
ngrok http 8000
```

2. คัดลอก HTTPS URL ที่ได้ (เช่น `https://372e8fe832c8.ngrok-free.app`)

### ขั้นตอนที่ 2: ตั้งค่า Environment Variables

สร้างหรือแก้ไขไฟล์ `.env` ในโฟลเดอร์โปรเจกต์:

```env
# สำหรับ ngrok (HTTPS)
CSRF_TRUSTED_ORIGINS=https://372e8fe832c8.ngrok-free.app
SESSION_COOKIE_SAMESITE=None
CSRF_COOKIE_SAMESITE=None
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# สำหรับ localhost (HTTP) - ใช้ค่า default ไม่ต้องตั้ง
# หรือตั้งเป็น:
# SESSION_COOKIE_SAMESITE=Lax
# CSRF_COOKIE_SAMESITE=Lax
# SESSION_COOKIE_SECURE=False
# CSRF_COOKIE_SECURE=False
```

**หมายเหตุ**: 
- เปลี่ยน `372e8fe832c8.ngrok-free.app` เป็น ngrok domain ของคุณ
- ถ้า ngrok domain เปลี่ยน ต้องอัปเดต `CSRF_TRUSTED_ORIGINS` ใหม่

### ขั้นตอนที่ 3: รัน Django Server

```bash
python manage.py runserver
```

### ขั้นตอนที่ 4: ทดสอบบน iPhone

1. เปิด Safari บน iPhone
2. ไปที่ URL: `https://372e8fe832c8.ngrok-free.app` (ใช้ domain ของคุณ)
3. ล็อกอินและทดสอบฟังก์ชันสแกน QR Code

## การทำงานบน Localhost (ไม่เปลี่ยนแปลง)

- การทำงานบน `http://localhost:8000` ยังคงทำงานเหมือนเดิม
- ไม่ต้องตั้งค่า environment variables สำหรับ localhost
- ใช้ค่า default (`Lax`, `Secure=False`)

## ความปลอดภัย

### ✅ สิ่งที่ยังคงความปลอดภัย:

1. **CSRF Protection**: ยังคงทำงานปกติ (ไม่ใช้ `@csrf_exempt`)
2. **Authentication**: ยังคงทำงานปกติ
3. **Session Security**: ใช้ `Secure=True` เมื่อใช้ HTTPS (ngrok)
4. **Cookie SameSite**: ใช้ `None` สำหรับ ngrok (HTTPS) และ `Lax` สำหรับ localhost (HTTP)

### ⚠️ ข้อควรระวัง:

1. **CSRF_TRUSTED_ORIGINS**: ต้องระบุ domain เต็มๆ (Django ไม่รองรับ wildcard)
   - ✅ ถูกต้อง: `https://372e8fe832c8.ngrok-free.app`
   - ❌ ผิด: `https://*.ngrok-free.app`

2. **Cookie SameSite=None**: ต้องใช้กับ `Secure=True` เสมอ (HTTPS เท่านั้น)
   - ✅ ถูกต้อง: `SameSite=None; Secure` (สำหรับ ngrok)
   - ❌ ผิด: `SameSite=None` โดยไม่มี `Secure` (จะไม่ทำงาน)

3. **ngrok Domain**: ngrok free plan จะเปลี่ยน domain ทุกครั้งที่ restart
   - ต้องอัปเดต `CSRF_TRUSTED_ORIGINS` ทุกครั้งที่ domain เปลี่ยน
   - หรือใช้ ngrok paid plan ที่มี static domain

## การแก้ปัญหา (Troubleshooting)

### ปัญหา: CSRF verification failed

**สาเหตุที่เป็นไปได้:**
1. `CSRF_TRUSTED_ORIGINS` ไม่ได้ตั้งค่าหรือตั้งค่าผิด
2. Cookie settings ไม่ถูกต้อง (`SameSite=None` แต่ไม่มี `Secure=True`)
3. ngrok domain เปลี่ยนแล้วแต่ไม่ได้อัปเดต

**วิธีแก้:**
1. ตรวจสอบ `.env` ว่ามี `CSRF_TRUSTED_ORIGINS` ที่ถูกต้อง
2. ตรวจสอบว่า `CSRF_COOKIE_SECURE=True` และ `CSRF_COOKIE_SAMESITE=None` สำหรับ ngrok
3. Restart Django server หลังจากแก้ไข `.env`

### ปัญหา: JavaScript อ่าน CSRF token ไม่ได้ (Safari/iOS)

**สาเหตุที่เป็นไปได้:**
1. CSRF cookie ไม่ถูกสร้าง
2. Safari block cookies

**วิธีแก้:**
1. ตรวจสอบว่า `base.html` มี `{% csrf_token %}` และ meta tag
2. ตรวจสอบว่า `getCookie` function มี fallback mechanism
3. ตรวจสอบ Console ใน Safari Developer Tools

### ปัญหา: กล้องไม่ทำงานบน iPhone

**สาเหตุที่เป็นไปได้:**
1. ไม่ได้อนุญาตให้ใช้กล้อง
2. ใช้ HTTP แทน HTTPS (Safari ต้องการ HTTPS สำหรับ camera API)

**วิธีแก้:**
1. ใช้ ngrok HTTPS URL (ไม่ใช่ HTTP)
2. อนุญาตให้ใช้กล้องใน Safari Settings

## Production Deployment

สำหรับ production ในอนาคต:

1. **ใช้ Static Domain**: ใช้ domain ที่ไม่เปลี่ยน (ไม่ใช่ ngrok free)
2. **ตั้งค่า Environment Variables**: ตั้งค่าใน production server
3. **HTTPS**: ใช้ HTTPS certificate จริง (Let's Encrypt)
4. **Security Headers**: เพิ่ม security headers อื่นๆ (HSTS, CSP, etc.)

## สรุป

การแก้ไขนี้:
- ✅ รองรับทั้ง localhost และ ngrok
- ✅ ไม่กระทบการทำงานเดิมบน PC
- ✅ ยังคงความปลอดภัย (CSRF, Auth)
- ✅ รองรับ Safari/iOS
- ✅ ไม่ใช้ `@csrf_exempt`
- ✅ ใช้ environment variables สำหรับ configuration

