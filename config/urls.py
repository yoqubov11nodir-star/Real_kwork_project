from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/marketplace/', permanent=False)),
    path('auth/', include('marketplace.auth_urls', namespace='auth')),
    path('marketplace/', include('marketplace.urls', namespace='marketplace')),
    path('negotiation/', include('negotiation.urls', namespace='negotiation')),
    path('reputation/', include('reputation.urls', namespace='reputation')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)