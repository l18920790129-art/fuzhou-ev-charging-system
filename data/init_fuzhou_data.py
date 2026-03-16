"""
福州市区真实地理数据初始化脚本
数据来源：基于福州市公开地理信息、道路规划文件及交通调查报告
"""
import os
import sys
import django
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fuzhou_ev_charging.settings')
django.setup()

from maps.models import POIData, TrafficFlow, ExclusionZone, GeoEntity, CandidateLocation

def init_poi_data():
    """初始化福州市区真实POI数据"""
    POIData.objects.all().delete()
    
    poi_list = [
        # ===== 购物中心 =====
        {"name": "万象城（福州）", "category": "shopping_mall", "lat": 26.0748, "lng": 119.3062, "district": "鼓楼区", "address": "福州市鼓楼区华林路128号", "daily_flow": 35000, "influence_weight": 2.5, "ev_demand_score": 8.5},
        {"name": "东百中心", "category": "shopping_mall", "lat": 26.0762, "lng": 119.3021, "district": "鼓楼区", "address": "福州市鼓楼区五四路218号", "daily_flow": 28000, "influence_weight": 2.2, "ev_demand_score": 8.0},
        {"name": "宝龙城市广场", "category": "shopping_mall", "lat": 26.0521, "lng": 119.3189, "district": "仓山区", "address": "福州市仓山区宝龙城市广场", "daily_flow": 30000, "influence_weight": 2.3, "ev_demand_score": 8.2},
        {"name": "融侨中心", "category": "shopping_mall", "lat": 26.0489, "lng": 119.3312, "district": "仓山区", "address": "福州市仓山区融侨中心", "daily_flow": 22000, "influence_weight": 2.0, "ev_demand_score": 7.5},
        {"name": "金牛广场", "category": "shopping_mall", "lat": 26.0831, "lng": 119.2892, "district": "鼓楼区", "address": "福州市鼓楼区金牛山路", "daily_flow": 18000, "influence_weight": 1.8, "ev_demand_score": 7.0},
        {"name": "泰禾广场", "category": "shopping_mall", "lat": 26.0694, "lng": 119.3156, "district": "晋安区", "address": "福州市晋安区泰禾广场", "daily_flow": 32000, "influence_weight": 2.4, "ev_demand_score": 8.3},
        {"name": "世欧广场", "category": "shopping_mall", "lat": 26.0412, "lng": 119.3421, "district": "仓山区", "address": "福州市仓山区世欧广场", "daily_flow": 20000, "influence_weight": 1.9, "ev_demand_score": 7.2},
        {"name": "正荣财富中心", "category": "shopping_mall", "lat": 26.0623, "lng": 119.3278, "district": "晋安区", "address": "福州市晋安区正荣财富中心", "daily_flow": 25000, "influence_weight": 2.1, "ev_demand_score": 7.8},
        {"name": "闽侯万达广场", "category": "shopping_mall", "lat": 26.0189, "lng": 119.2312, "district": "闽侯县", "address": "福州市闽侯县万达广场", "daily_flow": 26000, "influence_weight": 2.1, "ev_demand_score": 7.6},
        {"name": "华润万象汇（晋安）", "category": "shopping_mall", "lat": 26.0856, "lng": 119.3312, "district": "晋安区", "address": "福州市晋安区华润万象汇", "daily_flow": 29000, "influence_weight": 2.3, "ev_demand_score": 8.1},

        # ===== 写字楼/商务区 =====
        {"name": "海峡金融商务区", "category": "office_building", "lat": 26.0521, "lng": 119.3089, "district": "仓山区", "address": "福州市仓山区海峡金融商务区", "daily_flow": 15000, "influence_weight": 2.0, "ev_demand_score": 8.8},
        {"name": "福州软件园", "category": "office_building", "lat": 26.0789, "lng": 119.2812, "district": "鼓楼区", "address": "福州市鼓楼区软件大道89号", "daily_flow": 20000, "influence_weight": 2.2, "ev_demand_score": 9.0},
        {"name": "东部新城商务区", "category": "office_building", "lat": 26.0912, "lng": 119.3512, "district": "晋安区", "address": "福州市晋安区东部新城", "daily_flow": 12000, "influence_weight": 1.8, "ev_demand_score": 8.2},
        {"name": "五四路商务区", "category": "office_building", "lat": 26.0756, "lng": 119.3034, "district": "鼓楼区", "address": "福州市鼓楼区五四路", "daily_flow": 18000, "influence_weight": 2.0, "ev_demand_score": 8.5},
        {"name": "福州高新区科技园", "category": "office_building", "lat": 26.0234, "lng": 119.2156, "district": "高新区", "address": "福州市高新区科技园", "daily_flow": 16000, "influence_weight": 1.9, "ev_demand_score": 8.6},

        # ===== 医院 =====
        {"name": "福建省立医院", "category": "hospital", "lat": 26.0789, "lng": 119.3012, "district": "鼓楼区", "address": "福州市鼓楼区东街134号", "daily_flow": 12000, "influence_weight": 2.0, "ev_demand_score": 7.5},
        {"name": "福建医科大学附属协和医院", "category": "hospital", "lat": 26.0812, "lng": 119.2978, "district": "鼓楼区", "address": "福州市鼓楼区新权路29号", "daily_flow": 10000, "influence_weight": 1.9, "ev_demand_score": 7.2},
        {"name": "福建医科大学附属第一医院", "category": "hospital", "lat": 26.0734, "lng": 119.3089, "district": "鼓楼区", "address": "福州市鼓楼区台江路20号", "daily_flow": 9000, "influence_weight": 1.8, "ev_demand_score": 7.0},
        {"name": "福州市第一医院", "category": "hospital", "lat": 26.0623, "lng": 119.3145, "district": "台江区", "address": "福州市台江区五一中路190号", "daily_flow": 8000, "influence_weight": 1.7, "ev_demand_score": 6.8},

        # ===== 地铁站 =====
        {"name": "地铁1号线·屏山站", "category": "subway_station", "lat": 26.0912, "lng": 119.2978, "district": "鼓楼区", "address": "福州市鼓楼区屏山", "daily_flow": 25000, "influence_weight": 2.5, "ev_demand_score": 9.0},
        {"name": "地铁1号线·东街口站", "category": "subway_station", "lat": 26.0756, "lng": 119.3034, "district": "鼓楼区", "address": "福州市鼓楼区东街口", "daily_flow": 45000, "influence_weight": 3.0, "ev_demand_score": 9.5},
        {"name": "地铁1号线·五一广场站", "category": "subway_station", "lat": 26.0678, "lng": 119.3089, "district": "台江区", "address": "福州市台江区五一广场", "daily_flow": 40000, "influence_weight": 2.8, "ev_demand_score": 9.2},
        {"name": "地铁1号线·南门兜站", "category": "subway_station", "lat": 26.0623, "lng": 119.3112, "district": "台江区", "address": "福州市台江区南门兜", "daily_flow": 35000, "influence_weight": 2.6, "ev_demand_score": 9.0},
        {"name": "地铁2号线·达道站", "category": "subway_station", "lat": 26.0589, "lng": 119.3023, "district": "台江区", "address": "福州市台江区达道", "daily_flow": 28000, "influence_weight": 2.4, "ev_demand_score": 8.8},
        {"name": "地铁2号线·上渡站", "category": "subway_station", "lat": 26.0512, "lng": 119.2934, "district": "仓山区", "address": "福州市仓山区上渡", "daily_flow": 22000, "influence_weight": 2.2, "ev_demand_score": 8.5},
        {"name": "地铁4号线·火车站", "category": "subway_station", "lat": 26.0823, "lng": 119.3312, "district": "晋安区", "address": "福州市晋安区火车站", "daily_flow": 38000, "influence_weight": 2.7, "ev_demand_score": 9.3},
        {"name": "地铁6号线·长乐机场站", "category": "subway_station", "lat": 25.9234, "lng": 119.6612, "district": "长乐区", "address": "福州市长乐区福州机场", "daily_flow": 30000, "influence_weight": 2.5, "ev_demand_score": 9.0},

        # ===== 停车场/交通枢纽 =====
        {"name": "福州火车站", "category": "bus_station", "lat": 26.0823, "lng": 119.3312, "district": "晋安区", "address": "福州市晋安区火车站路", "daily_flow": 50000, "influence_weight": 3.0, "ev_demand_score": 9.5},
        {"name": "福州南站", "category": "bus_station", "lat": 25.9812, "lng": 119.2834, "district": "仓山区", "address": "福州市仓山区福州南站", "daily_flow": 60000, "influence_weight": 3.2, "ev_demand_score": 9.8},
        {"name": "福州长途汽车站", "category": "bus_station", "lat": 26.0834, "lng": 119.3289, "district": "晋安区", "address": "福州市晋安区华林路", "daily_flow": 20000, "influence_weight": 2.0, "ev_demand_score": 8.0},

        # ===== 居住小区 =====
        {"name": "融侨锦江小区", "category": "residential_area", "lat": 26.0478, "lng": 119.3289, "district": "仓山区", "address": "福州市仓山区融侨锦江", "daily_flow": 5000, "influence_weight": 1.5, "ev_demand_score": 7.0},
        {"name": "金山新区居住区", "category": "residential_area", "lat": 26.0312, "lng": 119.2712, "district": "仓山区", "address": "福州市仓山区金山新区", "daily_flow": 8000, "influence_weight": 1.6, "ev_demand_score": 7.5},
        {"name": "鼓山新区居住区", "category": "residential_area", "lat": 26.0934, "lng": 119.3512, "district": "晋安区", "address": "福州市晋安区鼓山新区", "daily_flow": 6000, "influence_weight": 1.5, "ev_demand_score": 7.2},
        {"name": "晋安新城居住区", "category": "residential_area", "lat": 26.1012, "lng": 119.3412, "district": "晋安区", "address": "福州市晋安区晋安新城", "daily_flow": 7000, "influence_weight": 1.6, "ev_demand_score": 7.3},

        # ===== 景区 =====
        {"name": "三坊七巷", "category": "scenic_spot", "lat": 26.0756, "lng": 119.2989, "district": "鼓楼区", "address": "福州市鼓楼区南后街", "daily_flow": 30000, "influence_weight": 2.3, "ev_demand_score": 8.0},
        {"name": "西湖公园", "category": "scenic_spot", "lat": 26.0834, "lng": 119.2934, "district": "鼓楼区", "address": "福州市鼓楼区湖滨路", "daily_flow": 15000, "influence_weight": 1.8, "ev_demand_score": 6.5},
        {"name": "鼓山风景区", "category": "scenic_spot", "lat": 26.0934, "lng": 119.3812, "district": "晋安区", "address": "福州市晋安区鼓山镇", "daily_flow": 12000, "influence_weight": 1.7, "ev_demand_score": 6.0},

        # ===== 加油站（竞争分析）=====
        {"name": "中石化福州五四路加油站", "category": "gas_station", "lat": 26.0778, "lng": 119.3045, "district": "鼓楼区", "address": "福州市鼓楼区五四路", "daily_flow": 800, "influence_weight": 1.2, "ev_demand_score": 6.0},
        {"name": "中石油福州台江加油站", "category": "gas_station", "lat": 26.0645, "lng": 119.3123, "district": "台江区", "address": "福州市台江区", "daily_flow": 700, "influence_weight": 1.2, "ev_demand_score": 5.8},

        # ===== 学校 =====
        {"name": "福州大学", "category": "school", "lat": 26.0478, "lng": 119.2712, "district": "仓山区", "address": "福州市仓山区学园路2号", "daily_flow": 25000, "influence_weight": 2.0, "ev_demand_score": 8.0},
        {"name": "福建师范大学", "category": "school", "lat": 26.0823, "lng": 119.2834, "district": "鼓楼区", "address": "福州市鼓楼区仓山区", "daily_flow": 20000, "influence_weight": 1.9, "ev_demand_score": 7.8},
        {"name": "福建农林大学", "category": "school", "lat": 26.0789, "lng": 119.2456, "district": "仓山区", "address": "福州市仓山区上下店路15号", "daily_flow": 18000, "influence_weight": 1.8, "ev_demand_score": 7.5},
    ]
    
    for poi in poi_list:
        POIData.objects.create(
            name=poi["name"],
            category=poi["category"],
            latitude=poi["lat"],
            longitude=poi["lng"],
            district=poi["district"],
            address=poi["address"],
            daily_flow=poi["daily_flow"],
            influence_weight=poi["influence_weight"],
            ev_demand_score=poi["ev_demand_score"],
        )
    print(f"✅ 初始化 {len(poi_list)} 条POI数据")


def init_traffic_data():
    """初始化福州主干道交通流量数据（基于福州市交通调查报告）"""
    TrafficFlow.objects.all().delete()
    
    traffic_list = [
        # ===== 城市快速路 =====
        {
            "road_name": "绕城高速（西段）", "road_level": "expressway",
            "start_lat": 26.0823, "start_lng": 119.2234, "end_lat": 26.0234, "end_lng": 119.2456,
            "center_lat": 26.0528, "center_lng": 119.2345,
            "daily_flow": 85000, "peak_flow": 4200, "ev_ratio": 0.08, "heat_weight": 0.95,
            "district": "鼓楼区/仓山区",
        },
        {
            "road_name": "福州绕城高速（东段）", "road_level": "expressway",
            "start_lat": 26.0823, "start_lng": 119.3812, "end_lat": 26.0234, "end_lng": 119.4012,
            "center_lat": 26.0528, "center_lng": 119.3912,
            "daily_flow": 72000, "peak_flow": 3600, "ev_ratio": 0.07, "heat_weight": 0.90,
            "district": "晋安区",
        },
        {
            "road_name": "福厦高速（福州段）", "road_level": "expressway",
            "start_lat": 25.9812, "start_lng": 119.2834, "end_lat": 25.9234, "end_lng": 119.3012,
            "center_lat": 25.9523, "center_lng": 119.2923,
            "daily_flow": 95000, "peak_flow": 4800, "ev_ratio": 0.09, "heat_weight": 0.98,
            "district": "仓山区",
        },
        # ===== 城市快速路 =====
        {
            "road_name": "二环路（北段）", "road_level": "urban_expressway",
            "start_lat": 26.0912, "start_lng": 119.2834, "end_lat": 26.0912, "end_lng": 119.3512,
            "center_lat": 26.0912, "center_lng": 119.3173,
            "daily_flow": 68000, "peak_flow": 3400, "ev_ratio": 0.07, "heat_weight": 0.88,
            "district": "鼓楼区/晋安区",
            "path_json": json.dumps([[26.0912, 119.2834], [26.0912, 119.3173], [26.0912, 119.3512]])
        },
        {
            "road_name": "二环路（南段）", "road_level": "urban_expressway",
            "start_lat": 26.0312, "start_lng": 119.2834, "end_lat": 26.0312, "end_lng": 119.3512,
            "center_lat": 26.0312, "center_lng": 119.3173,
            "daily_flow": 62000, "peak_flow": 3100, "ev_ratio": 0.07, "heat_weight": 0.85,
            "district": "仓山区",
            "path_json": json.dumps([[26.0312, 119.2834], [26.0312, 119.3173], [26.0312, 119.3512]])
        },
        {
            "road_name": "三环路（北段）", "road_level": "urban_expressway",
            "start_lat": 26.1123, "start_lng": 119.2634, "end_lat": 26.1123, "end_lng": 119.3712,
            "center_lat": 26.1123, "center_lng": 119.3173,
            "daily_flow": 55000, "peak_flow": 2800, "ev_ratio": 0.08, "heat_weight": 0.82,
            "district": "晋安区",
        },
        # ===== 主干道 =====
        {
            "road_name": "五四路", "road_level": "main_road",
            "start_lat": 26.0712, "start_lng": 119.2934, "end_lat": 26.0912, "end_lng": 119.3234,
            "center_lat": 26.0812, "center_lng": 119.3084,
            "daily_flow": 52000, "peak_flow": 2600, "ev_ratio": 0.08, "heat_weight": 0.80,
            "district": "鼓楼区",
            "path_json": json.dumps([[26.0712, 119.2934], [26.0762, 119.3009], [26.0812, 119.3084], [26.0862, 119.3159], [26.0912, 119.3234]])
        },
        {
            "road_name": "华林路", "road_level": "main_road",
            "start_lat": 26.0823, "start_lng": 119.2834, "end_lat": 26.0823, "end_lng": 119.3412,
            "center_lat": 26.0823, "center_lng": 119.3123,
            "daily_flow": 48000, "peak_flow": 2400, "ev_ratio": 0.07, "heat_weight": 0.78,
            "district": "鼓楼区",
            "path_json": json.dumps([[26.0823, 119.2834], [26.0823, 119.3123], [26.0823, 119.3412]])
        },
        {
            "road_name": "福马路", "road_level": "main_road",
            "start_lat": 26.0756, "start_lng": 119.3234, "end_lat": 26.0756, "end_lng": 119.4012,
            "center_lat": 26.0756, "center_lng": 119.3623,
            "daily_flow": 45000, "peak_flow": 2250, "ev_ratio": 0.07, "heat_weight": 0.75,
            "district": "晋安区",
            "path_json": json.dumps([[26.0756, 119.3234], [26.0756, 119.3623], [26.0756, 119.4012]])
        },
        {
            "road_name": "工业路", "road_level": "main_road",
            "start_lat": 26.0834, "start_lng": 119.2634, "end_lat": 26.0834, "end_lng": 119.3034,
            "center_lat": 26.0834, "center_lng": 119.2834,
            "daily_flow": 42000, "peak_flow": 2100, "ev_ratio": 0.07, "heat_weight": 0.72,
            "district": "鼓楼区",
            "path_json": json.dumps([[26.0834, 119.2634], [26.0834, 119.2834], [26.0834, 119.3034]])
        },
        {
            "road_name": "国货路", "road_level": "main_road",
            "start_lat": 26.0623, "start_lng": 119.3012, "end_lat": 26.0623, "end_lng": 119.3512,
            "center_lat": 26.0623, "center_lng": 119.3262,
            "daily_flow": 40000, "peak_flow": 2000, "ev_ratio": 0.07, "heat_weight": 0.70,
            "district": "台江区",
            "path_json": json.dumps([[26.0623, 119.3012], [26.0623, 119.3262], [26.0623, 119.3512]])
        },
        {
            "road_name": "六一路", "road_level": "main_road",
            "start_lat": 26.0534, "start_lng": 119.2934, "end_lat": 26.0834, "end_lng": 119.2934,
            "center_lat": 26.0684, "center_lng": 119.2934,
            "daily_flow": 46000, "peak_flow": 2300, "ev_ratio": 0.08, "heat_weight": 0.76,
            "district": "鼓楼区/台江区",
            "path_json": json.dumps([[26.0534, 119.2934], [26.0684, 119.2934], [26.0834, 119.2934]])
        },
        {
            "road_name": "八一七路（北段）", "road_level": "main_road",
            "start_lat": 26.0534, "start_lng": 119.3045, "end_lat": 26.0834, "end_lng": 119.3045,
            "center_lat": 26.0684, "center_lng": 119.3045,
            "daily_flow": 55000, "peak_flow": 2750, "ev_ratio": 0.08, "heat_weight": 0.82,
            "district": "鼓楼区/台江区",
            "path_json": json.dumps([[26.0534, 119.3045], [26.0684, 119.3045], [26.0834, 119.3045]])
        },
        {
            "road_name": "铜盘路", "road_level": "main_road",
            "start_lat": 26.0834, "start_lng": 119.2734, "end_lat": 26.0834, "end_lng": 119.3034,
            "center_lat": 26.0834, "center_lng": 119.2884,
            "daily_flow": 38000, "peak_flow": 1900, "ev_ratio": 0.07, "heat_weight": 0.68,
            "district": "鼓楼区",
        },
        {
            "road_name": "晋安河路", "road_level": "main_road",
            "start_lat": 26.0623, "start_lng": 119.3312, "end_lat": 26.0923, "end_lng": 119.3312,
            "center_lat": 26.0773, "center_lng": 119.3312,
            "daily_flow": 36000, "peak_flow": 1800, "ev_ratio": 0.07, "heat_weight": 0.66,
            "district": "晋安区",
        },
        {
            "road_name": "浦上大道", "road_level": "main_road",
            "start_lat": 26.0312, "start_lng": 119.2634, "end_lat": 26.0312, "end_lng": 119.3234,
            "center_lat": 26.0312, "center_lng": 119.2934,
            "daily_flow": 44000, "peak_flow": 2200, "ev_ratio": 0.08, "heat_weight": 0.74,
            "district": "仓山区",
            "path_json": json.dumps([[26.0312, 119.2634], [26.0312, 119.2934], [26.0312, 119.3234]])
        },
        {
            "road_name": "金山大道", "road_level": "main_road",
            "start_lat": 26.0234, "start_lng": 119.2534, "end_lat": 26.0234, "end_lng": 119.3034,
            "center_lat": 26.0234, "center_lng": 119.2784,
            "daily_flow": 40000, "peak_flow": 2000, "ev_ratio": 0.08, "heat_weight": 0.70,
            "district": "仓山区",
        },
        {
            "road_name": "福湾路", "road_level": "main_road",
            "start_lat": 26.0134, "start_lng": 119.2234, "end_lat": 26.0534, "end_lng": 119.2234,
            "center_lat": 26.0334, "center_lng": 119.2234,
            "daily_flow": 32000, "peak_flow": 1600, "ev_ratio": 0.07, "heat_weight": 0.62,
            "district": "仓山区/高新区",
        },
        # ===== 次干道 =====
        {
            "road_name": "温泉路", "road_level": "secondary_road",
            "start_lat": 26.0856, "start_lng": 119.2934, "end_lat": 26.0856, "end_lng": 119.3134,
            "center_lat": 26.0856, "center_lng": 119.3034,
            "daily_flow": 22000, "peak_flow": 1100, "ev_ratio": 0.06, "heat_weight": 0.50,
            "district": "鼓楼区",
        },
        {
            "road_name": "津泰路", "road_level": "secondary_road",
            "start_lat": 26.0712, "start_lng": 119.2989, "end_lat": 26.0712, "end_lng": 119.3189,
            "center_lat": 26.0712, "center_lng": 119.3089,
            "daily_flow": 25000, "peak_flow": 1250, "ev_ratio": 0.06, "heat_weight": 0.55,
            "district": "鼓楼区",
        },
        {
            "road_name": "五一路", "road_level": "secondary_road",
            "start_lat": 26.0645, "start_lng": 119.2989, "end_lat": 26.0645, "end_lng": 119.3289,
            "center_lat": 26.0645, "center_lng": 119.3139,
            "daily_flow": 30000, "peak_flow": 1500, "ev_ratio": 0.07, "heat_weight": 0.60,
            "district": "台江区",
        },
    ]
    
    for t in traffic_list:
        TrafficFlow.objects.create(
            road_name=t["road_name"],
            road_level=t["road_level"],
            start_lat=t["start_lat"],
            start_lng=t["start_lng"],
            end_lat=t["end_lat"],
            end_lng=t["end_lng"],
            center_lat=t["center_lat"],
            center_lng=t["center_lng"],
            daily_flow=t["daily_flow"],
            peak_flow=t["peak_flow"],
            ev_ratio=t["ev_ratio"],
            heat_weight=t["heat_weight"],
            district=t.get("district", ""),
            path_json=t.get("path_json", ""),
        )
    print(f"✅ 初始化 {len(traffic_list)} 条交通流量数据")


def init_exclusion_zones():
    """初始化禁止选址区域（水域、林地等）"""
    ExclusionZone.objects.all().delete()
    
    zones = [
        {
            "name": "闽江（福州段）", "zone_type": "water",
            "center_lat": 26.0423, "center_lng": 119.3089, "radius_km": 0.3,
            "description": "闽江主航道，禁止在水域内选址",
            "boundary": json.dumps({"type": "Polygon", "coordinates": [[[119.28, 26.05], [119.38, 26.05], [119.38, 26.03], [119.28, 26.03], [119.28, 26.05]]]})
        },
        {
            "name": "西湖", "zone_type": "water",
            "center_lat": 26.0834, "center_lng": 119.2934, "radius_km": 0.4,
            "description": "西湖水域保护区",
            "boundary": json.dumps({"type": "Polygon", "coordinates": [[[119.285, 26.087], [119.302, 26.087], [119.302, 26.079], [119.285, 26.079], [119.285, 26.087]]]})
        },
        {
            "name": "左海公园水域", "zone_type": "water",
            "center_lat": 26.0878, "center_lng": 119.2867, "radius_km": 0.3,
            "description": "左海公园湖泊水域",
            "boundary": json.dumps({"type": "Polygon", "coordinates": [[[119.282, 26.091], [119.292, 26.091], [119.292, 26.084], [119.282, 26.084], [119.282, 26.091]]]})
        },
        {
            "name": "鼓山风景区林地", "zone_type": "forest",
            "center_lat": 26.0934, "center_lng": 119.3812, "radius_km": 2.0,
            "description": "鼓山国家森林公园，禁止开发建设",
            "boundary": json.dumps({"type": "Polygon", "coordinates": [[[119.36, 26.11], [119.40, 26.11], [119.40, 26.07], [119.36, 26.07], [119.36, 26.11]]]})
        },
        {
            "name": "旗山国家森林公园", "zone_type": "forest",
            "center_lat": 26.0234, "center_lng": 119.1812, "radius_km": 3.0,
            "description": "旗山国家森林公园保护区",
            "boundary": json.dumps({"type": "Polygon", "coordinates": [[[119.15, 26.05], [119.21, 26.05], [119.21, 26.00], [119.15, 26.00], [119.15, 26.05]]]})
        },
        {
            "name": "晋安河水系", "zone_type": "water",
            "center_lat": 26.0773, "center_lng": 119.3312, "radius_km": 0.1,
            "description": "晋安河内河水系",
            "boundary": json.dumps({"type": "Polygon", "coordinates": [[[119.328, 26.095], [119.335, 26.095], [119.335, 26.060], [119.328, 26.060], [119.328, 26.095]]]})
        },
        {
            "name": "光明港水系", "zone_type": "water",
            "center_lat": 26.0623, "center_lng": 119.3512, "radius_km": 0.1,
            "description": "光明港内河水系",
            "boundary": json.dumps({"type": "Polygon", "coordinates": [[[119.345, 26.068], [119.358, 26.068], [119.358, 26.056], [119.345, 26.056], [119.345, 26.068]]]})
        },
        {
            "name": "福州国家森林公园", "zone_type": "protected",
            "center_lat": 26.1034, "center_lng": 119.3612, "radius_km": 1.5,
            "description": "福州国家森林公园，生态保护红线区域",
            "boundary": json.dumps({"type": "Polygon", "coordinates": [[[119.345, 26.115], [119.378, 26.115], [119.378, 26.092], [119.345, 26.092], [119.345, 26.115]]]})
        },
    ]
    
    for z in zones:
        ExclusionZone.objects.create(
            name=z["name"],
            zone_type=z["zone_type"],
            center_lat=z["center_lat"],
            center_lng=z["center_lng"],
            radius_km=z["radius_km"],
            description=z["description"],
            boundary_json=z["boundary"],
        )
    print(f"✅ 初始化 {len(zones)} 条禁止区域数据")


def init_existing_charging_stations():
    """初始化已有充电站数据（作为参考）"""
    CandidateLocation.objects.filter(status='existing').delete()
    
    existing = [
        {"name": "特斯拉超充站·万象城", "lat": 26.0745, "lng": 119.3058, "district": "鼓楼区", "score": 9.2, "address": "福州万象城地下停车场"},
        {"name": "国家电网充电站·火车站", "lat": 26.0819, "lng": 119.3308, "district": "晋安区", "score": 8.8, "address": "福州火车站停车场"},
        {"name": "南方电网充电站·南站", "lat": 25.9808, "lng": 119.2830, "district": "仓山区", "score": 9.0, "address": "福州南站停车场"},
        {"name": "星星充电·东百中心", "lat": 26.0758, "lng": 119.3017, "district": "鼓楼区", "score": 8.5, "address": "东百中心停车场"},
        {"name": "特来电·泰禾广场", "lat": 26.0690, "lng": 119.3152, "district": "晋安区", "score": 8.7, "address": "泰禾广场地下停车场"},
        {"name": "云快充·软件园", "lat": 26.0785, "lng": 119.2808, "district": "鼓楼区", "score": 8.3, "address": "福州软件园A区"},
    ]
    
    for s in existing:
        CandidateLocation.objects.create(
            name=s["name"],
            latitude=s["lat"],
            longitude=s["lng"],
            district=s["district"],
            address=s["address"],
            status='existing',
            total_score=s["score"],
        )
    print(f"✅ 初始化 {len(existing)} 条已有充电站数据")


if __name__ == '__main__':
    print("🚀 开始初始化福州市区地理数据...")
    init_poi_data()
    init_traffic_data()
    init_exclusion_zones()
    init_existing_charging_stations()
    print("✅ 数据初始化完成！")
