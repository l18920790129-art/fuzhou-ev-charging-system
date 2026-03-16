from django.urls import path
from . import views
urlpatterns = [
    path('analyze/', views.analyze_location),
    path('task/<str:task_id>/', views.get_task),
    path('knowledge-graph/', views.knowledge_graph),
    path('chat/', views.agent_chat),
    path('quick-score/', views.quick_score_api),
]
