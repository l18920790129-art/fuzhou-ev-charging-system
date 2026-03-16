"""
LangChain Agent 核心分析引擎
集成：RAG（ChromaDB）+ 知识图谱 + 长期记忆 + DeepSeek LLM
"""
import os
import math
import json
import logging
from typing import List, Dict, Any, Optional

from django.conf import settings
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
import chromadb

logger = logging.getLogger(__name__)


# ============================================================
# LLM 初始化（DeepSeek）
# ============================================================
def get_llm():
    return ChatOpenAI(
        model=settings.DEEPSEEK_MODEL,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
        temperature=0.3,
        max_tokens=4096,
    )


# ============================================================
# ChromaDB RAG 检索
# ============================================================
def get_chroma_client():
    import os
    # 优先使用knowledge_base/chroma_db（实际构建路径）
    kb_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'knowledge_base', 'chroma_db')
    if os.path.exists(kb_path):
        return chromadb.PersistentClient(path=kb_path)
    return chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)


def rag_retrieve(query: str, n_results: int = 5) -> List[Dict]:
    """从ChromaDB检索相关知识"""
    try:
        client = get_chroma_client()
        collection = client.get_collection("ev_charging_knowledge")
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
        )
        docs = []
        for i, doc in enumerate(results['documents'][0]):
            docs.append({
                "content": doc,
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if results.get('distances') else 0,
            })
        return docs
    except Exception as e:
        logger.error(f"RAG检索失败: {e}")
        return []


# ============================================================
# 地理计算工具
# ============================================================
def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """计算两点间的球面距离（公里）"""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


# ============================================================
# Agent Tools（工具函数）
# ============================================================
@tool
def query_nearby_pois(location_info: str) -> str:
    """
    查询指定坐标周边的POI数据，用于评估充电桩选址的需求潜力。
    输入格式：'纬度,经度,半径km' 例如 '26.0756,119.3034,1.0'
    """
    from maps.models import POIData
    try:
        parts = location_info.strip().split(',')
        lat, lng, radius = float(parts[0]), float(parts[1]), float(parts[2])
    except:
        return "参数格式错误，请使用'纬度,经度,半径km'格式"
    
    pois = POIData.objects.all()
    nearby = []
    for poi in pois:
        dist = haversine_distance(lat, lng, poi.latitude, poi.longitude)
        if dist <= radius:
            nearby.append({
                "name": poi.name,
                "category": poi.get_category_display(),
                "distance_km": round(dist, 3),
                "daily_flow": poi.daily_flow,
                "ev_demand_score": poi.ev_demand_score,
                "influence_weight": poi.influence_weight,
            })
    
    nearby.sort(key=lambda x: x['distance_km'])
    
    if not nearby:
        return f"在{radius}km范围内未找到POI数据"
    
    result = f"在({lat}, {lng})周边{radius}km范围内找到{len(nearby)}个POI：\n"
    for p in nearby[:15]:
        result += f"- {p['name']}（{p['category']}）：距离{p['distance_km']}km，日均人流{p['daily_flow']}人，充电需求评分{p['ev_demand_score']}\n"
    
    # 计算加权POI评分
    if nearby:
        total_weight = sum(p['influence_weight'] for p in nearby)
        avg_ev_score = sum(p['ev_demand_score'] * p['influence_weight'] for p in nearby) / max(total_weight, 1)
        result += f"\nPOI综合评分：{avg_ev_score:.2f}/10（基于{len(nearby)}个POI加权计算）"
    
    return result


@tool
def query_traffic_flow(location_info: str) -> str:
    """
    查询指定坐标周边的主干道交通流量数据，评估充电需求。
    输入格式：'纬度,经度,半径km' 例如 '26.0756,119.3034,1.5'
    """
    from maps.models import TrafficFlow
    try:
        parts = location_info.strip().split(',')
        lat, lng, radius = float(parts[0]), float(parts[1]), float(parts[2])
    except:
        return "参数格式错误"
    
    roads = TrafficFlow.objects.all()
    nearby_roads = []
    for road in roads:
        dist = haversine_distance(lat, lng, road.center_lat, road.center_lng)
        if dist <= radius:
            nearby_roads.append({
                "road_name": road.road_name,
                "road_level": road.get_road_level_display(),
                "distance_km": round(dist, 3),
                "daily_flow": road.daily_flow,
                "peak_flow": road.peak_flow,
                "ev_ratio": road.ev_ratio,
                "heat_weight": road.heat_weight,
                "daily_ev_flow": int(road.daily_flow * road.ev_ratio),
            })
    
    nearby_roads.sort(key=lambda x: x['distance_km'])
    
    if not nearby_roads:
        return f"在{radius}km范围内未找到主干道数据"
    
    result = f"在({lat}, {lng})周边{radius}km范围内找到{len(nearby_roads)}条道路：\n"
    for r in nearby_roads[:10]:
        result += (f"- {r['road_name']}（{r['road_level']}）：距离{r['distance_km']}km，"
                   f"日均流量{r['daily_flow']}辆，日均EV流量{r['daily_ev_flow']}辆\n")
    
    if nearby_roads:
        max_flow = max(r['daily_flow'] for r in nearby_roads)
        avg_ev_flow = sum(r['daily_ev_flow'] for r in nearby_roads) / len(nearby_roads)
        result += f"\n交通流量评估：最高日均流量{max_flow}辆，周边平均日均EV流量{avg_ev_flow:.0f}辆"
    
    return result


@tool
def check_exclusion_zones(location_info: str) -> str:
    """
    检查指定坐标是否位于禁止选址区域（水域、林地、保护区等）。
    输入格式：'纬度,经度' 例如 '26.0756,119.3034'
    """
    from maps.models import ExclusionZone
    try:
        parts = location_info.strip().split(',')
        lat, lng = float(parts[0]), float(parts[1])
    except:
        return "参数格式错误"
    
    zones = ExclusionZone.objects.all()
    conflicts = []
    for zone in zones:
        dist = haversine_distance(lat, lng, zone.center_lat, zone.center_lng)
        if dist <= zone.radius_km:
            conflicts.append({
                "name": zone.name,
                "type": zone.get_zone_type_display(),
                "distance_km": round(dist, 3),
                "radius_km": zone.radius_km,
            })
    
    if conflicts:
        result = f"⚠️ 警告：该位置位于以下禁止/限制区域内：\n"
        for c in conflicts:
            result += f"- {c['name']}（{c['type']}）：距中心{c['distance_km']}km，影响半径{c['radius_km']}km\n"
        result += "\n建议：该位置不适合建设充电桩，请重新选择位置。"
    else:
        result = "✅ 该位置未位于任何禁止选址区域，通过环境约束检查。"
    
    return result


@tool
def query_existing_charging_stations(location_info: str) -> str:
    """
    查询指定坐标周边已有充电站，进行竞争分析。
    输入格式：'纬度,经度,半径km' 例如 '26.0756,119.3034,2.0'
    """
    from maps.models import CandidateLocation
    try:
        parts = location_info.strip().split(',')
        lat, lng, radius = float(parts[0]), float(parts[1]), float(parts[2])
    except:
        return "参数格式错误"
    
    stations = CandidateLocation.objects.filter(status='existing')
    nearby = []
    for s in stations:
        dist = haversine_distance(lat, lng, s.latitude, s.longitude)
        if dist <= radius:
            nearby.append({
                "name": s.name,
                "distance_km": round(dist, 3),
                "score": s.total_score,
            })
    
    nearby.sort(key=lambda x: x['distance_km'])
    
    if not nearby:
        result = f"✅ 在{radius}km范围内无已有充电站，竞争压力低，选址优势明显。"
    else:
        result = f"在{radius}km范围内发现{len(nearby)}个已有充电站：\n"
        for s in nearby:
            result += f"- {s['name']}：距离{s['distance_km']}km\n"
        
        if len(nearby) <= 2:
            result += f"\n竞争评估：竞争压力适中，仍有市场空间。"
        else:
            result += f"\n竞争评估：竞争压力较大，建议评估市场饱和度。"
    
    return result


@tool
def retrieve_knowledge(query: str) -> str:
    """
    从知识库检索充电桩选址相关专业知识，包括规范标准、案例分析、政策文件等。
    输入：查询关键词，例如 '充电桩选址规范' 或 '交通枢纽充电需求'
    """
    docs = rag_retrieve(query, n_results=4)
    if not docs:
        return "未检索到相关知识"
    
    result = f"检索到{len(docs)}条相关知识：\n\n"
    for i, doc in enumerate(docs, 1):
        meta = doc['metadata']
        result += f"【知识{i}】来源：{meta.get('source', '未知')} | 类型：{meta.get('type', '未知')}\n"
        result += f"{doc['content'][:500]}...\n\n"
    
    return result


@tool
def query_knowledge_graph(entity_name: str) -> str:
    """
    查询知识图谱中与指定实体相关的关系网络，获取选址影响因素的关联分析。
    输入：实体名称，例如 '购物中心' 或 '交通流量' 或 '鼓楼区'
    """
    from analysis.models import KnowledgeGraphNode, KnowledgeGraphEdge
    
    nodes = KnowledgeGraphNode.objects.filter(name__icontains=entity_name)
    if not nodes.exists():
        return f"知识图谱中未找到与'{entity_name}'相关的节点"
    
    result = f"知识图谱查询结果（'{entity_name}'相关）：\n\n"
    for node in nodes[:3]:
        result += f"节点：{node.name}（{node.get_node_type_display()}）\n"
        result += f"属性：{json.dumps(node.properties, ensure_ascii=False)}\n"
        
        # 查询出边
        out_edges = KnowledgeGraphEdge.objects.filter(source=node).select_related('target')[:5]
        if out_edges:
            result += "关联关系（影响）：\n"
            for edge in out_edges:
                result += f"  → {edge.target.name}（{edge.relation}，权重{edge.weight}）\n"
        
        # 查询入边
        in_edges = KnowledgeGraphEdge.objects.filter(target=node).select_related('source')[:5]
        if in_edges:
            result += "被关联关系（被影响）：\n"
            for edge in in_edges:
                result += f"  ← {edge.source.name}（{edge.relation}，权重{edge.weight}）\n"
        result += "\n"
    
    return result


@tool
def calculate_location_score(location_info: str) -> str:
    """
    综合计算指定坐标的充电桩选址评分（0-10分）。
    输入格式：'纬度,经度' 例如 '26.0756,119.3034'
    """
    from maps.models import POIData, TrafficFlow, ExclusionZone, CandidateLocation
    
    try:
        parts = location_info.strip().split(',')
        lat, lng = float(parts[0]), float(parts[1])
    except:
        return "参数格式错误"
    
    # 1. 检查禁止区域（一票否决）
    zones = ExclusionZone.objects.all()
    for zone in zones:
        dist = haversine_distance(lat, lng, zone.center_lat, zone.center_lng)
        if dist <= zone.radius_km:
            return f"❌ 该位置位于禁止区域'{zone.name}'内，综合评分：0分（不可选）"
    
    # 2. POI评分（权重30%）
    pois = POIData.objects.all()
    nearby_pois = []
    for poi in pois:
        dist = haversine_distance(lat, lng, poi.latitude, poi.longitude)
        if dist <= 1.0:
            nearby_pois.append((poi, dist))
    
    if nearby_pois:
        total_weight = sum(p.influence_weight for p, _ in nearby_pois)
        poi_score = sum(p.ev_demand_score * p.influence_weight for p, _ in nearby_pois) / max(total_weight, 1)
        poi_score = min(10, poi_score)
    else:
        poi_score = 2.0
    
    # 3. 交通流量评分（权重25%）
    roads = TrafficFlow.objects.all()
    nearby_roads = [(r, haversine_distance(lat, lng, r.center_lat, r.center_lng)) for r in roads]
    nearby_roads = [(r, d) for r, d in nearby_roads if d <= 1.5]
    
    if nearby_roads:
        max_flow = max(r.daily_flow for r, _ in nearby_roads)
        if max_flow >= 60000:
            traffic_score = 9.5
        elif max_flow >= 45000:
            traffic_score = 8.5
        elif max_flow >= 30000:
            traffic_score = 7.5
        elif max_flow >= 15000:
            traffic_score = 6.0
        else:
            traffic_score = 4.0
    else:
        traffic_score = 2.0
    
    # 4. 可达性评分（权重20%）
    if nearby_roads:
        min_dist = min(d for _, d in nearby_roads)
        if min_dist <= 0.1:
            access_score = 9.5
        elif min_dist <= 0.3:
            access_score = 8.0
        elif min_dist <= 0.5:
            access_score = 6.5
        elif min_dist <= 1.0:
            access_score = 5.0
        else:
            access_score = 3.0
    else:
        access_score = 2.0
    
    # 5. 竞争评分（权重15%）
    existing = CandidateLocation.objects.filter(status='existing')
    nearby_existing = [(s, haversine_distance(lat, lng, s.latitude, s.longitude)) for s in existing]
    nearby_existing = [(s, d) for s, d in nearby_existing if d <= 2.0]
    
    if len(nearby_existing) == 0:
        competition_score = 9.0
    elif len(nearby_existing) == 1:
        competition_score = 7.5
    elif len(nearby_existing) == 2:
        competition_score = 6.0
    else:
        competition_score = 4.0
    
    # 6. 配电条件评分（权重10%，基于与商业区距离估算）
    power_score = 7.0  # 默认中等评分
    
    # 综合评分
    total_score = (
        poi_score * 0.30 +
        traffic_score * 0.25 +
        access_score * 0.20 +
        competition_score * 0.15 +
        power_score * 0.10
    )
    
    result = f"""综合选址评分：{total_score:.2f}/10

评分明细：
- POI密度评分：{poi_score:.2f}/10（权重30%，周边{len(nearby_pois)}个POI）
- 交通流量评分：{traffic_score:.2f}/10（权重25%，周边{len(nearby_roads)}条道路）
- 可达性评分：{access_score:.2f}/10（权重20%）
- 竞争分析评分：{competition_score:.2f}/10（权重15%，周边{len(nearby_existing)}个已有充电站）
- 配电条件评分：{power_score:.2f}/10（权重10%）

评级：{'优秀（强烈推荐）' if total_score >= 8.5 else '良好（推荐）' if total_score >= 7.0 else '一般（可考虑）' if total_score >= 5.5 else '较差（不推荐）'}"""
    
    return result


@tool
def recommend_alternative_locations(location_info: str) -> str:
    """
    基于指定坐标，推荐周边其他优质充电桩候选位置。
    输入格式：'纬度,经度' 例如 '26.0756,119.3034'
    """
    from maps.models import POIData, TrafficFlow
    
    try:
        parts = location_info.strip().split(',')
        lat, lng = float(parts[0]), float(parts[1])
    except:
        return "参数格式错误"
    
    # 基于高评分POI推荐周边位置
    high_score_pois = POIData.objects.filter(ev_demand_score__gte=8.0).order_by('-ev_demand_score')
    
    candidates = []
    for poi in high_score_pois:
        dist = haversine_distance(lat, lng, poi.latitude, poi.longitude)
        if 0.3 <= dist <= 5.0:  # 排除太近和太远的
            candidates.append({
                "name": f"{poi.name}周边",
                "lat": poi.latitude + 0.002,
                "lng": poi.longitude + 0.002,
                "reason": f"靠近{poi.name}（{poi.get_category_display()}），日均人流{poi.daily_flow}人，充电需求评分{poi.ev_demand_score}",
                "score": poi.ev_demand_score,
                "distance_km": round(dist, 2),
            })
    
    candidates.sort(key=lambda x: (-x['score'], x['distance_km']))
    
    result = f"基于POI和交通分析，推荐以下备选位置：\n\n"
    for i, c in enumerate(candidates[:5], 1):
        result += f"{i}. {c['name']}\n"
        result += f"   坐标：({c['lat']:.4f}, {c['lng']:.4f})\n"
        result += f"   推荐理由：{c['reason']}\n"
        result += f"   距当前选点：{c['distance_km']}km\n\n"
    
    return result


# ============================================================
# Agent 系统提示词
# ============================================================
SYSTEM_PROMPT = """你是一个专业的福州市充电桩选址智能分析助手，基于大量专业知识和实时数据为用户提供科学的充电桩选址建议。

你的核心能力：
1. **RAG知识检索**：从专业知识库检索充电桩选址规范、政策文件、成功案例
2. **知识图谱推理**：利用知识图谱分析POI类型、道路等级、行政区特征之间的关联关系
3. **实时数据分析**：查询福州市真实POI数据、主干道交通流量、禁止区域信息
4. **综合评分**：按照行业标准对候选位置进行多维度量化评分
5. **长期记忆**：记住用户的历史选址偏好和分析结果

⚠️ 重要规则：
- 对于一般咨询问题（如区域分析、规范查询），最多调用3-4个工具，然后立即生成最终回复
- 对于具体坐标的选址分析，按以下流程执行后立即生成最终回复：
  1. 检查禁止区域
  2. 查询周边POI
  3. 查询交通流量
  4. 检索知识库
  5. 综合计算评分
  6. 推荐备选位置
- 收集到足够信息后，必须立即停止工具调用，生成完整的分析报告
- 不要重复查询相同类型的数据

输出格式要求：
- 使用Markdown格式，结构清晰
- 分析依据要列出数据来源（POI数据、流量数据、规范文件等）
- 评分要有详细的分项说明
- 推荐理由要结合实际数据，不能空泛
- 使用中文回答，专业且易懂

当前分析城市：福州市（福建省省会）
坐标系：WGS84（高德地图坐标系）"""


# ============================================================
# 主 Agent 类
# ============================================================
class EVChargingAgent:
    """充电桩选址LangChain Agent"""
    
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.llm = get_llm()
        self.tools = [
            query_nearby_pois,
            query_traffic_flow,
            check_exclusion_zones,
            query_existing_charging_stations,
            retrieve_knowledge,
            query_knowledge_graph,
            calculate_location_score,
            recommend_alternative_locations,
        ]
        self._setup_agent()
    
    def _setup_agent(self):
        """初始化Agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=15,
            max_execution_time=120,
            return_intermediate_steps=True,
            handle_parsing_errors=True,
        )
    
    def _load_memory(self) -> List:
        """从数据库加载历史对话记忆"""
        from memory.models import MemorySession, ConversationMemory
        try:
            session = MemorySession.objects.get(session_id=self.session_id)
            messages = ConversationMemory.objects.filter(session=session).order_by('created_at')
            
            history = []
            for msg in messages[-20:]:  # 最近20条
                if msg.role == 'user':
                    history.append(HumanMessage(content=msg.content))
                elif msg.role == 'assistant':
                    history.append(AIMessage(content=msg.content))
            return history
        except:
            return []
    
    def _save_memory(self, user_input: str, assistant_output: str):
        """保存对话到长期记忆"""
        from memory.models import MemorySession, ConversationMemory
        try:
            session, _ = MemorySession.objects.get_or_create(session_id=self.session_id)
            ConversationMemory.objects.create(session=session, role='user', content=user_input)
            ConversationMemory.objects.create(session=session, role='assistant', content=assistant_output)
        except Exception as e:
            logger.error(f"保存记忆失败: {e}")
    
    def analyze(self, user_input: str, lat: float = None, lng: float = None) -> Dict[str, Any]:
        """执行选址分析"""
        # 构建分析请求
        if lat and lng:
            full_input = f"请分析坐标({lat}, {lng})的充电桩选址可行性，并给出详细的分析报告。\n用户补充说明：{user_input}"
        else:
            full_input = user_input
        
        # 加载历史记忆
        chat_history = self._load_memory()
        
        try:
            result = self.agent_executor.invoke({
                "input": full_input,
                "chat_history": chat_history,
            })
            
            output = result.get("output", "")
            intermediate_steps = result.get("intermediate_steps", [])
            
            # 提取工具调用记录
            tool_calls = []
            for action, observation in intermediate_steps:
                tool_calls.append({
                    "tool": action.tool,
                    "input": action.tool_input,
                    "output": str(observation)[:500],
                })
            
            # 保存到长期记忆
            self._save_memory(full_input, output)
            
            return {
                "success": True,
                "output": output,
                "tool_calls": tool_calls,
                "rag_docs": rag_retrieve(full_input, n_results=3),
            }
        
        except Exception as e:
            logger.error(f"Agent分析失败: {e}")
            return {
                "success": False,
                "output": f"分析过程中出现错误：{str(e)}",
                "tool_calls": [],
                "rag_docs": [],
            }
    
    def chat(self, message: str) -> Dict[str, Any]:
        """普通对话（不需要坐标）"""
        return self.analyze(message)


# ============================================================
# 快速评分函数（不使用Agent，直接计算）
# ============================================================
def quick_score_location(lat: float, lng: float) -> Dict[str, Any]:
    """快速计算选址评分（用于地图实时反馈）"""
    from maps.models import POIData, TrafficFlow, ExclusionZone, CandidateLocation
    
    # 禁止区域检查
    zones = ExclusionZone.objects.all()
    for zone in zones:
        dist = haversine_distance(lat, lng, zone.center_lat, zone.center_lng)
        if dist <= zone.radius_km:
            return {
                "total_score": 0,
                "poi_score": 0,
                "traffic_score": 0,
                "accessibility_score": 0,
                "competition_score": 0,
                "exclusion_check": False,
                "exclusion_reason": f"位于{zone.name}（{zone.get_zone_type_display()}）内",
                "nearby_pois": [],
                "nearby_roads": [],
            }
    
    # POI评分
    pois = POIData.objects.all()
    nearby_pois = []
    for poi in pois:
        dist = haversine_distance(lat, lng, poi.latitude, poi.longitude)
        if dist <= 1.0:
            nearby_pois.append({
                "name": poi.name,
                "category": poi.get_category_display(),
                "distance_km": round(dist, 3),
                "ev_demand_score": poi.ev_demand_score,
                "daily_flow": poi.daily_flow,
            })
    
    nearby_pois.sort(key=lambda x: x['distance_km'])
    
    if nearby_pois:
        poi_scores = [p['ev_demand_score'] for p in nearby_pois]
        poi_score = min(10, sum(poi_scores[:5]) / min(len(poi_scores), 5))
    else:
        poi_score = 2.0
    
    # 交通流量评分
    roads = TrafficFlow.objects.all()
    nearby_roads = []
    for road in roads:
        dist = haversine_distance(lat, lng, road.center_lat, road.center_lng)
        if dist <= 1.5:
            nearby_roads.append({
                "road_name": road.road_name,
                "road_level": road.get_road_level_display(),
                "distance_km": round(dist, 3),
                "daily_flow": road.daily_flow,
                "heat_weight": road.heat_weight,
            })
    
    nearby_roads.sort(key=lambda x: x['distance_km'])
    
    if nearby_roads:
        max_flow = max(r['daily_flow'] for r in nearby_roads)
        traffic_score = min(10, max_flow / 10000)
    else:
        traffic_score = 2.0
    
    # 可达性评分
    if nearby_roads:
        min_dist = min(r['distance_km'] for r in nearby_roads)
        access_score = max(2, 10 - min_dist * 5)
    else:
        access_score = 2.0
    
    # 竞争评分
    existing = CandidateLocation.objects.filter(status='existing')
    nearby_count = sum(1 for s in existing if haversine_distance(lat, lng, s.latitude, s.longitude) <= 2.0)
    competition_score = max(3, 9 - nearby_count * 1.5)
    
    total_score = (
        poi_score * 0.30 +
        traffic_score * 0.25 +
        access_score * 0.20 +
        competition_score * 0.15 +
        7.0 * 0.10  # 配电条件默认
    )
    
    return {
        "total_score": round(total_score, 2),
        "poi_score": round(poi_score, 2),
        "traffic_score": round(traffic_score, 2),
        "accessibility_score": round(access_score, 2),
        "competition_score": round(competition_score, 2),
        "exclusion_check": True,
        "nearby_pois": nearby_pois[:8],
        "nearby_roads": nearby_roads[:5],
    }
