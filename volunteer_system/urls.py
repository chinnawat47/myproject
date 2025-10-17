from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    # หน้า admin ของ Django
    path("admin/", admin.site.urls),

    # รวม URLs ของแอป volunteer_app
    path("", include("volunteer_app.urls")),

    # Logout URL (ใช้ LogoutView ของ Django)
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),

    # สำหรับ django_browser_reload
    path("__reload__/", include("django_browser_reload.urls")),
]

# ให้ไฟล์ media สามารถเข้าถึงได้ใน DEBUG mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
