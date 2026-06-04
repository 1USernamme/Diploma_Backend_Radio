from django.contrib import admin
from django.urls import path
from .views import LoginView, RegisterView, analyze_signal, analyze_uploaded_file

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/analyze/", analyze_signal, name="analyze_signal"),
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/analyze-file/", analyze_uploaded_file, name="analyze-file"),
]
