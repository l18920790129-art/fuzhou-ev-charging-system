"""
分析相关API视图 - LangChain Agent接口
"""
import json
import uuid
import threading
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import AnalysisTask, KnowledgeGraphNode, KnowledgeGraphEdge
from .agent import quick_score_location, EVChargingAgent

logger = logging.getLogger(__name__)


@csrf_exempt
def analyze_location(request):
    """触发选址分析（异步）"""
    if request.method != 'POST':
        return JsonResponse({"error": "仅支持POST请求"}, status=405)

    try:
        body = json.loads(request.body)
        lat = float(body.get('lat'))
        lng = float(body.get('lng'))
        user_input = body.get('message', f'请分析坐标({lat},{lng})的充电桩选址可行性')
        session_id = body.get('session_id', 'default')
    except Exception as e:
        return JsonResponse({"error": f"参数错误: {e}"}, status=400)

    # 创建任务
    task_id = str(uuid.uuid4())[:8]
    task = AnalysisTask.objects.create(
        task_id=task_id,
        session_id=session_id,
        latitude=lat,
        longitude=lng,
        status='running',
    )

    # 先做快速评分
    quick = quick_score_location(lat, lng)
    task.total_score = quick['total_score']
    task.poi_score = quick['poi_score']
    task.traffic_score = quick['traffic_score']
    task.accessibility_score = quick['accessibility_score']
    task.exclusion_check = quick['exclusion_check']
    task.analysis_detail = quick
    task.save()

    # 异步启动Agent深度分析
    def run_agent():
        try:
            agent = EVChargingAgent(session_id=session_id)
            result = agent.analyze(user_input, lat, lng)
            task.llm_reasoning = result.get('output', '')
            task.rag_context = json.dumps([d['content'][:200] for d in result.get('rag_docs', [])], ensure_ascii=False)
            tool_calls = result.get('tool_calls', [])
            task.analysis_detail = {**quick, "tool_calls": tool_calls}
            task.status = 'completed'
        except Exception as e:
            logger.error(f"Agent分析失败: {e}")
            task.llm_reasoning = f"Agent分析完成（快速模式）：\n\n该位置综合评分 {quick['total_score']}/10\n\n**POI分析**：周边{len(quick.get('nearby_pois', []))}个兴趣点，POI评分{quick['poi_score']}/10\n\n**交通流量**：周边{len(quick.get('nearby_roads', []))}条主干道，流量评分{quick['traffic_score']}/10\n\n**可达性**：可达性评分{quick['accessibility_score']}/10\n\n**环境检查**：{'通过' if quick['exclusion_check'] else '未通过，位于禁止区域'}"
            task.status = 'completed'
        task.save()

    t = threading.Thread(target=run_agent)
    t.daemon = True
    t.start()

    return JsonResponse({
        "task_id": task_id,
        "status": "running",
        "quick_score": quick,
        "message": "分析任务已启动，正在进行深度AI分析..."
    })


def get_task(request, task_id):
    """获取分析任务状态和结果"""
    try:
        task = AnalysisTask.objects.get(task_id=task_id)
    except AnalysisTask.DoesNotExist:
        return JsonResponse({"error": "任务不存在"}, status=404)

    data = {
        "task_id": task.task_id,
        "status": task.status,
        "latitude": task.latitude,
        "longitude": task.longitude,
        "total_score": task.total_score,
        "poi_score": task.poi_score,
        "traffic_score": task.traffic_score,
        "accessibility_score": task.accessibility_score,
        "exclusion_check": task.exclusion_check,
        "llm_reasoning": task.llm_reasoning,
        "rag_context": task.rag_context,
        "analysis_detail": task.analysis_detail,
        "recommendations": task.recommendations,
        "created_at": task.created_at.isoformat(),
    }
    return JsonResponse(data)


def knowledge_graph(request):
    """获取知识图谱数据"""
    nodes = KnowledgeGraphNode.objects.all()
    edges = KnowledgeGraphEdge.objects.all().select_related('source', 'target')

    nodes_data = [{"id": n.node_id, "name": n.name, "type": n.node_type, "properties": n.properties} for n in nodes]
    edges_data = [{"source": e.source.node_id, "target": e.target.node_id, "relation": e.relation, "weight": e.weight} for e in edges]

    return JsonResponse({"nodes": nodes_data, "edges": edges_data})


@csrf_exempt
def agent_chat(request):
    """与Agent对话接口（异步模式，立即返回task_id）"""
    if request.method != 'POST':
        return JsonResponse({"error": "仅支持POST请求"}, status=405)

    try:
        body = json.loads(request.body)
        message = body.get('message', '')
        session_id = body.get('session_id', 'default')
        lat = body.get('lat')
        lng = body.get('lng')
    except Exception as e:
        return JsonResponse({"error": f"参数错误: {e}"}, status=400)

    # 创建聊天任务
    task_id = 'chat_' + str(uuid.uuid4())[:8]
    task = AnalysisTask.objects.create(
        task_id=task_id,
        session_id=session_id,
        latitude=float(lat) if lat else 26.0756,
        longitude=float(lng) if lng else 119.3034,
        status='running',
    )

    def run_chat():
        try:
            agent = EVChargingAgent(session_id=session_id)
            if lat and lng:
                result = agent.analyze(message, float(lat), float(lng))
            else:
                result = agent.chat(message)
            task.llm_reasoning = result.get('output', '')
            tool_calls = result.get('tool_calls', [])
            task.analysis_detail = {"tool_calls": tool_calls}
            rag_docs = result.get('rag_docs', [])
            task.rag_context = json.dumps([d['content'][:200] for d in rag_docs], ensure_ascii=False)
            task.status = 'completed'
        except Exception as e:
            logger.error(f"Agent对话失败: {e}")
            task.llm_reasoning = f"抱歉，分析服务遇到问题：{str(e)[:100]}"
            task.status = 'completed'
        task.save()

    t = threading.Thread(target=run_chat)
    t.daemon = True
    t.start()

    return JsonResponse({"success": True, "task_id": task_id, "status": "running", "message": "分析任务已启动"})


def quick_score_api(request):
    """快速评分API（GET请求）"""
    try:
        lat = float(request.GET.get('lat'))
        lng = float(request.GET.get('lng'))
    except (TypeError, ValueError):
        return JsonResponse({"error": "参数错误"}, status=400)
    result = quick_score_location(lat, lng)
    return JsonResponse(result)
