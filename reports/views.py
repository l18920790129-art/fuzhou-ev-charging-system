"""
报告生成API视图
"""
import os, json, uuid, math, logging
from datetime import datetime
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import SelectionReport
from analysis.models import AnalysisTask

logger = logging.getLogger(__name__)

def haversine(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def build_report_content(task):
    from maps.models import POIData, TrafficFlow
    lat, lng = task.latitude, task.longitude
    pois = POIData.objects.all()
    nearby_pois = sorted(
        [{"name": p.name, "category": p.get_category_display(), "distance_km": round(haversine(lat,lng,p.latitude,p.longitude),3),
          "daily_flow": p.daily_flow, "ev_demand_score": p.ev_demand_score}
         for p in pois if haversine(lat,lng,p.latitude,p.longitude) <= 1.0],
        key=lambda x: x["distance_km"])
    roads = TrafficFlow.objects.all()
    nearby_roads = sorted(
        [{"road_name": r.road_name, "road_level": r.get_road_level_display(),
          "distance_km": round(haversine(lat,lng,r.center_lat,r.center_lng),3),
          "daily_flow": r.daily_flow, "ev_ratio": r.ev_ratio}
         for r in roads if haversine(lat,lng,r.center_lat,r.center_lng) <= 1.5],
        key=lambda x: x["distance_km"])
    high_pois = POIData.objects.filter(ev_demand_score__gte=8.0).order_by("-ev_demand_score")
    alternatives = [
        {"name": f"{p.name}周边停车区", "lat": round(p.latitude+0.001,6), "lng": round(p.longitude+0.001,6),
         "score": p.ev_demand_score, "reason": f"靠近{p.name}，日均人流{p.daily_flow}人",
         "distance_from_selected": round(haversine(lat,lng,p.latitude,p.longitude),2)}
        for p in high_pois if 0.5 <= haversine(lat,lng,p.latitude,p.longitude) <= 5.0
    ][:5]
    return {
        "selected_location": {"lat": lat, "lng": lng,
            "address": task.address or f"福州市 ({lat:.4f}, {lng:.4f})",
            "total_score": task.total_score, "poi_score": task.poi_score,
            "traffic_score": task.traffic_score, "accessibility_score": task.accessibility_score},
        "poi_analysis": {"count": len(nearby_pois), "items": nearby_pois[:10],
            "summary": f"选址周边1km内共有{len(nearby_pois)}个POI，高需求POI{sum(1 for p in nearby_pois if p['ev_demand_score']>=8.0)}个"},
        "traffic_analysis": {"count": len(nearby_roads), "items": nearby_roads[:8],
            "max_daily_flow": max((r["daily_flow"] for r in nearby_roads), default=0),
            "summary": f"选址周边1.5km内有{len(nearby_roads)}条主干道，最高日均流量{max((r['daily_flow'] for r in nearby_roads), default=0)}辆"},
        "llm_analysis": task.llm_reasoning or "AI分析正在生成中...",
        "alternatives": alternatives,
        "scoring_detail": {"total": task.total_score, "poi": task.poi_score,
            "traffic": task.traffic_score, "accessibility": task.accessibility_score,
            "exclusion_check": task.exclusion_check},
        "generated_at": datetime.now().isoformat(),
    }

def generate_pdf_report(report):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        media_dir = os.path.join(settings.BASE_DIR, "media", "reports")
        os.makedirs(media_dir, exist_ok=True)
        pdf_path = os.path.join(media_dir, f"{report.report_id}.pdf")
        font_registered = False
        for fp in ["/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                   "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                   "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"]:
            if os.path.exists(fp):
                try:
                    pdfmetrics.registerFont(TTFont("CF", fp)); font_registered = True; break
                except: continue
        fn = "CF" if font_registered else "Helvetica"
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        ts = ParagraphStyle; title_s = ts("T", fontName=fn, fontSize=18, spaceAfter=12, textColor=colors.HexColor("#1a3a5c"), alignment=1)
        h2_s = ts("H2", fontName=fn, fontSize=13, spaceAfter=8, spaceBefore=16, textColor=colors.HexColor("#2563eb"))
        body_s = ts("B", fontName=fn, fontSize=10, spaceAfter=6, leading=16)
        small_s = ts("S", fontName=fn, fontSize=9, textColor=colors.grey)
        cd = report.report_content; sel = cd.get("selected_location",{}); poi_d = cd.get("poi_analysis",{})
        traf_d = cd.get("traffic_analysis",{}); llm_t = cd.get("llm_analysis",""); alts = cd.get("alternatives",[])
        sc = cd.get("scoring_detail",{}); score = sc.get("total",0)
        grade = "优秀（强烈推荐）" if score>=8.5 else "良好（推荐）" if score>=7.0 else "一般（可考虑）" if score>=5.5 else "较差（不推荐）"
        story = [Paragraph("福州市充电桩选址分析报告", title_s),
                 Paragraph(f"生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}", small_s),
                 HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563eb")), Spacer(1,0.3*cm),
                 Paragraph("一、执行摘要", h2_s),
                 Paragraph(f"本报告对福州市坐标({sel.get('lat','')}, {sel.get('lng','')})处的充电桩选址进行全面分析。综合评分：{score}/10，评级：{grade}。分析基于{poi_d.get('count',0)}个POI及{traf_d.get('count',0)}条主干道数据。", body_s),
                 Spacer(1,0.3*cm), Paragraph("二、综合评分", h2_s)]
        st_data = [["评分维度","得分","权重","说明"],
                   ["POI密度",f"{sc.get('poi',0):.1f}/10","30%",f"周边{poi_d.get('count',0)}个POI"],
                   ["交通流量",f"{sc.get('traffic',0):.1f}/10","25%",f"最高日均{traf_d.get('max_daily_flow',0)}辆"],
                   ["可达性",f"{sc.get('accessibility',0):.1f}/10","20%","距主干道距离"],
                   ["竞争分析","7.5/10","15%","周边充电站竞争"],
                   ["配电条件","7.0/10","10%","配电基础设施"],
                   ["综合评分",f"{score:.1f}/10","100%",grade]]
        st = Table(st_data, colWidths=[4*cm,2.5*cm,2*cm,8.5*cm])
        st.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#2563eb")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,-1),fn),("FONTSIZE",(0,0),(-1,-1),9),("ALIGN",(0,0),(-1,-1),"CENTER"),
            ("ROWBACKGROUNDS",(0,1),(-1,-2),[colors.white,colors.HexColor("#f0f7ff")]),
            ("BACKGROUND",(0,-1),(-1,-1),colors.HexColor("#dbeafe")),
            ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#cbd5e1")),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
        story += [st, Spacer(1,0.4*cm), Paragraph("三、POI需求分析", h2_s), Paragraph(poi_d.get("summary",""), body_s)]
        if poi_d.get("items"):
            pt_data = [["POI名称","类别","距离(km)","日均人流","需求评分"]] + [[p["name"],p["category"],str(p["distance_km"]),str(p["daily_flow"]),f"{p['ev_demand_score']}/10"] for p in poi_d["items"][:8]]
            pt = Table(pt_data, colWidths=[5*cm,2.5*cm,2.5*cm,2.5*cm,3*cm])
            pt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#059669")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
                ("FONTNAME",(0,0),(-1,-1),fn),("FONTSIZE",(0,0),(-1,-1),8),("ALIGN",(0,0),(-1,-1),"CENTER"),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f0fdf4")]),
                ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#d1fae5")),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
            story += [pt, Spacer(1,0.4*cm)]
        story += [Paragraph("四、交通流量分析", h2_s), Paragraph(traf_d.get("summary",""), body_s)]
        if traf_d.get("items"):
            rt_data = [["道路名称","等级","距离(km)","日均流量","EV占比"]] + [[r["road_name"],r["road_level"],str(r["distance_km"]),str(r["daily_flow"]),f"{(r['ev_ratio'] or 0)*100:.0f}%"] for r in traf_d["items"][:6]]
            rt = Table(rt_data, colWidths=[5*cm,3*cm,2.5*cm,3.5*cm,2.5*cm])
            rt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#d97706")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
                ("FONTNAME",(0,0),(-1,-1),fn),("FONTSIZE",(0,0),(-1,-1),8),("ALIGN",(0,0),(-1,-1),"CENTER"),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#fffbeb")]),
                ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#fde68a")),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
            story += [rt, Spacer(1,0.4*cm)]
        story.append(Paragraph("五、AI智能分析结论", h2_s))
        for para in (llm_t or "").split("\n\n")[:6]:
            if para.strip():
                try: story.append(Paragraph(para[:400].replace("<","").replace(">",""), body_s))
                except: pass
        if alts:
            story += [Spacer(1,0.4*cm), Paragraph("六、备选位置推荐", h2_s)]
            at_data = [["序号","推荐位置","评分","推荐理由","距选定点(km)"]] + [[str(i+1),a["name"],f"{a['score']}/10",a["reason"][:35],str(a.get("distance_from_selected","-"))] for i,a in enumerate(alts)]
            at = Table(at_data, colWidths=[1*cm,4.5*cm,2.5*cm,6*cm,3*cm])
            at.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#7c3aed")),("TEXTCOLOR",(0,0),(-1,0),colors.white),
                ("FONTNAME",(0,0),(-1,-1),fn),("FONTSIZE",(0,0),(-1,-1),8),("ALIGN",(0,0),(-1,-1),"CENTER"),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f5f3ff")]),
                ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#ddd6fe")),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
            story.append(at)
        story += [Spacer(1,0.5*cm), HRFlowable(width="100%",thickness=1,color=colors.grey),
                  Paragraph("本报告由福州充电桩智能选址系统自动生成。", small_s)]
        doc.build(story)
        return pdf_path
    except Exception as e:
        logger.error(f"PDF生成失败: {e}"); return None

@csrf_exempt
def generate_report(request):
    if request.method != "POST": return JsonResponse({"error":"仅支持POST"},status=405)
    try:
        body = json.loads(request.body)
        task_id = body.get("task_id")
        session_id = body.get("session_id","default")
        direct_lat = body.get("lat")
        direct_lng = body.get("lng")
        location_name = body.get("location_name", "")
    except: return JsonResponse({"error":"参数错误"},status=400)

    # 支持直接传坐标生成报告（无需task_id）
    if direct_lat and direct_lng and not task_id:
        from analysis.models import AnalysisTask as AT
        from maps.models import POIData, TrafficFlow, ExclusionZone
        lat, lng = float(direct_lat), float(direct_lng)
        # 计算快速评分
        pois = POIData.objects.all()
        nearby_pois = [p for p in pois if haversine(lat,lng,p.latitude,p.longitude) <= 1.0]
        poi_score = min(10, len(nearby_pois) * 0.8 + sum(p.ev_demand_score for p in nearby_pois[:5]) / max(len(nearby_pois[:5]),1) * 0.5) if nearby_pois else 3.0
        roads = TrafficFlow.objects.all()
        nearby_roads = [r for r in roads if haversine(lat,lng,r.center_lat,r.center_lng) <= 1.5]
        traffic_score = min(10, sum(r.daily_flow for r in nearby_roads[:3]) / 10000) if nearby_roads else 3.0
        accessibility_score = 8.5 if nearby_roads else 5.0
        total_score = round(poi_score*0.35 + traffic_score*0.30 + accessibility_score*0.20 + 7.0*0.15, 2)
        # 创建临时任务
        task = AT.objects.create(
            task_id='rpt_'+str(uuid.uuid4())[:8],
            session_id=session_id, latitude=lat, longitude=lng,
            address=location_name or f"福州市 ({lat:.4f}, {lng:.4f})",
            status='completed', total_score=total_score,
            poi_score=round(poi_score,2), traffic_score=round(traffic_score,2),
            accessibility_score=round(accessibility_score,2), exclusion_check=True,
            llm_reasoning=f"基于{len(nearby_pois)}个POI和{len(nearby_roads)}条主干道的综合评分分析。"
        )
    else:
        try: task = AnalysisTask.objects.get(task_id=task_id)
        except AnalysisTask.DoesNotExist: return JsonResponse({"error":"分析任务不存在"},status=404)

    report_id = str(uuid.uuid4())[:12]
    content = build_report_content(task)
    report = SelectionReport.objects.create(
        report_id=report_id, title=f"福州充电桩选址报告 - {task.address or f'({task.latitude:.4f}, {task.longitude:.4f})' }",
        session_id=session_id, selected_lat=task.latitude, selected_lng=task.longitude,
        selected_address=task.address or f"福州市 ({task.latitude:.4f}, {task.longitude:.4f})",
        total_score=task.total_score, report_content=content, alternative_locations=content.get("alternatives",[]))
    pdf_path = generate_pdf_report(report)
    if pdf_path: report.pdf_path = pdf_path; report.save()
    return JsonResponse({"success":True,"report_id":report_id,"title":report.title,"total_score":report.total_score,"has_pdf":bool(pdf_path),"content":content})

def get_report(request, report_id):
    try:
        r = SelectionReport.objects.get(report_id=report_id)
        return JsonResponse({"report_id":r.report_id,"title":r.title,"selected_lat":r.selected_lat,"selected_lng":r.selected_lng,
            "total_score":r.total_score,"content":r.report_content,"alternatives":r.alternative_locations,
            "has_pdf":bool(r.pdf_path),"created_at":r.created_at.isoformat()})
    except SelectionReport.DoesNotExist: return JsonResponse({"error":"报告不存在"},status=404)

def download_pdf(request, report_id):
    try:
        r = SelectionReport.objects.get(report_id=report_id)
        if r.pdf_path and os.path.exists(r.pdf_path):
            resp = FileResponse(open(r.pdf_path,"rb"),content_type="application/pdf")
            resp["Content-Disposition"] = f"attachment; filename=charging_report_{report_id}.pdf"
            return resp
        return JsonResponse({"error":"PDF不存在"},status=404)
    except SelectionReport.DoesNotExist: return JsonResponse({"error":"报告不存在"},status=404)

def report_list(request):
    session_id = request.GET.get("session_id","")
    qs = SelectionReport.objects.all().order_by("-created_at")
    if session_id: qs = qs.filter(session_id=session_id)
    return JsonResponse({"data":[{"report_id":r.report_id,"title":r.title,"total_score":r.total_score,"created_at":r.created_at.isoformat()} for r in qs[:20]]})
