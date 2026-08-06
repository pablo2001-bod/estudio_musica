from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView # <-- Importamos RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Service Worker desde la plantilla
    path('sw.js', TemplateView.as_view(
        template_name='estudio/sw.js', 
        content_type='application/javascript'
    ), name='sw.js'),
    
    # Manifest redirigido al archivo estático
    path('manifest.json', RedirectView.as_view(
        url='/static/manifest.json', 
        permanent=True
    ), name='manifest.json'),

    path('', include('estudio.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)