function initChatbot(apiUrl){
  const out = document.getElementById("chat-output");
  const input = document.getElementById("chat-input");
  const send = document.getElementById("chat-send");

  function append(text, who){
    const d = document.createElement("div");
    d.className = who === "user" ? "text-right text-sm mt-1" : "text-left text-sm mt-1 text-gray-700";
    d.innerText = text;
    out.appendChild(d);
    out.scrollTop = out.scrollHeight;
  }

  send.addEventListener("click", () => {
    const q = input.value.trim();
    if(!q) return;
    append(q, "user");
    input.value = "";
    fetch(apiUrl, {
      method: "POST",
      headers: {'Content-Type':'application/x-www-form-urlencoded','X-CSRFToken': getCookie("csrftoken")},
      body: new URLSearchParams({ q: q })
    }).then(r=>r.json()).then(data=>{
      append(data.reply, "bot");
    }).catch(e=>{
      append("เกิดข้อผิดพลาด", "bot");
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
