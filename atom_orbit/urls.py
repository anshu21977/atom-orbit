from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('secure-admin-portal-923847/', admin.site.urls),  # 🔥 custom admin URL
    path('', include('core.urls')),
]

# Media files (PDFs)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
