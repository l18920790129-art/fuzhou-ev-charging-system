"""
地图相关API视图
"""
import json
import math
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import POIData, TrafficFlow, ExclusionZone, GeoEntity, CandidateLocation


def haversine(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def geo_entities(request):
    """获取地理实体列表"""
    entity_type = request.GET.get('type', '')
    qs = GeoEntity.objects.all()
    if entity_type:
        qs = qs.filter(entity_type=entity_type)
    data = [{"id": e.id, "name": e.name, "type": e.entity_type, "lat": e.latitude, "lng": e.longitude, "district": e.district} for e in qs[:200]]
    return JsonResponse({"data": data, "total": len(data)})


def poi_list(request):
    """获取POI数据列表"""
    category = request.GET.get('category', '')
    district = request.GET.get('district', '')
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    radius = float(request.GET.get('radius', 2.0))

    qs = POIData.objects.all()
    if category:
        qs = qs.filter(category=category)
    if district:
        qs = qs.filter(district__icontains=district)

    pois = list(qs)
    if lat and lng:
        lat, lng = float(lat), float(lng)
        pois = [(p, haversine(lat, lng, p.latitude, p.longitude)) for p in pois]
        pois = [(p, d) for p, d in pois if d <= radius]
        pois.sort(key=lambda x: x[1])
        data = [{"id": p.id, "name": p.name, "category": p.category, "category_display": p.get_category_display(),
                 "lat": p.latitude, "lng": p.longitude, "district": p.district,
                 "daily_flow": p.daily_flow, "ev_demand_score": p.ev_demand_score,
                 "influence_weight": p.influence_weight, "distance_km": round(d, 3)} for p, d in pois]
    else:
        data = [{"id": p.id, "name": p.name, "category": p.category, "category_display": p.get_category_display(),
                 "lat": p.latitude, "lng": p.longitude, "district": p.district,
                 "daily_flow": p.daily_flow, "ev_demand_score": p.ev_demand_score,
                 "influence_weight": p.influence_weight} for p in pois]

    return JsonResponse({"data": data, "total": len(data)})


def traffic_flow(request):
    """获取交通流量数据"""
    district = request.GET.get('district', '')
    road_level = request.GET.get('road_level', '')
    qs = TrafficFlow.objects.all()
    if district:
        qs = qs.filter(district__icontains=district)
    if road_level:
        qs = qs.filter(road_level=road_level)

    data = []
    for t in qs:
        item = {
            "id": t.id, "road_name": t.road_name,
            "road_level": t.road_level, "road_level_display": t.get_road_level_display(),
            "start_lat": t.start_lat, "start_lng": t.start_lng,
            "end_lat": t.end_lat, "end_lng": t.end_lng,
            "center_lat": t.center_lat, "center_lng": t.center_lng,
            "daily_flow": t.daily_flow, "peak_flow": t.peak_flow,
            "ev_ratio": t.ev_ratio, "heat_weight": t.heat_weight,
            "district": t.district,
        }
        if t.path_json:
            try:
                item["path"] = json.loads(t.path_json)
            except:
                item["path"] = [[t.start_lat, t.start_lng], [t.center_lat, t.center_lng], [t.end_lat, t.end_lng]]
        else:
            item["path"] = [[t.start_lat, t.start_lng], [t.center_lat, t.center_lng], [t.end_lat, t.end_lng]]
        data.append(item)

    return JsonResponse({"data": data, "total": len(data)})


def exclusion_zones(request):
    """获取禁止选址区域"""
    qs = ExclusionZone.objects.all()
    data = []
    for z in qs:
        item = {
            "id": z.id, "name": z.name,
            "zone_type": z.zone_type, "zone_type_display": z.get_zone_type_display(),
            "center_lat": z.center_lat, "center_lng": z.center_lng,
            "radius_km": z.radius_km, "description": z.description,
        }
        try:
            item["boundary"] = json.loads(z.boundary_json)
        except:
            item["boundary"] = None
        data.append(item)
    return JsonResponse({"data": data})


@csrf_exempt
def check_location(request):
    """检查位置是否在禁止区域内"""
    if request.method == 'POST':
        body = json.loads(request.body)
        lat, lng = float(body.get('lat')), float(body.get('lng'))
    else:
        lat, lng = float(request.GET.get('lat')), float(request.GET.get('lng'))

    zones = ExclusionZone.objects.all()
    conflicts = []
    for zone in zones:
        dist = haversine(lat, lng, zone.center_lat, zone.center_lng)
        if dist <= zone.radius_km:
            conflicts.append({"name": zone.name, "type": zone.get_zone_type_display(), "distance_km": round(dist, 3)})

    return JsonResponse({
        "lat": lat, "lng": lng,
        "is_valid": len(conflicts) == 0,
        "conflicts": conflicts,
        "message": "位置有效，可以选址" if not conflicts else f"该位置位于禁止区域内：{conflicts[0]['name']}"
    })


def heatmap_data(request):
    """获取热力图数据（主干道流量热力点）"""
    roads = TrafficFlow.objects.all().order_by('-daily_flow')
    heatmap_points = []
    for road in roads:
        # 优先使用path_json中的路径点
        path_points = None
        if road.path_json:
            try:
                path_points = json.loads(road.path_json)
            except:
                pass
        
        if path_points and len(path_points) >= 2:
            # 使用实际路径点
            for pt in path_points:
                heatmap_points.append({
                    "lat": round(pt[0], 6),
                    "lng": round(pt[1], 6),
                    "weight": road.heat_weight,
                    "flow": road.daily_flow,
                    "road_name": road.road_name,
                })
        else:
            # 沿路段插值生成热力点
            steps = 6
            for i in range(steps + 1):
                t = i / steps
                point_lat = road.start_lat + (road.end_lat - road.start_lat) * t
                point_lng = road.start_lng + (road.end_lng - road.start_lng) * t
                heatmap_points.append({
                    "lat": round(point_lat, 6),
                    "lng": round(point_lng, 6),
                    "weight": road.heat_weight,
                    "flow": road.daily_flow,
                    "road_name": road.road_name,
                })

    return JsonResponse({"data": heatmap_points, "total": len(heatmap_points)})


def candidates_list(request):
    """获取候选位置列表"""
    from .models import CandidateLocation
    qs = CandidateLocation.objects.all()
    data = [{"id": c.id, "name": c.name, "lat": c.latitude, "lng": c.longitude,
             "status": c.status, "total_score": c.total_score, "address": c.address} for c in qs]
    return JsonResponse({"data": data})
