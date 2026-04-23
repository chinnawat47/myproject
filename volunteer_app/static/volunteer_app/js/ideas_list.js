/**
 * ideas_list.js
 * AJAX vote/unvote for idea forms (.idea-vote-form).
 * Submits to form.action, expects JSON: { ok, votes, voted }.
 */
(function () {
  "use strict";

  function initIdeasList() {
    var voteForms = document.querySelectorAll(".idea-vote-form");
    voteForms.forEach(function (form) {
      form.addEventListener("submit", function (event) {
        event.preventDefault();
        var ideaId = form.getAttribute("data-idea-id");
        var submitBtn = form.querySelector("button[type='submit']");
        var actionInput = form.querySelector("input[name='action']");
        var csrfInput = form.querySelector("input[name='csrfmiddlewaretoken']");
        var csrfToken = csrfInput ? csrfInput.value : "";

        submitBtn.disabled = true;
        submitBtn.classList.add("opacity-70", "cursor-not-allowed");

        var formData = new FormData(form);
        var body = new URLSearchParams(formData);

        fetch(form.action, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrfToken,
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: body,
        })
          .then(function (response) {
            if (!response.ok) throw new Error("network error");
            return response.json();
          })
          .then(function (data) {
            if (data.ok) {
              var countEl = document.querySelector("[data-idea-count='" + ideaId + "']");
              if (countEl) countEl.textContent = data.votes;

              if (data.voted) {
                actionInput.value = "unvote";
                submitBtn.innerHTML =
                  '<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">' +
                  '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>' +
                  "</svg> โหวตแล้ว - กดเพื่อยกเลิก";
                submitBtn.classList.remove("bg-primary");
                submitBtn.classList.add("bg-gradient-to-r", "from-green-500", "to-emerald-600", "text-white");
              } else {
                actionInput.value = "vote";
                submitBtn.innerHTML =
                  '<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">' +
                  '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5v14"></path>' +
                  "</svg> โหวตสนับสนุนไอเดียนี้";
                submitBtn.classList.remove("bg-gradient-to-r", "from-green-500", "to-emerald-600");
                submitBtn.classList.add("bg-primary", "text-white");
              }
            }
          })
          .catch(function () {
            alert("เกิดข้อผิดพลาดในการบันทึกโหวต กรุณาลองใหม่");
          })
          .finally(function () {
            submitBtn.disabled = false;
            submitBtn.classList.remove("opacity-70", "cursor-not-allowed");
          });
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initIdeasList);
  } else {
    initIdeasList();
  }
})();
