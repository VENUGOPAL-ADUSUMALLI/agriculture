from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('agri.urls')),
    path('api/v1/petroleum/', include('petroleum.urls')),
]
