from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .amap_proxy import amap_service_proxy

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('api/maps/', include('maps.urls')),
    path('api/analysis/', include('analysis.urls')),
    path('api/memory/', include('memory.urls')),
    path('api/reports/', include('reports.urls')),
    # 高德地图安全代理（绕过域名白名单限制）
    re_path(r'^_AMapService/(?P<path>.*)$', amap_service_proxy, name='amap_service_proxy'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
  + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
