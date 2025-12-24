// qr_scanner_main.js
// Uses html5-qrcode (CDN) to scan camera and POST token to backend
function initQrScanner(verifyUrl){
  const resultDiv = document.getElementById('qr-result');
  const activityDetailsDiv = document.getElementById('activity-details');
  const errorHelpDiv = document.getElementById('error-help');
  
  function showSuccess(data) {
    resultDiv.classList.add('hidden');
    activityDetailsDiv.classList.remove('hidden');
    errorHelpDiv.classList.add('hidden');
    
    if (data.activity) {
      document.getElementById('activity-title').textContent = data.activity.title;
      document.getElementById('activity-datetime').innerHTML = `
        <svg class="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
        ${data.activity.datetime}
      `;
      document.getElementById('activity-location').innerHTML = `
        <svg class="w-4 h-4 mr-2 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path></svg>
        ${data.activity.location || 'ไม่ระบุ'}
      `;
    }
    document.getElementById('activity-hours').textContent = data.hours_reward || 0;
  }

  function showError(data) {
    resultDiv.classList.add('hidden');
    activityDetailsDiv.classList.add('hidden');
    errorHelpDiv.classList.remove('hidden');
    
    const helpText = data.help || 'กรุณาลองใหม่หรือติดต่อผู้ดูแลระบบ';
    document.getElementById('error-message').textContent = data.message || 'เกิดข้อผิดพลาด';
    document.getElementById('error-help-text').textContent = helpText;
  }

  const html5QrCode = new Html5Qrcode("reader");
  const qrConfig = { fps: 10, qrbox: 250 };

  Html5Qrcode.getCameras().then(cameras => {
    const cameraId = cameras.length ? cameras[0].id : null;
    if(!cameraId){
      showError({
        message: 'ไม่พบกล้องในอุปกรณ์นี้',
        help: 'กรุณาใช้อุปกรณ์ที่มีกล้องหรือสแกน QR code ผ่านฟอร์มกรอกโทเค็นแทน'
      });
      return;
    }
    html5QrCode.start(
      { facingMode: "environment" },
      qrConfig,
      qrCodeMessage => {
        // when scanned, send to verify endpoint
        let token = qrCodeMessage;
        try {
          const u = new URL(qrCodeMessage);
          token = u.pathname.split('/').filter(Boolean).pop();
        } catch(e){}
        
        // post via fetch
        fetch(verifyUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCookie("csrftoken")
          },
          body: new URLSearchParams({ token: token })
        }).then(r => r.json()).then(data => {
          if(data.ok){
            showSuccess(data);
            // stop scanning after success
            html5QrCode.stop().then(()=>{}).catch(()=>{});
          } else {
            showError(data);
          }
        }).catch(err=>{
          showError({
            message: 'เกิดข้อผิดพลาดในการติดต่อเซิร์ฟเวอร์',
            help: 'กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต'
          });
        });
      },
      errorMessage => {
        // ignore per-frame errors
      }
    ).catch(err=>{
      showError({
        message: 'ไม่สามารถเริ่มกล้องได้: ' + err,
        help: 'กรุณาตรวจสอบการอนุญาตการใช้กล้องและลองใหม่'
      });
    });
  }).catch(err=>{
    showError({
      message: 'ไม่สามารถเข้าถึงกล้อง: ' + err,
      help: 'กรุณาตรวจสอบการอนุญาตในการตั้งค่าและลองใหม่'
    });
  });

  function getCookie(name) {
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
    return cookieValue;
  }
}
