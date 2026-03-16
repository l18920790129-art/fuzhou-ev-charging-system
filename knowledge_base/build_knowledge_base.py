"""
ChromaDB 知识向量库 + 知识图谱构建脚本
知识来源：充电桩选址规范、福州城市规划文件、新能源汽车行业报告
"""
import os
import sys
import json
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fuzhou_ev_charging.settings')
django.setup()

from django.conf import settings
import chromadb
from chromadb.config import Settings as ChromaSettings
from analysis.models import KnowledgeGraphNode, KnowledgeGraphEdge

# ============================================================
# 充电桩选址专业知识文档库
# ============================================================
KNOWLEDGE_DOCUMENTS = [
    {
        "id": "std_001",
        "content": """《电动汽车充换电设施规划导则》（GB/T 51313-2018）核心要求：
充电设施选址应遵循以下原则：
1. 优先选择在大型商业综合体、交通枢纽、居住小区、办公园区等人流密集区域附近；
2. 充电站服务半径：城市核心区不超过1公里，城市一般区域不超过3公里；
3. 选址应避开水域、林地、坡度超过8%的坡地、文物保护区等区域；
4. 充电站用地面积：快充站不低于200平方米，慢充桩可结合停车场设置；
5. 与加油站、变电站等危险设施保持安全距离（不低于50米）；
6. 应具备完善的配电条件，距10kV配电线路不超过500米。""",
        "metadata": {"source": "国家标准", "type": "规范标准", "category": "选址规范", "year": "2018"}
    },
    {
        "id": "std_002",
        "content": """福州市电动汽车充电基础设施建设规划（2021-2025）：
规划目标：
- 到2025年，全市公共充电桩达到5万个，其中快充桩占比不低于30%；
- 重点布局区域：鼓楼区、台江区商业核心区，仓山区金融商务区，晋安区东部新城；
- 优先在地铁站500米范围内、大型商业综合体、交通枢纽配套建设充电设施；
- 推进"充电桩进小区"工程，新建小区按每户0.2个车位配建充电桩；
- 高速公路服务区实现充电设施全覆盖，平均间距不超过50公里。
布局策略：
- 商业区：以快充为主，满足短时停留充电需求；
- 居住区：以慢充为主，满足夜间充电需求；
- 交通枢纽：快慢结合，满足长途出行需求。""",
        "metadata": {"source": "福州市政府规划", "type": "地方规划", "category": "城市规划", "year": "2021"}
    },
    {
        "id": "std_003",
        "content": """充电桩选址评估体系（行业最佳实践）：
综合评分维度：
1. 交通流量评分（权重25%）：
   - 日均车流量>5万辆：9-10分
   - 日均车流量3-5万辆：7-8分
   - 日均车流量1-3万辆：5-6分
   - 日均车流量<1万辆：3-4分
2. POI密度评分（权重30%）：
   - 500米内POI数量>20个且含高等级POI：9-10分
   - 500米内POI数量10-20个：7-8分
   - 500米内POI数量5-10个：5-6分
3. 可达性评分（权重20%）：
   - 距主干道<100米：9-10分
   - 距主干道100-300米：7-8分
   - 距主干道300-500米：5-6分
4. 竞争分析评分（权重15%）：
   - 1公里内无竞争充电站：9-10分
   - 1公里内有1-2个竞争站：6-8分
   - 1公里内有3个以上竞争站：3-5分
5. 配电条件评分（权重10%）：
   - 距变电站<300米：9-10分
   - 距变电站300-500米：7-8分""",
        "metadata": {"source": "行业报告", "type": "评估标准", "category": "评分体系", "year": "2023"}
    },
    {
        "id": "poi_001",
        "content": """POI类型对充电桩需求影响分析：
高需求POI类型（充电需求评分8-10分）：
- 购物中心/商业综合体：停留时间1-3小时，适合快充，日均EV需求50-200次
- 交通枢纽（火车站、机场、地铁站）：高频次进出，需要快充，日均EV需求100-500次
- 写字楼/商务园区：停留时间8小时以上，适合慢充，日均EV需求30-100次
- 大型停车场：停留时间不定，快慢结合，日均EV需求20-80次

中需求POI类型（充电需求评分6-8分）：
- 医院：停留时间1-4小时，适合快充，日均EV需求20-60次
- 酒店：停留时间8小时以上，适合慢充，日均EV需求15-50次
- 学校/大学：停留时间较长，适合慢充，日均EV需求10-40次
- 景区：停留时间2-5小时，适合快充，日均EV需求20-80次

低需求POI类型（充电需求评分4-6分）：
- 居住小区：夜间慢充为主，日均EV需求5-20次
- 加油站：竞争关系，需谨慎评估""",
        "metadata": {"source": "行业研究", "type": "需求分析", "category": "POI分析", "year": "2023"}
    },
    {
        "id": "traffic_001",
        "content": """交通流量与充电需求关系研究（福州市交通调查报告2022）：
福州市主要道路交通特征：
1. 城市快速路（二环、三环）：日均车流量5-8万辆，EV占比约7-9%，充电需求高
2. 主干道（五四路、华林路、八一七路等）：日均车流量3-6万辆，EV占比约6-8%
3. 次干道：日均车流量1-3万辆，EV占比约5-7%

充电需求热点区域分析：
- 鼓楼区商业核心：五四路、东街口周边，日均EV充电需求约800-1200次
- 台江区商业区：五一广场、南门兜周边，日均EV充电需求约600-900次
- 晋安区交通枢纽：火车站、泰禾周边，日均EV充电需求约700-1000次
- 仓山区金融商务区：海峡金融商务区周边，日均EV充电需求约400-600次
- 高新区：软件园、大学城周边，日均EV充电需求约300-500次

峰值时段：
- 工作日早高峰（7:30-9:00）：充电需求占全天15%
- 工作日晚高峰（17:30-19:30）：充电需求占全天25%
- 周末午间（11:00-14:00）：充电需求占全天20%""",
        "metadata": {"source": "福州市交通调查报告", "type": "交通分析", "category": "流量分析", "year": "2022"}
    },
    {
        "id": "case_001",
        "content": """福州充电桩成功选址案例分析：
案例1：万象城充电站（特斯拉超充）
- 位置：鼓楼区华林路128号万象城地下停车场
- 选址依据：日均客流3.5万人次，停留时间1-3小时，EV用户比例高（约15%），
  距五四路主干道200米，配电条件优良，1公里内无竞争快充站
- 运营效果：日均充电次数180次，利用率达75%，月营收约12万元

案例2：福州南站充电站（国家电网）
- 位置：仓山区福州南站停车场
- 选址依据：日均旅客6万人次，长途出行EV用户充电需求强烈，
  高速公路出入口附近，交通便利，配套设施完善
- 运营效果：日均充电次数240次，利用率达80%，月营收约18万元

案例3：软件园充电站（云快充）
- 位置：鼓楼区软件大道89号福州软件园
- 选址依据：日均员工2万人，EV拥有率约20%，停留时间8小时以上，
  适合慢充，夜间充电需求旺盛
- 运营效果：日均充电次数120次，利用率达65%，月营收约8万元""",
        "metadata": {"source": "运营案例", "type": "案例分析", "category": "成功案例", "year": "2023"}
    },
    {
        "id": "policy_001",
        "content": """福建省新能源汽车推广政策（2023-2025）：
主要政策措施：
1. 购车补贴：省级补贴每辆EV最高1万元，福州市额外补贴5000元
2. 充电优惠：EV充电电价享受谷电价格，约0.35元/度（较商业用电低40%）
3. 路权优惠：EV享受不限行政策，部分路段专用车道
4. 停车优惠：公共停车场EV停车费减半

充电基础设施补贴政策：
- 公共快充桩建设补贴：每桩最高补贴2万元
- 公共慢充桩建设补贴：每桩最高补贴0.5万元
- 充电站运营补贴：按充电量补贴0.1元/度，前三年有效

市场预测：
- 2024年福州EV保有量预计达35万辆，占汽车总量15%
- 2025年福州EV保有量预计达50万辆，占汽车总量20%
- 充电桩缺口：按1:3桩车比，2025年需新增公共充电桩约1.2万个""",
        "metadata": {"source": "政策文件", "type": "政策分析", "category": "政策环境", "year": "2023"}
    },
    {
        "id": "tech_001",
        "content": """充电桩技术规格与选址配电要求：
快充桩（DC直流）：
- 功率规格：60kW、120kW、180kW、360kW
- 充电时间：30分钟补充200-400公里续航
- 配电需求：120kW桩需400V三相电，配电容量不低于150kVA
- 适用场景：商业区、交通枢纽、高速服务区

慢充桩（AC交流）：
- 功率规格：7kW、11kW、22kW
- 充电时间：6-10小时充满
- 配电需求：7kW桩需220V单相电，11kW需三相电
- 适用场景：居住小区、写字楼、酒店

超充桩（大功率DC）：
- 功率规格：480kW、600kW（V4超充）
- 充电时间：15分钟补充300公里续航
- 配电需求：需专用变压器，容量不低于500kVA
- 适用场景：高速服务区、大型商业综合体

选址配电评估要点：
- 距10kV变电站距离：<300米最优，300-500米良好，>500米需评估增容成本
- 地块用电容量：需预留充电站用电容量的150%作为余量
- 电网接入方式：优先选择有专用变压器或可增容的地块""",
        "metadata": {"source": "技术规范", "type": "技术标准", "category": "技术要求", "year": "2023"}
    },
    {
        "id": "district_001",
        "content": """福州各区充电桩需求特征分析：
鼓楼区：
- 特征：商业核心区，人口密度高，EV用户收入水平高
- 需求：快充为主，重点布局商业综合体、写字楼周边
- 推荐区域：五四路商圈、东街口、软件园、西湖周边
- 预计需求：公共快充桩2000个，慢充桩3000个

台江区：
- 特征：商业零售集中，交通枢纽密集
- 需求：快慢结合，重点布局商业街区和交通节点
- 推荐区域：五一广场、南门兜、台江万达
- 预计需求：公共快充桩1500个，慢充桩2000个

仓山区：
- 特征：大学城、金融商务区、居住区混合
- 需求：慢充为主，商务区快充补充
- 推荐区域：海峡金融商务区、福州大学周边、金山新区
- 预计需求：公共快充桩1800个，慢充桩4000个

晋安区：
- 特征：交通枢纽（火车站）、新兴商业区
- 需求：快充为主，交通枢纽配套
- 推荐区域：火车站周边、泰禾广场、东部新城
- 预计需求：公共快充桩1600个，慢充桩2500个

高新区：
- 特征：科技园区、高校聚集
- 需求：慢充为主，员工通勤充电
- 推荐区域：软件园、高新区科技园、大学城
- 预计需求：公共快充桩800个，慢充桩2000个""",
        "metadata": {"source": "市场研究", "type": "区域分析", "category": "需求分析", "year": "2023"}
    },
    {
        "id": "env_001",
        "content": """充电桩选址环境影响评估要点：
禁止选址区域（红线）：
1. 水域及岸线保护区：距水体边界不少于30米
2. 生态保护红线区域：国家级/省级自然保护区、森林公园核心区
3. 文物保护单位：距文物保护单位建设控制地带边界不少于50米
4. 军事设施保护区：禁止进入
5. 坡度>15%的山地：施工困难，安全风险高

限制选址区域（黄线）：
1. 坡度8%-15%的坡地：需做地基处理
2. 地质灾害易发区：需进行地质勘察
3. 洪涝风险区：需抬高基础，做防洪措施
4. 高压输电线路走廊：距高压线水平距离不少于10米

优先选址区域（绿线）：
1. 大型停车场配套区域：利用现有基础设施
2. 商业综合体地下停车场：客流稳定，配电条件好
3. 交通枢纽配套停车场：需求旺盛，政策支持
4. 工业园区/科技园区：用电需求集中，配电条件优良""",
        "metadata": {"source": "环境规范", "type": "环境评估", "category": "选址约束", "year": "2022"}
    },
]


def build_chroma_knowledge_base():
    """构建ChromaDB向量知识库"""
    persist_dir = settings.CHROMA_PERSIST_DIR
    os.makedirs(persist_dir, exist_ok=True)
    
    client = chromadb.PersistentClient(path=persist_dir)
    
    # 删除已有集合（重建）
    try:
        client.delete_collection("ev_charging_knowledge")
    except:
        pass
    
    collection = client.create_collection(
        name="ev_charging_knowledge",
        metadata={"hnsw:space": "cosine"}
    )
    
    # 批量添加文档
    ids = [doc["id"] for doc in KNOWLEDGE_DOCUMENTS]
    documents = [doc["content"] for doc in KNOWLEDGE_DOCUMENTS]
    metadatas = [doc["metadata"] for doc in KNOWLEDGE_DOCUMENTS]
    
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    
    print(f"✅ ChromaDB知识库构建完成，共 {len(documents)} 条知识文档")
    return collection


def build_knowledge_graph():
    """构建知识图谱（存入PostgreSQL）"""
    KnowledgeGraphEdge.objects.all().delete()
    KnowledgeGraphNode.objects.all().delete()
    
    # 定义节点
    nodes_data = [
        # 影响因素节点
        {"node_id": "factor_traffic", "name": "交通流量", "node_type": "factor", "properties": {"weight": 0.25, "description": "道路日均车流量和峰值流量"}},
        {"node_id": "factor_poi", "name": "POI密度", "node_type": "factor", "properties": {"weight": 0.30, "description": "周边兴趣点数量和质量"}},
        {"node_id": "factor_accessibility", "name": "可达性", "node_type": "factor", "properties": {"weight": 0.20, "description": "距主干道距离和交通便利程度"}},
        {"node_id": "factor_competition", "name": "竞争分析", "node_type": "factor", "properties": {"weight": 0.15, "description": "周边已有充电站数量和覆盖情况"}},
        {"node_id": "factor_power", "name": "配电条件", "node_type": "factor", "properties": {"weight": 0.10, "description": "距变电站距离和用电容量"}},
        
        # POI类型节点
        {"node_id": "poi_shopping", "name": "购物中心", "node_type": "poi_type", "properties": {"ev_demand": 8.5, "stay_time": "1-3小时", "charge_type": "快充"}},
        {"node_id": "poi_office", "name": "写字楼", "node_type": "poi_type", "properties": {"ev_demand": 8.8, "stay_time": "8小时+", "charge_type": "慢充"}},
        {"node_id": "poi_transit", "name": "交通枢纽", "node_type": "poi_type", "properties": {"ev_demand": 9.5, "stay_time": "0.5-2小时", "charge_type": "快充"}},
        {"node_id": "poi_hospital", "name": "医院", "node_type": "poi_type", "properties": {"ev_demand": 7.2, "stay_time": "1-4小时", "charge_type": "快充"}},
        {"node_id": "poi_school", "name": "学校", "node_type": "poi_type", "properties": {"ev_demand": 7.8, "stay_time": "8小时+", "charge_type": "慢充"}},
        {"node_id": "poi_residential", "name": "居住小区", "node_type": "poi_type", "properties": {"ev_demand": 7.0, "stay_time": "夜间", "charge_type": "慢充"}},
        {"node_id": "poi_subway", "name": "地铁站", "node_type": "poi_type", "properties": {"ev_demand": 9.0, "stay_time": "0.5-1小时", "charge_type": "快充"}},
        
        # 道路节点
        {"node_id": "road_expressway", "name": "城市快速路", "node_type": "road", "properties": {"daily_flow": "5-8万辆", "ev_ratio": "7-9%"}},
        {"node_id": "road_main", "name": "主干道", "node_type": "road", "properties": {"daily_flow": "3-6万辆", "ev_ratio": "6-8%"}},
        {"node_id": "road_secondary", "name": "次干道", "node_type": "road", "properties": {"daily_flow": "1-3万辆", "ev_ratio": "5-7%"}},
        
        # 行政区节点
        {"node_id": "dist_gulou", "name": "鼓楼区", "node_type": "district", "properties": {"priority": "高", "demand": "快充为主"}},
        {"node_id": "dist_taijiang", "name": "台江区", "node_type": "district", "properties": {"priority": "高", "demand": "快慢结合"}},
        {"node_id": "dist_cangshan", "name": "仓山区", "node_type": "district", "properties": {"priority": "中", "demand": "慢充为主"}},
        {"node_id": "dist_jinan", "name": "晋安区", "node_type": "district", "properties": {"priority": "中", "demand": "快充为主"}},
        {"node_id": "dist_gaoxin", "name": "高新区", "node_type": "district", "properties": {"priority": "中", "demand": "慢充为主"}},
        
        # 规范标准节点
        {"node_id": "std_location", "name": "选址规范", "node_type": "standard", "properties": {"source": "GB/T 51313-2018", "key_req": "服务半径1-3km"}},
        {"node_id": "std_power", "name": "配电规范", "node_type": "standard", "properties": {"source": "技术规范", "key_req": "距变电站<500m"}},
        {"node_id": "std_safety", "name": "安全规范", "node_type": "standard", "properties": {"source": "消防规范", "key_req": "距危险源>50m"}},
    ]
    
    nodes = {}
    for n in nodes_data:
        node = KnowledgeGraphNode.objects.create(
            node_id=n["node_id"],
            name=n["name"],
            node_type=n["node_type"],
            properties=n["properties"]
        )
        nodes[n["node_id"]] = node
    
    # 定义边（关系）
    edges_data = [
        # 因素 -> 评分维度关系
        ("factor_traffic", "road_expressway", "影响_高", 0.9),
        ("factor_traffic", "road_main", "影响_中", 0.7),
        ("factor_traffic", "road_secondary", "影响_低", 0.4),
        
        # POI类型 -> 充电需求关系
        ("poi_transit", "factor_traffic", "高度关联", 0.95),
        ("poi_shopping", "factor_poi", "强影响", 0.85),
        ("poi_office", "factor_poi", "强影响", 0.88),
        ("poi_subway", "factor_traffic", "强影响", 0.90),
        ("poi_residential", "factor_power", "关联", 0.60),
        ("poi_hospital", "factor_accessibility", "关联", 0.75),
        ("poi_school", "factor_poi", "中等影响", 0.70),
        
        # 行政区 -> POI类型关系
        ("dist_gulou", "poi_shopping", "集中分布", 0.90),
        ("dist_gulou", "poi_office", "集中分布", 0.85),
        ("dist_taijiang", "poi_shopping", "分布", 0.75),
        ("dist_cangshan", "poi_school", "集中分布", 0.80),
        ("dist_jinan", "poi_transit", "集中分布", 0.85),
        ("dist_gaoxin", "poi_office", "集中分布", 0.80),
        
        # 规范标准 -> 影响因素关系
        ("std_location", "factor_accessibility", "约束", 0.95),
        ("std_power", "factor_power", "约束", 0.95),
        ("std_safety", "factor_competition", "约束", 0.80),
        
        # 道路 -> 行政区关系
        ("road_expressway", "dist_gulou", "穿越", 0.70),
        ("road_expressway", "dist_cangshan", "穿越", 0.75),
        ("road_main", "dist_taijiang", "穿越", 0.80),
        ("road_main", "dist_jinan", "穿越", 0.75),
    ]
    
    for src_id, tgt_id, relation, weight in edges_data:
        if src_id in nodes and tgt_id in nodes:
            KnowledgeGraphEdge.objects.create(
                source=nodes[src_id],
                target=nodes[tgt_id],
                relation=relation,
                weight=weight
            )
    
    print(f"✅ 知识图谱构建完成：{len(nodes_data)} 个节点，{len(edges_data)} 条关系边")


if __name__ == '__main__':
    print("🚀 开始构建知识库和知识图谱...")
    build_chroma_knowledge_base()
    build_knowledge_graph()
    print("✅ 知识库构建完成！")
