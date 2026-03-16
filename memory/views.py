"""
长期记忆系统API视图
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import MemorySession, ConversationMemory, LocationMemory


@csrf_exempt
def get_or_create_session(request):
    """获取或创建会话"""
    if request.method == 'POST':
        body = json.loads(request.body)
        session_id = body.get('session_id', '')
        user_name = body.get('user_name', '用户')
    else:
        session_id = request.GET.get('session_id', '')
        user_name = request.GET.get('user_name', '用户')

    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())[:12]

    session, created = MemorySession.objects.get_or_create(
        session_id=session_id,
        defaults={'user_name': user_name}
    )

    return JsonResponse({
        "session_id": session.session_id,
        "user_name": session.user_name,
        "created": created,
        "created_at": session.created_at.isoformat(),
        "message_count": session.messages.count(),
        "location_count": session.locations.count(),
    })


def get_history(request):
    """获取会话历史"""
    session_id = request.GET.get('session_id', 'default')
    try:
        session = MemorySession.objects.get(session_id=session_id)
        messages = ConversationMemory.objects.filter(session=session).order_by('-created_at')[:20]
        locations = LocationMemory.objects.filter(session=session).order_by('-created_at')[:10]

        return JsonResponse({
            "session_id": session_id,
            "messages": [{"role": m.role, "content": m.content[:200], "created_at": m.created_at.isoformat()} for m in reversed(list(messages))],
            "locations": [{"lat": l.latitude, "lng": l.longitude, "score": l.score, "address": l.address, "created_at": l.created_at.isoformat()} for l in locations],
        })
    except MemorySession.DoesNotExist:
        return JsonResponse({"session_id": session_id, "messages": [], "locations": []})


@csrf_exempt
def clear_memory(request):
    """清除会话记忆"""
    if request.method == 'POST':
        body = json.loads(request.body)
        session_id = body.get('session_id', 'default')
        try:
            session = MemorySession.objects.get(session_id=session_id)
            session.messages.all().delete()
            session.locations.all().delete()
            return JsonResponse({"success": True, "message": "记忆已清除"})
        except MemorySession.DoesNotExist:
            return JsonResponse({"success": False, "message": "会话不存在"})
    return JsonResponse({"error": "仅支持POST"}, status=405)
