"""
长期记忆系统数据模型
"""
from django.db import models


class MemorySession(models.Model):
    """用户会话记忆"""
    session_id = models.CharField(max_length=100, unique=True, verbose_name='会话ID')
    user_name = models.CharField(max_length=100, blank=True, verbose_name='用户名')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    context_summary = models.TextField(blank=True, verbose_name='上下文摘要')

    class Meta:
        verbose_name = '记忆会话'
        verbose_name_plural = '记忆会话'

    def __str__(self):
        return f"会话 {self.session_id}"


class ConversationMemory(models.Model):
    """对话记忆条目"""
    ROLE_CHOICES = [('user', '用户'), ('assistant', '助手'), ('system', '系统')]
    session = models.ForeignKey(MemorySession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name='角色')
    content = models.TextField(verbose_name='内容')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='元数据')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '对话记忆'
        verbose_name_plural = '对话记忆'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class LocationMemory(models.Model):
    """选址记忆 - 记录用户历史选址行为"""
    session = models.ForeignKey(MemorySession, on_delete=models.CASCADE, related_name='locations')
    latitude = models.FloatField(verbose_name='纬度')
    longitude = models.FloatField(verbose_name='经度')
    address = models.CharField(max_length=500, blank=True, verbose_name='地址')
    analysis_result = models.JSONField(default=dict, blank=True, verbose_name='分析结果')
    score = models.FloatField(default=0.0, verbose_name='评分')
    user_feedback = models.CharField(max_length=20, blank=True, verbose_name='用户反馈')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '选址记忆'
        verbose_name_plural = '选址记忆'
        ordering = ['-created_at']

    def __str__(self):
        return f"({self.latitude:.4f}, {self.longitude:.4f}) - {self.score:.2f}"


class KnowledgeMemory(models.Model):
    """知识记忆 - 存储RAG检索到的重要知识片段"""
    session = models.ForeignKey(MemorySession, on_delete=models.CASCADE, related_name='knowledge', null=True, blank=True)
    content = models.TextField(verbose_name='知识内容')
    source = models.CharField(max_length=200, blank=True, verbose_name='来源')
    relevance_score = models.FloatField(default=0.0, verbose_name='相关性评分')
    tags = models.JSONField(default=list, blank=True, verbose_name='标签')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '知识记忆'
        verbose_name_plural = '知识记忆'

    def __str__(self):
        return f"{self.content[:80]}"
