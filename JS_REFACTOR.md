# การแยก JavaScript ออกจาก Django Templates

เอกสารนี้อธิบายการย้าย JavaScript ที่เคยเขียน inline ใน template ไปไว้ในไฟล์ภายใต้ `volunteer_app/static/volunteer_app/js/` และการปรับ template ให้โหลด JS ผ่าน `{% static %}`

---

## 1. qr_scan.html

### โค้ดเดิมอยู่ตรงไหน

- **ตำแหน่งใน template:** ภายใน `{% block content %}` หลัง `</main>` มี 3 บล็อก `<script>` แบบ inline:
  1. **บล็อกที่ 1:** เรียก `initQrScanner("{% url 'volunteer_app:qr_verify' %}");` (ประมาณ 3 บรรทัด)
  2. **บล็อกที่ 2:** IIFE สำหรับฟอร์มอัปโหลดรูป QR — ฟังก์ชัน `getCookie`, `showUploadLoading`, `showUploadSuccess`, `showUploadError`, event ลูกศร image preview / remove / submit, ใช้ `uploadUrl = "{% url 'volunteer_app:qr_upload' %}"` (ประมาณ 230 บรรทัด)
  3. **บล็อกที่ 3:** IIFE สำหรับฟอร์มกรอกโทเค็นมือ — `errorMessages`, `getCookie`, `showLoading`, `showSuccess`, `showError`, submit handler, retry และ contact-admin (ประมาณ 165 บรรทัด)

### ย้ายไปไฟล์ไหน

| โค้ดเดิม (ใน template) | ไฟล์ใหม่ |
|------------------------|----------|
| บล็อกที่ 1 (init QrScanner) | ยังคงใช้ `qr_scanner_main.js` เหมือนเดิม แต่ตอนนี้ถูกเรียกจาก `qr_scan_page.js` ตาม config |
| บล็อกที่ 2 (QR Upload form) | `volunteer_app/static/volunteer_app/js/qr_scan_page.js` — ฟังก์ชัน `initQrUploadForm(uploadUrl)` |
| บล็อกที่ 3 (Manual token form) | `volunteer_app/static/volunteer_app/js/qr_scan_page.js` — ฟังก์ชัน `initQrManualToken(verifyUrl)` |

- **Config จาก template ส่งอย่างไร:** ไม่ใช้ inline script — ใช้ data attributes บน `<main>`:
  - `data-qr-scan-page`
  - `data-verify-url="{% url 'volunteer_app:qr_verify' %}"`
  - `data-upload-url="{% url 'volunteer_app:qr_upload' %}"`
- **การโหลด:** Template โหลด `qr_scanner_main.js` แล้วตามด้วย `qr_scan_page.js`; `qr_scan_page.js` จะหา element ที่มี `[data-qr-scan-page]` แล้วอ่าน `data-verify-url` / `data-upload-url` เพื่อเรียก `initQrScanner`, `initQrUploadForm`, `initQrManualToken`

### โค้ดก่อนและหลัง (สรุป)

**ก่อน (ใน qr_scan.html):**
```html
<main class="min-h-full ...">
  ...
</main>

<script src="{% static 'volunteer_app/js/qr_scanner_main.js' %}"></script>
<script>
  initQrScanner("{% url 'volunteer_app:qr_verify' %}");
</script>
<script>
  (function(){
    const uploadForm = document.getElementById('qr-upload-form');
    const uploadUrl = "{% url 'volunteer_app:qr_upload' %}";
    // ... getCookie, showUploadLoading, showUploadSuccess, showUploadError ...
    // ... image preview, remove, form submit fetch(uploadUrl) ...
  })();
</script>
<script>
  (function(){
    const form = document.getElementById('manual-token-form');
    const verifyUrl = "{% url 'volunteer_app:qr_verify' %}";
    // ... errorMessages, getCookie, showLoading, showSuccess, showError ...
    // ... form submit fetch(verifyUrl), retry btn, contact-admin btn ...
  })();
</script>
{% endblock %}
```

**หลัง (ใน qr_scan.html):**
```html
<main class="min-h-full ..."
      data-qr-scan-page
      data-verify-url="{% url 'volunteer_app:qr_verify' %}"
      data-upload-url="{% url 'volunteer_app:qr_upload' %}">
  ...
</main>

<script src="{% static 'volunteer_app/js/qr_scanner_main.js' %}"></script>
<script src="{% static 'volunteer_app/js/qr_scan_page.js' %}"></script>
{% endblock %}
```

---

## 2. group_detail.html

### โค้ดเดิมอยู่ตรงไหน

- **ตำแหน่งใน template:** ภายใน `{% block content %}` ท้ายไฟล์ มี 1 บล็อก `<script>` แบบ inline (ประมาณ 115 บรรทัด):
  - ตัวแปร `csrftoken = '{{ csrf_token }}'` (ไม่ได้ใช้ใน fetch เพราะ FormData มี csrf จาก form อยู่แล้ว)
  - **เข้าร่วมกลุ่ม (AJAX):** หา form ที่มีปุ่ม `name="join_group"`, preventDefault, ส่ง FormData ไป `fetch("", { method: "POST", ... })`, ถ้า `data.ok` ให้เพิ่มสมาชิกใน `#members-list` แล้วลบ form และ alert
  - **เชิญเพื่อน (AJAX):** form `#inviteForm`, ส่งไป `fetch("", ...)`, แสดง `data.message` ใน `#inviteResult`, ถ้า ok ให้เพิ่มสมาชิกใน `#members-list`
  - **โพสต์ข้อความ (AJAX):** form `#postForm`, ส่งไป `fetch("", ...)`, ถ้า ok ให้สร้าง article แทรกที่ต้น `#posts-list` แล้ว reset form

### ย้ายไปไฟล์ไหน

| โค้ดเดิม (ใน template) | ไฟล์ใหม่ |
|------------------------|----------|
| ทั้งบล็อก script (join / invite / post) | `volunteer_app/static/volunteer_app/js/group_detail.js` |

- **Config:** ไม่ต้องส่งจาก template — ใช้ `fetch("")` (URL ปัจจุบัน) เหมือนเดิม และ CSRF มาจาก FormData ของ form ที่มี `{% csrf_token %}` อยู่แล้ว
- **การโหลด:** ท้าย `group_detail.html` มี `{% load static %}` และ `<script src="{% static 'volunteer_app/js/group_detail.js' %}"></script>`

### โค้ดก่อนและหลัง (สรุป)

**ก่อน (ใน group_detail.html):**
```html
  </div>
</div>

<script>
document.addEventListener("DOMContentLoaded", () => {
  const csrftoken = '{{ csrf_token }}';
  const joinForm = document.querySelector('form button[name="join_group"]')?.closest("form");
  if (joinForm) {
    joinForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(joinForm);
      const res = await fetch("", { method: "POST", headers: {"X-Requested-With": "XMLHttpRequest"}, body: formData });
      // ... handle data.ok, append to members-list, remove form, alert ...
    });
  }
  // ... inviteForm, postForm คล้ายกัน ...
});
</script>
{% endblock %}
```

**หลัง (ใน group_detail.html):**
```html
  </div>
</div>

{% load static %}
<script src="{% static 'volunteer_app/js/group_detail.js' %}"></script>
{% endblock %}
```

---

## 3. ideas_list.html

### โค้ดเดิมอยู่ตรงไหน

- **ตำแหน่งใน template:** ภายใน `{% block scripts %}` มี 1 บล็อก `<script>` แบบ inline (ประมาณ 75 บรรทัด):
  - เลือกทุก `.idea-vote-form`, ติด submit listener
  - preventDefault, อ่าน `data-idea-id`, ปุ่ม submit, input `name="action"`, csrf จาก form
  - `fetch(form.action, { method: "POST", ... body: new URLSearchParams(new FormData(form)) })`
  - ถ้า `data.ok`: อัปเดต `[data-idea-count='${ideaId}']`, สลับ action (vote/unvote) และเปลี่ยนข้อความ/สไตล์ปุ่ม

### ย้ายไปไฟล์ไหน

| โค้ดเดิม (ใน template) | ไฟล์ใหม่ |
|------------------------|----------|
| ทั้งบล็อก script (vote form AJAX) | `volunteer_app/static/volunteer_app/js/ideas_list.js` |

- **Config:** ไม่ต้องส่งจาก template — form มี `action="{% url 'volunteer_app:vote_idea' idea.pk %}"` และ csrf อยู่ใน form อยู่แล้ว; JS แค่ bind กับ `.idea-vote-form` และใช้ `form.action` กับ FormData
- **การโหลด:** ใน `{% block scripts %}` ใช้ `{{ block.super }}` แล้วตามด้วย `<script src="{% static 'volunteer_app/js/ideas_list.js' %}"></script>`

### โค้ดก่อนและหลัง (สรุป)

**ก่อน (ใน ideas_list.html):**
```html
{% block scripts %}
{{ block.super }}
<script>
  (function() {
    const voteForms = document.querySelectorAll(".idea-vote-form");
    voteForms.forEach(form => {
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const ideaId = form.dataset.ideaId;
        // ... fetch(form.action, ...), update count, toggle button text/class ...
      });
    });
  })();
</script>
{% endblock %}
```

**หลัง (ใน ideas_list.html):**
```html
{% block scripts %}
{{ block.super }}
<script src="{% static 'volunteer_app/js/ideas_list.js' %}"></script>
{% endblock %}
```

---

## สรุปไฟล์ที่เกี่ยวข้อง

| Template | ไฟล์ JS ที่เพิ่ม/ใช้ | หมายเหตุ |
|----------|------------------------|----------|
| `qr_scan.html` | `qr_scanner_main.js` (เดิม) + `qr_scan_page.js` (ใหม่) | ส่ง URL ผ่าน `data-verify-url`, `data-upload-url` บน `<main>` |
| `group_detail.html` | `group_detail.js` (ใหม่) | POST ไป URL ปัจจุบัน (`""`), CSRF จาก FormData |
| `ideas_list.html` | `ideas_list.js` (ใหม่) | ใช้ `form.action` และ FormData จาก form |

พฤติกรรมของหน้า (การยืนยัน QR, เข้าร่วม/เชิญ/โพสต์กลุ่ม, โหวตไอเดีย) เหมือนเดิม มีเพียงการย้ายโค้ดออกจาก template เพื่อให้โครงสร้างสะอาดและดูแลง่ายขึ้น
