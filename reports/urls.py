from django.urls import path
from . import views
urlpatterns = [
    path('generate/', views.generate_report),
    path('list/', views.report_list),
    path('<str:report_id>/', views.get_report),
    path('<str:report_id>/pdf/', views.download_pdf),
]
