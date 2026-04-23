/**
 * qr_scan_page.js
 * Handles QR upload form and manual token form on the QR scan page.
 * Expects container with data-verify-url and data-upload-url (e.g. <main data-verify-url="..." data-upload-url="...">).
 * Depends: qr_scanner_main.js (for initQrScanner).
 */
(function () {
  "use strict";

  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      var cookies = document.cookie.split(";");
      for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    if (!cookieValue && name === "csrftoken") {
      var metaTag = document.querySelector('meta[name="csrf-token"]');
      if (metaTag) cookieValue = metaTag.getAttribute("content");
    }
    if (!cookieValue && name === "csrftoken") {
      var csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
      if (csrfInput) cookieValue = csrfInput.value;
    }
    return cookieValue;
  }

  var ERROR_MESSAGES = {
    no_token: "โปรดกรอกหรือสแกน QR code ก่อน",
    invalid_token: "โทเค็นไม่ถูกต้องหรือหมดอายุแล้ว",
    activity_not_found: "ไม่พบกิจกรรมนี้ในระบบ",
    not_signed_up: "คุณยังไม่ได้สมัครกิจกรรมนี้",
    already_attended: "คุณยืนยันชั่วโมงกิจกรรมนี้แล้ว",
    database_error: "เกิดข้อผิดพลาดในการบันทึก ลองอีกครั้ง",
    unknown: "เกิดข้อผิดพลาดที่ไม่ทราบสาเหตุ",
  };

  function initQrUploadForm(uploadUrl) {
    var uploadForm = document.getElementById("qr-upload-form");
    var imageInput = document.getElementById("qr-image-input");
    var imagePreview = document.getElementById("image-preview");
    var previewImg = document.getElementById("preview-img");
    var removeImageBtn = document.getElementById("remove-image-btn");
    var uploadSubmitBtn = document.getElementById("qr-upload-submit");
    var resultDiv = document.getElementById("qr-result");
    var activityDetailsDiv = document.getElementById("activity-details");
    var errorHelpDiv = document.getElementById("error-help");

    if (!uploadForm || !uploadUrl) return;

    function showUploadLoading() {
      resultDiv.classList.remove("hidden");
      resultDiv.innerHTML =
        '<div class="flex flex-col items-center justify-center h-full">' +
        '<div class="mb-4"><div class="inline-block">' +
        '<svg class="animate-spin h-12 w-12 text-emerald-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">' +
        '<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>' +
        '<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>' +
        "</svg></div></div>' +
        '<p class="text-gray-600 font-medium">กำลังอ่าน QR code และยืนยัน...</p></div>';
      activityDetailsDiv.classList.add("hidden");
      errorHelpDiv.classList.add("hidden");
      uploadSubmitBtn.disabled = true;
    }

    function showUploadSuccess(data) {
      resultDiv.classList.add("hidden");
      activityDetailsDiv.classList.remove("hidden");
      errorHelpDiv.classList.add("hidden");

      if (data.activity) {
        var titleEl = document.getElementById("activity-title");
        var datetimeEl = document.getElementById("activity-datetime");
        var locationEl = document.getElementById("activity-location");
        if (titleEl) titleEl.textContent = data.activity.title;
        if (datetimeEl) {
          datetimeEl.innerHTML =
            '<svg class="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg> ' +
            (data.activity.datetime || "");
        }
        if (locationEl) {
          locationEl.innerHTML =
            '<svg class="w-4 h-4 mr-2 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path></svg> ' +
            (data.activity.location || "ไม่ระบุ");
        }
      }

      var hoursEl = document.getElementById("activity-hours");
      if (hoursEl) {
        if (data.calculated_hours !== undefined) {
          hoursEl.textContent = Number(data.calculated_hours).toFixed(2);
        } else if (data.hours_reward !== undefined) {
          hoursEl.textContent = data.hours_reward;
        } else {
          hoursEl.textContent = "0";
        }
      }

      uploadSubmitBtn.disabled = false;
      imageInput.value = "";
      imagePreview.classList.add("hidden");
      uploadSubmitBtn.disabled = true;
    }

    function showUploadError(data) {
      resultDiv.classList.add("hidden");
      activityDetailsDiv.classList.add("hidden");
      errorHelpDiv.classList.remove("hidden");
      var errorMsgEl = document.getElementById("error-message");
      var helpEl = document.getElementById("error-help-text");
      if (errorMsgEl) errorMsgEl.textContent = data.message || "เกิดข้อผิดพลาดในการอัปโหลด";
      if (helpEl) helpEl.textContent = data.help || "กรุณาลองใหม่หรือติดต่อผู้ดูแลระบบ";
      uploadSubmitBtn.disabled = false;
    }

    imageInput.addEventListener("change", function (e) {
      var file = e.target.files[0];
      if (!file) return;
      var allowedTypes = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"];
      if (allowedTypes.indexOf(file.type) === -1) {
        alert("รูปแบบไฟล์ไม่ถูกต้อง กรุณาใช้ไฟล์รูปภาพ (JPG, PNG, GIF, WEBP)");
        imageInput.value = "";
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        alert("ไฟล์ใหญ่เกินไป กรุณาเลือกรูปภาพที่มีขนาดไม่เกิน 10MB");
        imageInput.value = "";
        return;
      }
      var reader = new FileReader();
      reader.onload = function (ev) {
        previewImg.src = ev.target.result;
        imagePreview.classList.remove("hidden");
        uploadSubmitBtn.disabled = false;
      };
      reader.readAsDataURL(file);
    });

    if (removeImageBtn) {
      removeImageBtn.addEventListener("click", function () {
        imageInput.value = "";
        imagePreview.classList.add("hidden");
        uploadSubmitBtn.disabled = true;
      });
    }

    uploadForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var file = imageInput.files[0];
      if (!file) {
        alert("กรุณาเลือกรูปภาพ QR code");
        return;
      }
      showUploadLoading();
      var formData = new FormData();
      formData.append("image", file);
      fetch(uploadUrl, {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
        body: formData,
      })
        .then(function (r) {
          return r.json();
        })
        .then(function (data) {
          if (data.ok) showUploadSuccess(data);
          else showUploadError(data);
        })
        .catch(function () {
          showUploadError({
            code: "network_error",
            message: "เกิดข้อผิดพลาดในการติดต่อเซิร์ฟเวอร์",
            help: "กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต",
          });
        });
    });
  }

  function initQrManualToken(verifyUrl) {
    var form = document.getElementById("manual-token-form");
    if (!form || !verifyUrl) return;
    var input = document.getElementById("manual-token-input");
    var submitBtn = document.getElementById("manual-token-submit");
    var resultDiv = document.getElementById("qr-result");
    var activityDetailsDiv = document.getElementById("activity-details");
    var errorHelpDiv = document.getElementById("error-help");

    function showLoading() {
      resultDiv.innerHTML =
        '<div class="flex flex-col items-center justify-center h-full">' +
        '<div class="mb-4"><div class="inline-block">' +
        '<svg class="animate-spin h-12 w-12 text-emerald-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">' +
        '<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>' +
        '<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>' +
        "</svg></div></div>' +
        '<p class="text-gray-600 font-medium">กำลังยืนยัน...</p></div>';
      activityDetailsDiv.classList.add("hidden");
      errorHelpDiv.classList.add("hidden");
      submitBtn.disabled = true;
    }

    function showSuccess(data) {
      resultDiv.classList.add("hidden");
      activityDetailsDiv.classList.remove("hidden");
      errorHelpDiv.classList.add("hidden");
      var titleEl = document.getElementById("activity-title");
      var datetimeEl = document.getElementById("activity-datetime");
      var locationEl = document.getElementById("activity-location");
      var hoursEl = document.getElementById("activity-hours");
      if (data.activity) {
        if (titleEl) titleEl.textContent = data.activity.title;
        if (datetimeEl) {
          datetimeEl.innerHTML =
            '<svg class="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg> ' +
            (data.activity.datetime || "");
        }
        if (locationEl) {
          locationEl.innerHTML =
            '<svg class="w-4 h-4 mr-2 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path></svg> ' +
            (data.activity.location || "ไม่ระบุ");
        }
      }
      if (hoursEl) hoursEl.textContent = data.hours_reward || 0;
      submitBtn.disabled = false;
    }

    function showError(data) {
      resultDiv.classList.add("hidden");
      activityDetailsDiv.classList.add("hidden");
      errorHelpDiv.classList.remove("hidden");
      var errorMsg = data.message || ERROR_MESSAGES[data.code] || ERROR_MESSAGES.unknown;
      var helpText = data.help || "กรุณาลองใหม่หรือติดต่อผู้ดูแลระบบ";
      document.getElementById("error-message").textContent = errorMsg;
      document.getElementById("error-help-text").textContent = helpText;
      submitBtn.disabled = false;
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var token = input.value.trim();
      if (!token) {
        showError({ code: "no_token", message: "กรุณากรอกหรือสแกน QR code" });
        return;
      }
      try {
        var u = new URL(token);
        token = u.pathname.split("/").filter(Boolean).pop();
      } catch (err) {}
      showLoading();
      fetch(verifyUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: new URLSearchParams({ token: token }),
      })
        .then(function (r) {
          return r.json();
        })
        .then(function (data) {
          if (data.ok) showSuccess(data);
          else showError(data);
        })
        .catch(function () {
          showError({
            code: "network_error",
            message: "เกิดข้อผิดพลาดในการติดต่อเซิร์ฟเวอร์",
            help: "กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต",
          });
        });
    });

    var retryBtn = document.getElementById("retry-btn");
    if (retryBtn) {
      retryBtn.addEventListener("click", function () {
        input.value = "";
        input.focus();
        resultDiv.classList.remove("hidden");
        activityDetailsDiv.classList.add("hidden");
        errorHelpDiv.classList.add("hidden");
      });
    }

    var contactBtn = document.getElementById("contact-admin-btn");
    if (contactBtn) {
      contactBtn.addEventListener("click", function () {
        var errEl = document.getElementById("error-message");
        var subject = "ปัญหาการยืนยันกิจกรรม";
        var body = "ดูเหมือนว่าฉันมีปัญหาในการยืนยันกิจกรรม: " + (errEl ? errEl.textContent : "");
        window.location.href =
          "mailto:admin@example.com?subject=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(body);
      });
    }
  }

  function initQrScanPage(config) {
    config = config || {};
    var verifyUrl = config.verifyUrl || (document.querySelector("[data-verify-url]") && document.querySelector("[data-verify-url]").getAttribute("data-verify-url"));
    var uploadUrl = config.uploadUrl || (document.querySelector("[data-upload-url]") && document.querySelector("[data-upload-url]").getAttribute("data-upload-url"));

    if (typeof initQrScanner === "function" && verifyUrl) {
      initQrScanner(verifyUrl);
    }
    if (uploadUrl) initQrUploadForm(uploadUrl);
    if (verifyUrl) initQrManualToken(verifyUrl);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      var el = document.querySelector("[data-qr-scan-page]");
      if (el) {
        initQrScanPage({
          verifyUrl: el.getAttribute("data-verify-url"),
          uploadUrl: el.getAttribute("data-upload-url"),
        });
      }
    });
  } else {
    var el = document.querySelector("[data-qr-scan-page]");
    if (el) {
      initQrScanPage({
        verifyUrl: el.getAttribute("data-verify-url"),
        uploadUrl: el.getAttribute("data-upload-url"),
      });
    }
  }

  window.initQrScanPage = initQrScanPage;
})();
