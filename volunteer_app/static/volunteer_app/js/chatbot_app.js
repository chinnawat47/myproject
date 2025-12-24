function initChatbot(apiUrl){
  const out = document.getElementById("chat-output");
  const input = document.getElementById("chat-input");
  const send = document.getElementById("chat-send");
  let isLoading = false;

  // Clear welcome message when first message is sent
  let isFirstMessage = true;

  function append(text, who){
    // Remove welcome message on first user message
    if (isFirstMessage && who === "user") {
      const welcomeMsg = out.querySelector('.text-center');
      if (welcomeMsg) {
        welcomeMsg.remove();
      }
      isFirstMessage = false;
    }

    const messageDiv = document.createElement("div");
    messageDiv.className = `chat-message mb-4 ${who === "user" ? "user-message" : "bot-message"}`;
    
    if (who === "user") {
      messageDiv.innerHTML = `
        <div class="flex justify-end">
          <div class="max-w-[80%] sm:max-w-[70%]">
            <div class="bg-gradient-to-br from-[#1055C9] to-[#05339C] text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-lg">
              <p class="text-sm leading-relaxed whitespace-pre-wrap">${escapeHtml(text)}</p>
            </div>
            <p class="text-xs text-gray-400 mt-1 text-right">คุณ</p>
          </div>
        </div>
      `;
    } else {
      messageDiv.innerHTML = `
        <div class="flex justify-start">
          <div class="max-w-[80%] sm:max-w-[70%]">
            <div class="flex items-start gap-2">
              <div class="w-8 h-8 bg-gradient-to-br from-[#41A67E] to-[#1055C9] rounded-full flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd"></path>
                </svg>
              </div>
              <div class="flex-1 bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-md">
                <p class="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">${escapeHtml(text)}</p>
              </div>
            </div>
            <p class="text-xs text-gray-400 mt-1 ml-10">ผู้ช่วยอัจฉริยะ</p>
          </div>
        </div>
      `;
    }
    
    out.appendChild(messageDiv);
    out.scrollTop = out.scrollHeight;
  }

  function showTyping() {
    const typingDiv = document.createElement("div");
    typingDiv.id = "typing-indicator";
    typingDiv.className = "mb-4 flex justify-start";
    typingDiv.innerHTML = `
      <div class="flex items-start gap-2">
        <div class="w-8 h-8 bg-gradient-to-br from-[#41A67E] to-[#1055C9] rounded-full flex items-center justify-center flex-shrink-0">
          <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd"></path>
          </svg>
        </div>
        <div class="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-md">
          <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    `;
    out.appendChild(typingDiv);
    out.scrollTop = out.scrollHeight;
  }

  function hideTyping() {
    const typing = document.getElementById("typing-indicator");
    if (typing) {
      typing.remove();
    }
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  send.addEventListener("click", () => {
    if (isLoading) return;
    
    const q = input.value.trim();
    if(!q) return;
    
    append(q, "user");
    input.value = "";
    isLoading = true;
    send.disabled = true;
    send.innerHTML = `
      <svg class="w-5 h-5 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
      </svg>
      <span>กำลังส่ง...</span>
    `;
    
    showTyping();
    
    fetch(apiUrl, {
      method: "POST",
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': getCookie("csrftoken")
      },
      body: new URLSearchParams({ q: q })
    })
    .then(r => {
      if (!r.ok) throw new Error('Network response was not ok');
      return r.json();
    })
    .then(data => {
      hideTyping();
      append(data.reply || "ขอโทษ ฉันไม่เข้าใจคำถามนี้", "bot");
    })
    .catch(e => {
      hideTyping();
      append("เกิดข้อผิดพลาดในการเชื่อมต่อ กรุณาลองใหม่อีกครั้ง", "bot");
      console.error('Chatbot error:', e);
    })
    .finally(() => {
      isLoading = false;
      send.disabled = false;
      send.innerHTML = `
        <svg class="w-5 h-5 mr-2 transition-transform duration-300 group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
        </svg>
        <span>ส่ง</span>
      `;
    });
  });

  // Enter key support
  input.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !isLoading) {
      e.preventDefault();
      send.click();
    }
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
