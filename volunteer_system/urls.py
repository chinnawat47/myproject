from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("volunteer_app.urls")),

    # Logout URL
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),

    # 👇 เพิ่มบรรทัดนี้เพื่อให้ django_browser_reload ทำงาน
    path("__reload__/", include("django_browser_reload.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
