/**
 * group_detail.js
 * AJAX handlers for group detail page: join group, invite member, post message.
 * POSTs to current page URL; expects JSON with ok, message, and optional fields.
 * CSRF: use meta[name="csrf-token"] or form's csrfmiddlewaretoken (FormData includes it).
 */
(function () {
  "use strict";

  function initGroupDetail() {
    // POST to current page (group_detail view handles different actions by form field names)
    var postUrl = "";

    // ----- Join group (AJAX) -----
    var joinForm = document.querySelector('form button[name="join_group"]');
    if (joinForm) {
      joinForm = joinForm.closest("form");
    }
    if (joinForm) {
      joinForm.addEventListener("submit", function (e) {
        e.preventDefault();
        var formData = new FormData(joinForm);
        fetch(postUrl, {
          method: "POST",
          headers: { "X-Requested-With": "XMLHttpRequest" },
          body: formData,
        })
          .then(function (r) {
            return r.json();
          })
          .then(function (data) {
            if (data.ok) {
              var memberList = document.getElementById("members-list");
              if (memberList) {
                var li = document.createElement("li");
                li.className = "flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors duration-150";
                var name = data.full_name || data.username || "";
                var initial = name ? name.charAt(0) : (data.username && data.username.charAt(0)) || "?";
                li.innerHTML =
                  '<div class="flex-shrink-0">' +
                  '<div class="w-8 h-8 bg-gradient-to-br from-[#E5C95F] to-[#41A67E] rounded-full flex items-center justify-center">' +
                  '<span class="text-white font-medium text-xs">' + initial + "</span></div></div>" +
                  '<div class="flex-1 min-w-0">' +
                  '<p class="text-sm font-medium text-[#05339C] truncate">' + (name || "") + "</p>" +
                  '<p class="text-xs text-gray-500 truncate">@' + (data.username || "") + "</p></div>";
                memberList.appendChild(li);
              }
              joinForm.remove();
              alert("เข้าร่วมกลุ่มเรียบร้อย!");
            } else {
              alert(data.message || "เกิดข้อผิดพลาดในการเข้าร่วมกลุ่ม");
            }
          })
          .catch(function () {
            alert("เกิดข้อผิดพลาดในการเชื่อมต่อ");
          });
      });
    }

    // ----- Invite friend (AJAX) -----
    var inviteForm = document.getElementById("inviteForm");
    if (inviteForm) {
      inviteForm.addEventListener("submit", function (e) {
        e.preventDefault();
        var formData = new FormData(inviteForm);
        fetch(postUrl, {
          method: "POST",
          headers: { "X-Requested-With": "XMLHttpRequest" },
          body: formData,
        })
          .then(function (r) {
            return r.json();
          })
          .then(function (data) {
            var resultDiv = document.getElementById("inviteResult");
            if (resultDiv) resultDiv.innerText = data.message || "";
            if (data.ok) {
              inviteForm.reset();
              var memberList = document.getElementById("members-list");
              if (memberList && data.username) {
                var li = document.createElement("li");
                li.className = "flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors duration-150";
                var name = data.full_name || data.username || "";
                var initial = name ? name.charAt(0) : data.username.charAt(0) || "?";
                li.innerHTML =
                  '<div class="flex-shrink-0">' +
                  '<div class="w-8 h-8 bg-gradient-to-br from-[#E5C95F] to-[#41A67E] rounded-full flex items-center justify-center">' +
                  '<span class="text-white font-medium text-xs">' + initial + "</span></div></div>" +
                  '<div class="flex-1 min-w-0">' +
                  '<p class="text-sm font-medium text-[#05339C] truncate">' + (name || "") + "</p>" +
                  '<p class="text-xs text-gray-500 truncate">@' + (data.username || "") + "</p></div>";
                memberList.appendChild(li);
              }
            }
          })
          .catch(function () {
            var resultDiv = document.getElementById("inviteResult");
            if (resultDiv) resultDiv.innerText = "เกิดข้อผิดพลาดในการเชื่อมต่อ";
          });
      });
    }

    // ----- Post message (AJAX) -----
    var postForm = document.getElementById("postForm");
    if (postForm) {
      postForm.addEventListener("submit", function (e) {
        e.preventDefault();
        var formData = new FormData(postForm);
        fetch(postUrl, {
          method: "POST",
          headers: { "X-Requested-With": "XMLHttpRequest" },
          body: formData,
        })
          .then(function (r) {
            return r.json();
          })
          .then(function (data) {
            if (data.ok) {
              var postsList = document.getElementById("posts-list");
              if (postsList) {
                var postDiv = document.createElement("article");
                postDiv.className = "p-6 hover:bg-gray-50 transition-colors duration-150";
                var authorName = data.author || "";
                var authorInitial = authorName ? authorName.charAt(0) : "?";
                postDiv.innerHTML =
                  '<div class="flex space-x-4">' +
                  '<div class="flex-shrink-0">' +
                  '<div class="w-10 h-10 bg-gradient-to-br from-[#41A67E] to-[#1055C9] rounded-full flex items-center justify-center">' +
                  '<span class="text-white font-medium text-sm">' + authorInitial + "</span></div></div>" +
                  '<div class="flex-1 min-w-0">' +
                  '<div class="flex items-center space-x-2 mb-2">' +
                  '<h4 class="text-sm font-medium text-[#05339C]">' + (authorName || "") + "</h4>" +
                  '<span class="text-xs text-gray-500">•</span>' +
                  '<time class="text-xs text-gray-500">' + (data.created_at || "") + "</time></div>" +
                  '<p class="text-gray-800 leading-relaxed">' + (data.content || "").replace(/</g, "&lt;").replace(/>/g, "&gt;") + "</p></div></div>";
                postsList.insertBefore(postDiv, postsList.firstChild);
              }
              postForm.reset();
            } else {
              alert(data.message || "เกิดข้อผิดพลาดในการโพสต์ข้อความ");
            }
          })
          .catch(function () {
            alert("เกิดข้อผิดพลาดในการเชื่อมต่อ");
          });
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initGroupDetail);
  } else {
    initGroupDetail();
  }
})();
