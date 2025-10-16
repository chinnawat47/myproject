from django.urls import path
from . import views

app_name = "volunteer_app"

urlpatterns = [
    # หน้าแรก
    path("", views.index, name="index"),

    # กิจกรรม
    path("activities/", views.activities, name="activities"),
    path("activity/<int:pk>/", views.activity_detail, name="activity_detail"),
    path("activity/create/", views.create_activity, name="create_activity"),
    path("activity/<int:pk>/signup/", views.activity_signup, name="activity_signup"),

    # QR code
    path("qr/scan/", views.qr_scan_page, name="qr_scan"),
    path("qr/verify/", views.qr_verify, name="qr_verify"),  # POST for verification
    path("qr/confirm/<str:token>/", views.qr_confirm, name="qr_confirm"),  # direct QR link

    # โปรไฟล์ผู้ใช้
    path("profile/", views.profile, name="profile"),

    # Chatbot
    path("chatbot/", views.chatbot_api, name="chatbot_api"),

    # เสนอไอเดีย / โหวตกิจกรรม
    path("propose/", views.propose_idea, name="propose_idea"),
    path("vote/<int:activity_id>/", views.vote_activity, name="vote_activity"),

    # กลุ่ม
    path("groups/", views.groups_list, name="groups"),
    path("group/create/", views.create_group, name="create_group"),
    path("group/<int:pk>/", views.group_detail, name="group_detail"),
    path("group/<int:pk>/join/", views.join_group, name="join_group"),

    # Authentication
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("accounts/register/", views.register, name="register"),
]
