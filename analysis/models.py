"""
分析结果数据模型
"""
from django.db import models


class AnalysisTask(models.Model):
    """选址分析任务"""
    STATUS_CHOICES = [
        ('pending', '待处理'), ('running', '分析中'),
        ('completed', '已完成'), ('failed', '失败'),
    ]
    task_id = models.CharField(max_length=100, unique=True, verbose_name='任务ID')
    session_id = models.CharField(max_length=100, blank=True, verbose_name='会话ID')
    latitude = models.FloatField(verbose_name='目标纬度')
    longitude = models.FloatField(verbose_name='目标经度')
    address = models.CharField(max_length=500, blank=True, verbose_name='地址')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    # 评分结果
    total_score = models.FloatField(default=0.0, verbose_name='综合评分')
    poi_score = models.FloatField(default=0.0, verbose_name='POI评分')
    traffic_score = models.FloatField(default=0.0, verbose_name='流量评分')
    accessibility_score = models.FloatField(default=0.0, verbose_name='可达性评分')
    exclusion_check = models.BooleanField(default=True, verbose_name='排除区域检查通过')
    # 分析详情
    analysis_detail = models.JSONField(default=dict, blank=True, verbose_name='分析详情')
    llm_reasoning = models.TextField(blank=True, verbose_name='LLM推理过程')
    rag_context = models.TextField(blank=True, verbose_name='RAG检索上下文')
    kg_entities = models.JSONField(default=list, blank=True, verbose_name='知识图谱实体')
    recommendations = models.JSONField(default=list, blank=True, verbose_name='推荐位置')
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '分析任务'
        verbose_name_plural = '分析任务'
        ordering = ['-created_at']

    def __str__(self):
        return f"任务 {self.task_id} ({self.status})"


class KnowledgeGraphNode(models.Model):
    """知识图谱节点"""
    NODE_TYPES = [
        ('location', '地点'), ('poi_type', 'POI类型'),
        ('road', '道路'), ('district', '行政区'),
        ('factor', '影响因素'), ('standard', '规范标准'),
    ]
    node_id = models.CharField(max_length=100, unique=True, verbose_name='节点ID')
    name = models.CharField(max_length=200, verbose_name='节点名称')
    node_type = models.CharField(max_length=50, choices=NODE_TYPES, verbose_name='节点类型')
    properties = models.JSONField(default=dict, blank=True, verbose_name='属性')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '知识图谱节点'
        verbose_name_plural = '知识图谱节点'

    def __str__(self):
        return f"{self.name} ({self.node_type})"


class KnowledgeGraphEdge(models.Model):
    """知识图谱边（关系）"""
    source = models.ForeignKey(KnowledgeGraphNode, on_delete=models.CASCADE, related_name='outgoing_edges')
    target = models.ForeignKey(KnowledgeGraphNode, on_delete=models.CASCADE, related_name='incoming_edges')
    relation = models.CharField(max_length=100, verbose_name='关系类型')
    weight = models.FloatField(default=1.0, verbose_name='权重')
    properties = models.JSONField(default=dict, blank=True, verbose_name='属性')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '知识图谱边'
        verbose_name_plural = '知识图谱边'

    def __str__(self):
        return f"{self.source.name} --[{self.relation}]--> {self.target.name}"
