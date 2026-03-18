"""
数据增强脚本：补充更多福州真实POI和道路数据（已修复类别和路径格式Bug）
"""
import os, sys, json, django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fuzhou_ev_charging.settings')
django.setup()

from maps.models import POIData, TrafficFlow, CandidateLocation

EXTRA_POIS = [
    {"name": "福州万达广场", "category": "shopping_mall", "lat": 26.0834, "lng": 119.2956, "daily_flow": 40000, "ev_demand_score": 9.0, "influence_weight": 1.0},
    {"name": "融侨中心", "category": "shopping_mall", "lat": 26.0912, "lng": 119.3123, "daily_flow": 25000, "ev_demand_score": 8.2, "influence_weight": 0.85},
    {"name": "福州软件园", "category": "office_building", "lat": 26.0456, "lng": 119.2834, "daily_flow": 20000, "ev_demand_score": 8.5, "influence_weight": 0.9},
    {"name": "福州大学城", "category": "school", "lat": 26.0234, "lng": 119.2456, "daily_flow": 30000, "ev_demand_score": 7.8, "influence_weight": 0.8},
    {"name": "福州火车站北广场", "category": "bus_station", "lat": 26.0823, "lng": 119.3345, "daily_flow": 55000, "ev_demand_score": 9.5, "influence_weight": 1.0},
    {"name": "福州南站（高铁站）", "category": "bus_station", "lat": 25.9812, "lng": 119.3234, "daily_flow": 65000, "ev_demand_score": 9.8, "influence_weight": 1.0},
    {"name": "福州长乐国际机场", "category": "bus_station", "lat": 25.9345, "lng": 119.6634, "daily_flow": 45000, "ev_demand_score": 9.2, "influence_weight": 1.0},
    {"name": "泰禾广场（福州）", "category": "shopping_mall", "lat": 26.0678, "lng": 119.3456, "daily_flow": 35000, "ev_demand_score": 8.8, "influence_weight": 0.95},
    {"name": "宝龙广场（晋安）", "category": "shopping_mall", "lat": 26.0934, "lng": 119.3567, "daily_flow": 28000, "ev_demand_score": 8.3, "influence_weight": 0.85},
    {"name": "福州奥体中心", "category": "sports_center", "lat": 26.0345, "lng": 119.2678, "daily_flow": 20000, "ev_demand_score": 7.5, "influence_weight": 0.75},
    {"name": "苏宁广场（台江）", "category": "shopping_mall", "lat": 26.0567, "lng": 119.3123, "daily_flow": 30000, "ev_demand_score": 8.5, "influence_weight": 0.9},
    {"name": "福州汽车北站", "category": "bus_station", "lat": 26.0756, "lng": 119.3234, "daily_flow": 25000, "ev_demand_score": 8.8, "influence_weight": 0.9},
    {"name": "中亭街商业区", "category": "shopping_mall", "lat": 26.0623, "lng": 119.3045, "daily_flow": 22000, "ev_demand_score": 8.0, "influence_weight": 0.85},
    {"name": "海峡奥林匹克体育中心", "category": "sports_center", "lat": 26.0234, "lng": 119.3012, "daily_flow": 18000, "ev_demand_score": 7.8, "influence_weight": 0.8},
    {"name": "福州大学（仓山校区）", "category": "school", "lat": 26.0456, "lng": 119.2923, "daily_flow": 25000, "ev_demand_score": 7.5, "influence_weight": 0.8},
    {"name": "金山万达广场", "category": "shopping_mall", "lat": 26.0312, "lng": 119.2756, "daily_flow": 32000, "ev_demand_score": 8.6, "influence_weight": 0.9},
    {"name": "东二环泰禾广场", "category": "shopping_mall", "lat": 26.0934, "lng": 119.3678, "daily_flow": 38000, "ev_demand_score": 8.9, "influence_weight": 0.95},
    {"name": "晋安湖公园", "category": "scenic_spot", "lat": 26.1023, "lng": 119.3789, "daily_flow": 15000, "ev_demand_score": 7.0, "influence_weight": 0.7},
    {"name": "福州高新区科技园", "category": "office_building", "lat": 26.0123, "lng": 119.2234, "daily_flow": 22000, "ev_demand_score": 8.3, "influence_weight": 0.85},
    {"name": "旗山大道商业带", "category": "shopping_mall", "lat": 26.0234, "lng": 119.2345, "daily_flow": 18000, "ev_demand_score": 7.8, "influence_weight": 0.8},
]

EXTRA_ROADS = [
    {"road_name": "福飞路", "road_level": "main_road", "center_lat": 26.0823, "center_lng": 119.2956,
     "start_lat": 26.0923, "start_lng": 119.2856, "end_lat": 26.0723, "end_lng": 119.3056,
     "daily_flow": 42000, "ev_ratio": 0.075,
     "path": [[26.0923, 119.2856], [26.0873, 119.2906], [26.0823, 119.2956], [26.0773, 119.3006], [26.0723, 119.3056]]},
    {"road_name": "福马路", "road_level": "main_road", "center_lat": 26.0678, "center_lng": 119.3678,
     "start_lat": 26.0678, "start_lng": 119.3278, "end_lat": 26.0678, "end_lng": 119.4078,
     "daily_flow": 38000, "ev_ratio": 0.07,
     "path": [[26.0678, 119.3278], [26.0678, 119.3478], [26.0678, 119.3678], [26.0678, 119.3878], [26.0678, 119.4078]]},
    {"road_name": "江滨大道（北）", "road_level": "main_road", "center_lat": 26.0623, "center_lng": 119.3234,
     "start_lat": 26.0623, "start_lng": 119.2634, "end_lat": 26.0623, "end_lng": 119.3834,
     "daily_flow": 48000, "ev_ratio": 0.082,
     "path": [[26.0623, 119.2634], [26.0623, 119.2934], [26.0623, 119.3234], [26.0623, 119.3534], [26.0623, 119.3834]]},
    {"road_name": "金山大道", "road_level": "main_road", "center_lat": 26.0312, "center_lng": 119.2756,
     "start_lat": 26.0312, "start_lng": 119.2356, "end_lat": 26.0312, "end_lng": 119.3156,
     "daily_flow": 35000, "ev_ratio": 0.068,
     "path": [[26.0312, 119.2356], [26.0312, 119.2556], [26.0312, 119.2756], [26.0312, 119.2956], [26.0312, 119.3156]]},
    {"road_name": "二环路（北段）", "road_level": "secondary_road", "center_lat": 26.0934, "center_lng": 119.3234,
     "start_lat": 26.0934, "start_lng": 119.2834, "end_lat": 26.0934, "end_lng": 119.3634,
     "daily_flow": 52000, "ev_ratio": 0.088,
     "path": [[26.0934, 119.2834], [26.0934, 119.3034], [26.0934, 119.3234], [26.0934, 119.3434], [26.0934, 119.3634]]},
    {"road_name": "三环路（西段）", "road_level": "urban_expressway", "center_lat": 26.0567, "center_lng": 119.2456,
     "start_lat": 26.0867, "start_lng": 119.2456, "end_lat": 26.0267, "end_lng": 119.2456,
     "daily_flow": 68000, "ev_ratio": 0.092,
     "path": [[26.0867, 119.2456], [26.0767, 119.2456], [26.0667, 119.2456], [26.0567, 119.2456], [26.0467, 119.2456], [26.0267, 119.2456]]},
]

EXISTING_STATIONS = [
    {"name": "特来电·万达广场充电站", "lat": 26.0834, "lng": 119.2956, "total_score": 8.5},
    {"name": "国家电网·火车站充电站", "lat": 26.0823, "lng": 119.3345, "total_score": 9.0},
    {"name": "星星充电·东街口站", "lat": 26.0756, "lng": 119.3034, "total_score": 8.8},
    {"name": "特来电·南站充电站", "lat": 25.9812, "lng": 119.3234, "total_score": 9.2},
    {"name": "国家电网·金山充电站", "lat": 26.0312, "lng": 119.2756, "total_score": 8.2},
    {"name": "充电宝·仓山万达站", "lat": 26.0234, "lng": 119.2923, "total_score": 7.8},
]

def run():
    added_poi = 0
    for p in EXTRA_POIS:
        obj, created = POIData.objects.get_or_create(
            name=p['name'],
            defaults={
                'category': p['category'],
                'latitude': p['lat'],
                'longitude': p['lng'],
                'daily_flow': p['daily_flow'],
                'ev_demand_score': p['ev_demand_score'],
                'influence_weight': p['influence_weight'],
                'district': '福州市区',
            }
        )
        if created:
            added_poi += 1

    added_road = 0
    for r in EXTRA_ROADS:
        obj, created = TrafficFlow.objects.get_or_create(
            road_name=r['road_name'],
            defaults={
                'road_level': r['road_level'],
                'center_lat': r['center_lat'],
                'center_lng': r['center_lng'],
                'start_lat': r['start_lat'],
                'start_lng': r['start_lng'],
                'end_lat': r['end_lat'],
                'end_lng': r['end_lng'],
                'daily_flow': r['daily_flow'],
                'ev_ratio': r['ev_ratio'],
                'heat_weight': min(1.0, r['daily_flow'] / 70000),
                'path_json': json.dumps(r['path']),
            }
        )
        if created:
            added_road += 1

    added_station = 0
    for s in EXISTING_STATIONS:
        obj, created = CandidateLocation.objects.get_or_create(
            name=s['name'],
            defaults={
                'latitude': s['lat'],
                'longitude': s['lng'],
                'total_score': s['total_score'],
                'status': 'existing',
            }
        )
        if created:
            added_station += 1

    print(f"数据增强完成：新增POI {added_poi}个，新增道路 {added_road}条，新增充电站 {added_station}个")
    print(f"当前数据总量：POI {POIData.objects.count()}个，道路 {TrafficFlow.objects.count()}条，充电站 {CandidateLocation.objects.count()}个")

if __name__ == '__main__':
    run()
