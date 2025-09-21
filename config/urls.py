from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def index_view(request):
    return redirect('shelves:shelf_list')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index_view, name='index'),
    path('products/', include('products.urls')),
    path('shelves/', include('shelves.urls')),
    path('proposals/', include('proposals.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
