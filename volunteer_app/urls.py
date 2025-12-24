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
    path("qr/verify/", views.qr_verify, name="qr_verify"),
    path("qr/confirm/<str:token>/", views.qr_confirm, name="qr_confirm"),

    # โปรไฟล์ผู้ใช้
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/change-password/", views.change_password, name="change_password"),

    # Notifications
    path("notifications/", views.notification_list, name="notifications"),
    path("notifications/read-all/", views.notification_mark_all, name="notification_mark_all"),
    path("notifications/<int:pk>/read/", views.notification_mark_read, name="notification_mark_read"),

    # Chatbot
    path("chatbot/", views.chatbot_api, name="chatbot_api"),

    # ไอเดีย & โหวต
    path("ideas/", views.idea_list, name="idea_list"),
    path("ideas/propose/", views.propose_idea, name="propose_idea"),
    path("ideas/<int:pk>/vote/", views.vote_idea, name="vote_idea"),

    # กลุ่ม
    path("groups/", views.groups_list, name="groups"),
    path("group/create/", views.create_group, name="create_group"),
    path("group/<int:pk>/", views.group_detail, name="group_detail"),
    path("group/<int:pk>/join/", views.join_group, name="join_group"),

    # Authentication (ผู้ใช้)
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("accounts/register/", views.register, name="register"),

    # Admin Routes
    path("custom-admin/login/", views.admin_login, name="admin_login"),
    path("custom-admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("custom-admin/activities/", views.admin_manage_activities, name="admin_manage_activities"),
    path("custom-admin/activity/<int:pk>/edit/", views.admin_edit_activity, name="admin_edit_activity"),
    path("custom-admin/activity/<int:pk>/delete/", views.admin_delete_activity, name="admin_delete_activity"),
    path("custom-admin/ideas/", views.admin_manage_ideas, name="admin_manage_ideas"),
    path("custom-admin/idea/<int:pk>/approve/", views.admin_approve_idea, name="admin_approve_idea"),
    path("custom-admin/idea/<int:pk>/reject/", views.admin_reject_idea, name="admin_reject_idea"),
    path("custom-admin/users/", views.admin_manage_users, name="admin_manage_users"),
    path("custom-admin/user/<int:pk>/edit/", views.admin_edit_user, name="admin_edit_user"),
    path("custom-admin/user/<int:pk>/delete/", views.admin_delete_user, name="admin_delete_user"),
    path("custom-admin/user/<int:user_id>/hours/", views.admin_view_user_hours, name="admin_view_user_hours"),
    path("custom-admin/hours/add/", views.admin_add_volunteer_hours, name="admin_add_volunteer_hours"),
    path("custom-admin/qr-scan/<int:pk>/delete/", views.admin_delete_qr_scan, name="admin_delete_qr_scan"),
    path("custom-admin/logout/", views.admin_logout, name="admin_logout"),
]

# Error Handlers
handler404 = "volunteer_app.views.error_404"
handler500 = "volunteer_app.views.error_500"
