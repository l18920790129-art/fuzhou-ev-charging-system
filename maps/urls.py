from django.urls import path
from . import views
urlpatterns = [
    path('geo-entities/', views.geo_entities),
    path('pois/', views.poi_list),
    path('traffic/', views.traffic_flow),
    path('exclusion-zones/', views.exclusion_zones),
    path('check/', views.check_location),
    path('heatmap/', views.heatmap_data),
    path('candidates/', views.candidates_list),
    path('quick-score/', views.quick_score_location),
]
