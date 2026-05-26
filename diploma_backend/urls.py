from django.contrib import admin
from django.urls import path
from .views import analyze_signal

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/analyze/', analyze_signal, name='analyze_signal'),
]