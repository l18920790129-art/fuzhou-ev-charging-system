"""
报告数据模型
"""
from django.db import models


class SelectionReport(models.Model):
    """充电桩选址报告"""
    report_id = models.CharField(max_length=100, unique=True, verbose_name='报告ID')
    title = models.CharField(max_length=300, verbose_name='报告标题')
    session_id = models.CharField(max_length=100, blank=True, verbose_name='会话ID')
    # 选定位置
    selected_lat = models.FloatField(verbose_name='选定纬度')
    selected_lng = models.FloatField(verbose_name='选定经度')
    selected_address = models.CharField(max_length=500, blank=True, verbose_name='选定地址')
    # 评分
    total_score = models.FloatField(default=0.0, verbose_name='综合评分')
    # 报告内容JSON
    report_content = models.JSONField(default=dict, verbose_name='报告内容')
    # 推荐的其他位置
    alternative_locations = models.JSONField(default=list, verbose_name='备选位置')
    # PDF文件路径
    pdf_path = models.CharField(max_length=500, blank=True, verbose_name='PDF路径')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '选址报告'
        verbose_name_plural = '选址报告'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.created_at.strftime('%Y-%m-%d')})"
