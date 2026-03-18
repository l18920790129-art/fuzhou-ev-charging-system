from django.urls import path
from . import views
urlpatterns = [
    path('session/', views.get_or_create_session, name='get_or_create_session'),
    path('history/', views.get_history, name='get_history'),
    path('clear/', views.clear_memory, name='clear_memory'),
]
