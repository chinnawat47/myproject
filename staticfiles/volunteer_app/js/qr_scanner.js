// qr_scanner.js
// Uses html5-qrcode (CDN) to scan camera and POST token to backend
function initQrScanner(verifyUrl){
  const resultDiv = document.getElementById('qr-result');
  function show(msg, ok){
    resultDiv.innerText = msg;
    if(ok) resultDiv.className = "mt-4 text-green-600 font-semibold";
    else resultDiv.className = "mt-4 text-red-600 font-semibold";
  }

  const html5QrCode = new Html5Qrcode("reader");
  const qrConfig = { fps: 10, qrbox: 250 };

  Html5Qrcode.getCameras().then(cameras => {
    const cameraId = cameras.length ? cameras[0].id : null;
    if(!cameraId){
      show("ไม่พบกล้อง");
      return;
    }
    html5QrCode.start(
      { facingMode: "environment" },
      qrConfig,
      qrCodeMessage => {
        // when scanned, send to verify endpoint
        // token could be url or token; extract token if url
        let token = qrCodeMessage;
        try {
          const u = new URL(qrCodeMessage);
          // token may be last part of path
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
            show(data.message, true);
            // stop scanning after success
            html5QrCode.stop().then(()=>{}).catch(()=>{});
          } else {
            show(data.message, false);
          }
        }).catch(err=>{
          show("เกิดข้อผิดพลาดในการติดต่อเซิร์ฟเวอร์", false);
        });
      },
      errorMessage => {
        // ignore per-frame errors
      }
    ).catch(err=>{
      show("ไม่สามารถเริ่มกล้อง: " + err, false);
    });
  }).catch(err=>{
    show("ไม่สามารถเข้าถึงกล้อง: " + err, false);
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
