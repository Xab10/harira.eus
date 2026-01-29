from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from accounts.views import signup
from django.conf import settings
from django.conf.urls.static import static
from cases.views import private_media

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("cases.urls")),
    path("users/", include("users.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("signup/", signup, name="signup"),
    path("media/<path:path>", private_media, name="private_media"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
