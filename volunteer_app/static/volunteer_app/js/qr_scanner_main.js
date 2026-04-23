// qr_scanner_main.js
// Uses html5-qrcode (CDN) to scan camera and POST token to backend

// Prevent multiple initializations
let scannerInitialized = false;

function initQrScanner(verifyUrl){
  // Prevent multiple initializations
  if (scannerInitialized) {
    console.warn('QR scanner already initialized, skipping...');
    return;
  }
  
  console.log('Initializing QR scanner with URL:', verifyUrl);
  
  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      initializeScanner(verifyUrl);
    });
  } else {
    initializeScanner(verifyUrl);
  }
}

function initializeScanner(verifyUrl) {
  try {
    // Check if HTTPS is required (for camera access)
    const isSecureContext = window.isSecureContext || location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1';
    
    if (!isSecureContext) {
      console.warn('Not a secure context - camera may not work');
      const resultDiv = document.getElementById('qr-result');
      if (resultDiv) {
        resultDiv.innerHTML = `
          <div class="text-center text-red-600 p-4">
            <p class="font-semibold">⚠️ ต้องใช้ HTTPS เพื่อเข้าถึงกล้อง</p>
            <p class="text-sm mt-2">กรุณาเข้าถึงเว็บไซต์ผ่าน HTTPS (https://)</p>
            <p class="text-xs mt-1 text-gray-500">หรือใช้ฟอร์มกรอกโทเค็นด้านล่างแทน</p>
          </div>
        `;
      }
      // Don't return - still allow manual token entry
    }
    
    const resultDiv = document.getElementById('qr-result');
    const activityDetailsDiv = document.getElementById('activity-details');
    const errorHelpDiv = document.getElementById('error-help');
    
    // Check if required elements exist
    if (!resultDiv) {
      console.error('qr-result element not found!');
    }
    if (!activityDetailsDiv) {
      console.error('activity-details element not found!');
    }
    if (!errorHelpDiv) {
      console.error('error-help element not found!');
    }
    
    const readerDiv = document.getElementById('reader');
    if (!readerDiv) {
      console.error('reader element not found!');
      // Show error in resultDiv if available
      if (resultDiv) {
        resultDiv.innerHTML = `
          <div class="text-center text-red-600">
            <p class="font-semibold">ไม่พบ element สำหรับสแกน QR code</p>
            <p class="text-sm mt-2">กรุณารีเฟรชหน้าเว็บและลองใหม่</p>
          </div>
        `;
      }
      return;
    }

  // Define helper functions first
  function showSuccess(data) {
    // Hide result placeholder and error, show activity details
    if (resultDiv) resultDiv.classList.add('hidden');
    if (activityDetailsDiv) activityDetailsDiv.classList.remove('hidden');
    if (errorHelpDiv) errorHelpDiv.classList.add('hidden');
    
    // Update activity information
    if (data.activity) {
      const titleEl = document.getElementById('activity-title');
      const datetimeEl = document.getElementById('activity-datetime');
      const locationEl = document.getElementById('activity-location');
      
      if (titleEl) titleEl.textContent = data.activity.title;
      
      if (datetimeEl) {
        datetimeEl.innerHTML = `
          <svg class="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
          ${data.activity.datetime || 'ไม่ระบุ'}
        `;
      }
      
      if (locationEl) {
        locationEl.innerHTML = `
          <svg class="w-4 h-4 mr-2 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path></svg>
          ${data.activity.location || 'ไม่ระบุ'}
        `;
      }
    }
    
    // Update hours - use hours_reward from root or from activity object
    const hoursEl = document.getElementById('activity-hours');
    if (hoursEl) {
      const hours = data.hours_reward || (data.activity && data.activity.hours_reward) || 0;
      hoursEl.textContent = hours;
    }
  }

  function showError(data) {
    // Hide result placeholder and activity details, show error
    if (resultDiv) resultDiv.classList.add('hidden');
    if (activityDetailsDiv) activityDetailsDiv.classList.add('hidden');
    if (errorHelpDiv) errorHelpDiv.classList.remove('hidden');
    
    const errorMsgEl = document.getElementById('error-message');
    const errorHelpEl = document.getElementById('error-help-text');
    
    if (errorMsgEl) {
      errorMsgEl.textContent = data.message || 'เกิดข้อผิดพลาด';
    }
    
    if (errorHelpEl) {
      const helpText = data.help || 'กรุณาลองใหม่หรือติดต่อผู้ดูแลระบบ';
      errorHelpEl.textContent = helpText;
    }
  }

  // Check if Html5Qrcode is available
  if (typeof Html5Qrcode === 'undefined') {
    console.error('Html5Qrcode library not loaded!');
    showError({
      message: 'ไม่พบไลบรารีสำหรับสแกน QR code',
      help: 'กรุณารีเฟรชหน้าเว็บและลองใหม่'
    });
    return;
  }
  
  const html5QrCode = new Html5Qrcode("reader");
  
  // Detect mobile device and adjust config
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
  
  // Adjust QR box size based on screen size
  const screenWidth = window.innerWidth || document.documentElement.clientWidth;
  const qrboxSize = isMobile ? Math.min(250, screenWidth * 0.8) : 250;
  
  const qrConfig = { 
    fps: 10, 
    qrbox: qrboxSize,
    aspectRatio: 1.0,
    disableFlip: false
  };
  
  console.log('Device info:', { isMobile, isIOS, screenWidth, qrboxSize });

  console.log('Getting cameras...');
  Html5Qrcode.getCameras().then(cameras => {
    console.log('Cameras found:', cameras.length, cameras);
    
    if (cameras.length === 0) {
      showError({
        message: 'ไม่พบกล้องในอุปกรณ์นี้',
        help: 'กรุณาใช้อุปกรณ์ที่มีกล้องหรือสแกน QR code ผ่านฟอร์มกรอกโทเค็นแทน'
      });
      return;
    }
    
    // Try to find back camera (environment) first, fallback to any camera
    let selectedCamera = null;
    let cameraConfig = null;
    
    // Find back camera (environment facing)
    const backCamera = cameras.find(cam => 
      cam.label && (cam.label.toLowerCase().includes('back') || 
                   cam.label.toLowerCase().includes('rear') ||
                   cam.label.toLowerCase().includes('environment'))
    );
    
    if (backCamera) {
      selectedCamera = backCamera.id;
      cameraConfig = { deviceId: { exact: selectedCamera } };
      console.log('Using back camera:', backCamera.label);
    } else if (cameras.length > 0) {
      // Try facingMode for mobile, or use first camera
      if (isMobile) {
        cameraConfig = { facingMode: "environment" };
        console.log('Using facingMode: environment');
      } else {
        selectedCamera = cameras[0].id;
        cameraConfig = { deviceId: { exact: selectedCamera } };
        console.log('Using first camera:', cameras[0].label);
      }
    }
    
    let isScanning = false;
    let scanProcessed = false;
    
    html5QrCode.start(
      cameraConfig || { facingMode: "environment" },
      qrConfig,
      qrCodeMessage => {
        // Prevent multiple scans
        if (scanProcessed) {
          return;
        }
        scanProcessed = true;
        
        console.log('QR Code scanned:', qrCodeMessage);
        
        // when scanned, send to verify endpoint
        let token = qrCodeMessage;
        try {
          const u = new URL(qrCodeMessage);
          token = u.pathname.split('/').filter(Boolean).pop();
          console.log('Extracted token from URL:', token);
        } catch(e){
          console.log('Using raw token:', token);
        }
        
        // Stop scanning to prevent multiple scans
        html5QrCode.stop().then(() => {
          console.log('QR scanner stopped for verification');
          isScanning = false;
        }).catch((err) => {
          console.error('Error stopping scanner:', err);
          isScanning = false;
        });
        
        // Show loading state
        if (resultDiv) {
          resultDiv.classList.remove('hidden');
          resultDiv.innerHTML = `
            <div class="flex flex-col items-center justify-center h-full">
              <div class="mb-4">
                <div class="inline-block">
                  <svg class="animate-spin h-12 w-12 text-emerald-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </div>
              </div>
              <p class="text-gray-600 font-medium">กำลังยืนยัน...</p>
            </div>
          `;
        }
        
        const csrfToken = getCookie("csrftoken");
        console.log('CSRF Token found:', csrfToken ? 'Yes' : 'No');
        console.log('Sending request to:', verifyUrl);
        
        // post via fetch
        fetch(verifyUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": csrfToken || ""
          },
          body: new URLSearchParams({ token: token })
        }).then(r => {
          console.log('Response status:', r.status);
          if (!r.ok) {
            throw new Error(`HTTP error! status: ${r.status}`);
          }
          return r.json();
        }).then(data => {
          console.log('Response data:', data);
          if(data.ok){
            showSuccess(data);
          } else {
            showError(data);
          }
        }).catch(err=>{
          console.error('QR verification error:', err);
          showError({
            message: 'เกิดข้อผิดพลาดในการติดต่อเซิร์ฟเวอร์',
            help: 'กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต'
          });
        }).finally(() => {
          scanProcessed = false;
        });
      },
      errorMessage => {
        // Only log significant errors, ignore per-frame scanning errors
        if (errorMessage && !errorMessage.includes('NotFoundException') && !errorMessage.includes('No QR code')) {
          console.debug('QR scan error (ignored):', errorMessage);
        }
      }
    ).then(() => {
      console.log('QR scanner started successfully');
      isScanning = true;
      
      // Hide loading message in reader div
      const readerDiv = document.getElementById('reader');
      if (readerDiv) {
        const loadingMsg = readerDiv.querySelector('.text-center.text-gray-500');
        if (loadingMsg) {
          loadingMsg.style.display = 'none';
        }
      }
    }).catch(err=>{
      console.error('Error starting QR scanner:', err);
      
      // More specific error messages for mobile
      let errorMessage = 'ไม่สามารถเริ่มกล้องได้';
      let helpMessage = 'กรุณาตรวจสอบการอนุญาตการใช้กล้องและลองใหม่';
      
      if (err.message) {
        if (err.message.includes('Permission') || err.message.includes('permission')) {
          errorMessage = 'ไม่ได้รับอนุญาตให้ใช้กล้อง';
          helpMessage = 'กรุณาอนุญาตให้เว็บไซต์ใช้กล้องในตั้งค่าของเบราว์เซอร์';
        } else if (err.message.includes('NotFound') || err.message.includes('not found')) {
          errorMessage = 'ไม่พบกล้อง';
          helpMessage = 'กรุณาตรวจสอบว่าอุปกรณ์มีกล้องและพร้อมใช้งาน';
        } else if (err.message.includes('NotAllowed') || err.message.includes('not allowed')) {
          errorMessage = 'การเข้าถึงกล้องถูกปฏิเสธ';
          helpMessage = 'กรุณาอนุญาตให้เว็บไซต์ใช้กล้องในตั้งค่าของเบราว์เซอร์';
        } else if (err.message.includes('HTTPS') || err.message.includes('secure context')) {
          errorMessage = 'ต้องใช้ HTTPS เพื่อเข้าถึงกล้อง';
          helpMessage = 'กรุณาเข้าถึงเว็บไซต์ผ่าน HTTPS (https://)';
        }
      }
      
      showError({
        message: errorMessage + ': ' + (err.message || err),
        help: helpMessage
      });
    });
  }).catch(err=>{
    showError({
      message: 'ไม่สามารถเข้าถึงกล้อง: ' + err,
      help: 'กรุณาตรวจสอบการอนุญาตในการตั้งค่าและลองใหม่'
    });
  });

  function getCookie(name) {
    // วิธีที่ 1: อ่านจาก cookie (รองรับ Safari และทุก browser)
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    
    // วิธีที่ 2: Fallback - อ่านจาก meta tag (สำหรับกรณีที่ cookie ไม่ทำงานใน Safari)
    if (!cookieValue && name === 'csrftoken') {
      const metaTag = document.querySelector('meta[name="csrf-token"]');
      if (metaTag) {
        cookieValue = metaTag.getAttribute('content');
      }
    }
    
    // วิธีที่ 3: Fallback - อ่านจาก hidden input (Django csrf_token)
    if (!cookieValue && name === 'csrftoken') {
      const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
      if (csrfInput) {
        cookieValue = csrfInput.value;
      }
    }
    
    return cookieValue;
  }
  
  // Mark as initialized
  scannerInitialized = true;
  console.log('QR scanner initialization completed');
  } catch (error) {
    console.error('Error initializing QR scanner:', error);
    const resultDiv = document.getElementById('qr-result');
    if (resultDiv) {
      resultDiv.innerHTML = `
        <div class="text-center text-red-600 p-4">
          <p class="font-semibold">เกิดข้อผิดพลาดในการเริ่มต้นสแกนเนอร์</p>
          <p class="text-sm mt-2">กรุณารีเฟรชหน้าเว็บและลองใหม่</p>
          <p class="text-xs mt-1 text-gray-500">Error: ${error.message}</p>
        </div>
      `;
    }
  }
}
