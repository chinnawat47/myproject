# ฟีเจอร์ Check-in / Check-out สำหรับกิจกรรมจิตอาสา

## สรุปการเปลี่ยนแปลง

เพิ่มฟีเจอร์ Check-in / Check-out เพื่อติดตามการเข้าร่วมกิจกรรมจริงและคำนวณชั่วโมงจิตอาสาจากเวลาจริงที่ทำงาน

## ไฟล์ที่แก้ไข

### 1. `volunteer_app/models.py`

#### เพิ่ม Model: `CheckInOut` (บรรทัด 147-186)
- **Fields:**
  - `activity`: ForeignKey to Activity
  - `user`: ForeignKey to User
  - `check_type`: CharField (choices: "checkin", "checkout")
  - `checked_at`: DateTimeField (auto_now_add)
  - `token`: CharField (เก็บ token ที่ใช้)
  - `calculated_hours`: DecimalField (ชั่วโมงที่คำนวณได้ - เติมเมื่อ check-out)
  - `ip_address`, `user_agent`, `device_id`: audit fields
  
- **Constraints:**
  - `unique_together`: ("activity", "user", "check_type") - 1 check-in และ 1 check-out ต่อ user ต่อ activity

#### อัปเดต Activity Model (บรรทัด 102-115)
- เพิ่ม method `checkin_token()`: สร้าง check-in token (expires 5 นาที)
- เพิ่ม method `checkout_token()`: สร้าง check-out token (expires 5 นาที)

#### อัปเดต User Model (บรรทัด 21-30)
- อัปเดต `total_hours()`: คำนวณชั่วโมงจากทั้ง QRScan (legacy) และ CheckInOut (ใหม่)
  - QRScan: ใช้ `activity.hours_reward`
  - CheckInOut: ใช้ `calculated_hours` จากเวลาจริง

### 2. `volunteer_app/utils.py`

#### เพิ่มฟังก์ชันสำหรับ Check-in/Check-out Tokens

- `make_checkin_token(activity_id, expires_in=300)`: สร้าง check-in token (expires 5 นาที)
- `make_checkout_token(activity_id, expires_in=300)`: สร้าง check-out token (expires 5 นาที)
- `verify_checkin_token(token)`: ตรวจสอบ check-in token → (True/False, activity_id)
- `verify_checkout_token(token)`: ตรวจสอบ check-out token → (True/False, activity_id)

**Token Format:**
- Check-in: `CHECKIN:{activity_id}:{expiry_ts}:{sig_hex}` (base64 encoded)
- Check-out: `CHECKOUT:{activity_id}:{expiry_ts}:{sig_hex}` (base64 encoded)

### 3. `volunteer_app/views.py`

#### เพิ่ม Views

**`check_in(request)`** (บรรทัด 530-625)
- **Method:** POST only
- **Authentication:** @login_required
- **Flow:**
  1. ตรวจสอบ token (verify_checkin_token)
  2. ตรวจสอบ activity exists และไม่ใช่ cancelled
  3. ตรวจสอบ user สมัครกิจกรรมแล้ว (ActivitySignup exists)
  4. สร้าง CheckInOut record (check_type="checkin") - atomic transaction
  5. ส่ง notification
  6. Return JSON response

**`check_out(request)`** (บรรทัด 628-750)
- **Method:** POST only
- **Authentication:** @login_required
- **Flow:**
  1. ตรวจสอบ token (verify_checkout_token)
  2. ตรวจสอบ activity exists และไม่ใช่ cancelled
  3. ตรวจสอบ user สมัครกิจกรรมแล้ว
  4. ตรวจสอบ user ได้ check-in แล้ว
  5. สร้าง CheckInOut record (check_type="checkout") - atomic transaction
  6. คำนวณชั่วโมงจากเวลาจริง (checkout.checked_at - checkin.checked_at)
  7. ถ้าเวลาน้อยกว่า 0.1 ชั่วโมง (6 นาที) → ใช้ activity.hours_reward เป็น fallback
  8. อัปเดต ActivitySignup.status = "attended"
  9. ส่ง notification
  10. Return JSON response

**อัปเดต `activity_detail(request, pk)`** (บรรทัด 274-320)
- เพิ่มการสร้าง QR codes สำหรับ check-in และ check-out
- ส่ง checkin_token, checkout_token, checkin_qr_b64, checkout_qr_b64 ไปยัง template

### 4. `volunteer_app/urls.py`

#### เพิ่ม URLs (บรรทัด 20-22)
- `path("check-in/", views.check_in, name="check_in")`
- `path("check-out/", views.check_out, name="check_out")`

## การทำงานของระบบ

### Workflow

```
1. User สมัครกิจกรรม (ActivitySignup)
   └─ status: "requested" / "confirmed" / "waitlist"

2. User Check-in (CheckInOut, check_type="checkin")
   ├─ ต้องสมัครกิจกรรมก่อน
   ├─ Token expires ใน 5 นาที
   ├─ 1 user ต่อ 1 activity: check-in ได้ครั้งเดียว
   └─ ส่ง notification "Check-in สำเร็จ"

3. User Check-out (CheckInOut, check_type="checkout")
   ├─ ต้อง check-in ก่อน
   ├─ Token expires ใน 5 นาที
   ├─ 1 user ต่อ 1 activity: check-out ได้ครั้งเดียว
   ├─ คำนวณชั่วโมงจากเวลาจริง (checkout - checkin)
   ├─ ถ้าเวลาน้อยกว่า 6 นาที → ใช้ activity.hours_reward
   ├─ อัปเดต ActivitySignup.status = "attended"
   └─ ส่ง notification "Check-out สำเร็จ"

4. คำนวณชั่วโมงจิตอาสา (User.total_hours())
   ├─ QRScan (legacy): sum(activity.hours_reward)
   └─ CheckInOut (new): sum(calculated_hours) จาก check-out records
```

### การคำนวณชั่วโมง

```python
# ตัวอย่าง
checkin_time = 2024-01-15 09:00:00
checkout_time = 2024-01-15 11:30:00
time_diff = 2.5 hours

if time_diff >= 0.1 hours (6 minutes):
    calculated_hours = 2.5 hours
else:
    calculated_hours = activity.hours_reward (fallback)
```

### Token Security

- **Expiration:** 5 นาที (300 วินาที)
- **Signature:** HMAC-SHA256
- **Format:** Base64 URL-safe encoded
- **Type Separation:** CHECKIN และ CHECKOUT ใช้ token format แยกกัน

### Database Constraints

- **Unique Constraint:** (activity, user, check_type)
  - ป้องกันการ check-in/check-out ซ้ำ
  - 1 check-in และ 1 check-out ต่อ user ต่อ activity

- **Atomic Transactions:** ใช้ `transaction.atomic()` ป้องกัน race condition

## Migration

สร้าง migration file:

```bash
python manage.py makemigrations volunteer_app --name add_checkinout
python manage.py migrate
```

## API Endpoints

### POST `/check-in/`

**Request:**
```json
{
  "token": "CHECKIN_TOKEN_HERE"
}
```

**Response (Success):**
```json
{
  "ok": true,
  "code": "checkin_success",
  "message": "Check-in สำเร็จ!",
  "activity": {
    "id": 1,
    "title": "กิจกรรมจิตอาสา",
    ...
  },
  "checked_in_at": "2024-01-15T09:00:00Z"
}
```

**Response (Error):**
```json
{
  "ok": false,
  "code": "already_checked_in",
  "message": "คุณได้ check-in กิจกรรมนี้แล้วเมื่อ...",
  "help": "..."
}
```

### POST `/check-out/`

**Request:**
```json
{
  "token": "CHECKOUT_TOKEN_HERE"
}
```

**Response (Success):**
```json
{
  "ok": true,
  "code": "checkout_success",
  "message": "Check-out สำเร็จ! คุณได้รับ 2.50 ชั่วโมงจิตอาสา",
  "activity": {...},
  "checked_in_at": "2024-01-15T09:00:00Z",
  "checked_out_at": "2024-01-15T11:30:00Z",
  "calculated_hours": 2.50,
  "time_worked_minutes": 150
}
```

## การใช้งาน

### สำหรับ Admin

1. ไปที่หน้ารายละเอียดกิจกรรม (`/activity/<id>/`)
2. จะเห็น QR codes 3 แบบ:
   - QR Code เดิม (สำหรับ QRScan - legacy)
   - QR Code Check-in (สำหรับ check-in)
   - QR Code Check-out (สำหรับ check-out)

### สำหรับ User

1. **Check-in:**
   - สแกน QR Code Check-in
   - หรือเปิด URL: `/check-in/?token=CHECKIN_TOKEN`
   - ระบบจะบันทึกเวลา check-in

2. **Check-out:**
   - สแกน QR Code Check-out
   - หรือเปิด URL: `/check-out/?token=CHECKOUT_TOKEN`
   - ระบบจะคำนวณชั่วโมงจากเวลาจริง
   - ส่ง notification พร้อมจำนวนชั่วโมงที่ได้รับ

## ข้อควรระวัง

1. **Token Expiration:** QR tokens มีอายุ 5 นาที ต้องใช้ทันที
2. **Check-in Required:** ต้อง check-in ก่อนจึงจะ check-out ได้
3. **One-time Only:** แต่ละ user สามารถ check-in/check-out ได้ครั้งเดียวต่อ activity
4. **Hours Calculation:** ถ้าเวลาน้อยกว่า 6 นาที จะใช้ activity.hours_reward เป็น fallback
5. **Legacy Support:** QRScan ยังคงทำงานได้ตามปกติ (ไม่กระทบระบบเดิม)

## Testing

### Test Cases

1. ✅ Check-in สำเร็จ (user สมัครแล้ว)
2. ✅ Check-in ซ้ำ (return error)
3. ✅ Check-out โดยไม่ check-in (return error)
4. ✅ Check-out สำเร็จ (คำนวณชั่วโมงถูกต้อง)
5. ✅ Check-out ซ้ำ (return error)
6. ✅ Token หมดอายุ (return error)
7. ✅ Token ไม่ถูกต้อง (return error)
8. ✅ Activity cancelled (return error)
9. ✅ User ไม่ได้สมัคร (return error)
10. ✅ Hours calculation (เวลาจริง vs fallback)

## สรุป

- ✅ แยก Check-in และ Check-out ชัดเจน
- ✅ ใช้ QR token คนละแบบ (CHECKIN / CHECKOUT)
- ✅ Token มีอายุ 5 นาที
- ✅ 1 user ต่อ 1 activity: check-in/check-out ได้ครั้งเดียว
- ✅ คำนวณชั่วโมงจากเวลาจริง
- ✅ ไม่กระทบ QRScan เดิม
- ✅ Fallback ใช้ activity.hours_reward
- ✅ ใช้ transaction.atomic() ป้องกัน race condition
- ✅ ส่ง notification เมื่อ check-in/check-out สำเร็จ

