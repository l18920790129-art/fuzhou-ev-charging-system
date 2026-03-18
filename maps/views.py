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


@csrf_exempt
@require_http_methods(["POST"])
def quick_score_location(request):
    """快速评分：基于POI密度、交通流量、可达性、竞争分析"""
    try:
        body = json.loads(request.body)
        lat = float(body.get('lat'))
        lng = float(body.get('lng'))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid parameters"}, status=400)

    # 1. 检查禁止区域
    zones = ExclusionZone.objects.all()
    conflicts = []
    for zone in zones:
        dist = haversine(lat, lng, zone.center_lat, zone.center_lng)
        if dist <= zone.radius_km:
            conflicts.append({"name": zone.name, "type": zone.get_zone_type_display(), "distance_km": round(dist, 3)})

    if conflicts:
        return JsonResponse({
            "is_valid": False,
            "conflicts": conflicts,
            "message": f"该位置位于禁止区域内：{conflicts[0]['name']}",
            "total_score": 0
        })

    # 2. POI密度评分（2km范围内）
    all_pois = POIData.objects.all()
    nearby_pois = []
    for p in all_pois:
        dist = haversine(lat, lng, p.latitude, p.longitude)
        if dist <= 2.0:
            nearby_pois.append({
                "id": p.id, "name": p.name, "category": p.category,
                "category_display": p.get_category_display(),
                "lat": p.latitude, "lng": p.longitude,
                "ev_demand_score": p.ev_demand_score,
                "distance_km": round(dist, 3)
            })
    nearby_pois.sort(key=lambda x: x['distance_km'])

    poi_count = len(nearby_pois)
    avg_ev_demand = sum(p['ev_demand_score'] for p in nearby_pois) / poi_count if poi_count > 0 else 0
    poi_score = min(10.0, (poi_count / 8.0) * 5.0 + avg_ev_demand * 0.5)

    # 3. 交通流量评分（3km范围内主干道）
    all_roads = TrafficFlow.objects.all()
    nearby_roads = []
    for r in all_roads:
        dist = haversine(lat, lng, r.center_lat, r.center_lng)
        if dist <= 3.0:
            nearby_roads.append({
                "road_name": r.road_name, "road_level": r.road_level,
                "daily_flow": r.daily_flow, "distance_km": round(dist, 3)
            })
    nearby_roads.sort(key=lambda x: x['distance_km'])

    if nearby_roads:
        max_flow = max(r['daily_flow'] for r in nearby_roads)
        traffic_score = min(10.0, (max_flow / 60000.0) * 10.0)
    else:
        traffic_score = 3.0

    # 4. 可达性评分（基于周边道路等级）
    highway_count = sum(1 for r in nearby_roads if r['road_level'] in ['expressway', 'urban_expressway'])
    main_road_count = sum(1 for r in nearby_roads if r['road_level'] == 'main_road')
    accessibility_score = min(10.0, highway_count * 2.0 + main_road_count * 1.5 + 4.0)

    # 5. 竞争分析（现有充电站数量）
    from maps.models import CandidateLocation
    existing_stations = CandidateLocation.objects.filter(status='existing')
    competition_count = 0
    for s in existing_stations:
        dist = haversine(lat, lng, s.latitude, s.longitude)
        if dist <= 1.5:
            competition_count += 1
    competition_score = max(0.0, 10.0 - competition_count * 2.5)

    # 综合评分（加权平均）
    total_score = round(
        poi_score * 0.35 +
        traffic_score * 0.30 +
        accessibility_score * 0.20 +
        competition_score * 0.15, 2
    )

    # 评级
    if total_score >= 8.5:
        rating = "优秀·强烈推荐"
        rating_level = "excellent"
    elif total_score >= 7.0:
        rating = "良好·推荐"
        rating_level = "good"
    elif total_score >= 5.5:
        rating = "一般·可考虑"
        rating_level = "fair"
    else:
        rating = "较差·不推荐"
        rating_level = "poor"

    return JsonResponse({
        "is_valid": True,
        "lat": lat, "lng": lng,
        "total_score": total_score,
        "rating": rating,
        "rating_level": rating_level,
        "score_breakdown": {
            "poi_density": round(poi_score, 2),
            "traffic_flow": round(traffic_score, 2),
            "accessibility": round(accessibility_score, 2),
            "competition": round(competition_score, 2)
        },
        "nearby_pois": nearby_pois[:10],
        "nearby_roads": nearby_roads[:5],
        "poi_count": poi_count,
        "road_count": len(nearby_roads),
        "message": f"综合评分 {total_score}/10，{rating}"
    })
