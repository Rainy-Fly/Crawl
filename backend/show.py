import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import font_manager
import numpy as np
import io
import base64
import json
from typing import Dict, List, Any, Optional, Tuple
import os

# 尝试导入wordcloud，如果失败则设置为None
try:
    from wordcloud import WordCloud
    WORDCLOUD_AVAILABLE = True
except ImportError:
    WordCloud = None
    WORDCLOUD_AVAILABLE = False

# 设置中文字体
font_path = None
possible_fonts = [
    'C:/Windows/Fonts/simhei.ttf',  # Windows 黑体
    'C:/Windows/Fonts/msyh.ttc',    # Windows 微软雅黑
    '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',  # Linux
    '/System/Library/Fonts/PingFang.ttc',  # macOS
]

for fp in possible_fonts:
    if os.path.exists(fp):
        font_path = fp
        break

if font_path:
    font_manager.fontManager.addfont(font_path)
    plt.rcParams['font.family'] = font_manager.FontProperties(fname=font_path).get_name()
else:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']

plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


class DataVisualizer:
    """数据可视化类，使用matplotlib生成各种图表"""
    
    def __init__(self):
        self.fig_size = (12, 8)
        self.dpi = 100
    
    def generate_all_visualizations(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        生成所有可视化图表
        
        Args:
            data: AI分析后的数据
        
        Returns:
            包含所有图表base64编码的字典
        """
        results = {}
        
        # 生成词云
        if 'wordcloud_data' in data or 'keywords' in data:
            results['wordcloud'] = self.generate_wordcloud(data)
        
        # 生成情感分析饼图
        if 'sentiment_distribution' in data:
            results['sentiment_pie'] = self.generate_sentiment_pie(data['sentiment_distribution'])
        
        # 生成分类柱状图
        if 'categories' in data:
            results['category_bar'] = self.generate_category_bar(data['categories'])
        
        # 生成关键词条形图
        if 'keywords' in data:
            results['keyword_bar'] = self.generate_keyword_bar(data['keywords'])
        
        # 生成统计信息图
        if 'statistics' in data:
            results['stats_chart'] = self.generate_stats_chart(data['statistics'])
        
        # 生成趋势图（如果有时间数据）
        if 'timeline' in data:
            results['timeline'] = self.generate_timeline(data['timeline'])
        
        return results
    
    def generate_wordcloud(self, data: Dict[str, Any], width: int = 800, height: int = 400) -> str:
        """生成词云图"""
        
        # 检查wordcloud是否可用
        if not WORDCLOUD_AVAILABLE:
            print("警告: wordcloud库未安装，跳过词云生成。请使用 'pip install wordcloud' 安装")
            return None
        
        # 获取词云数据
        wordcloud_data = data.get('wordcloud_data', data.get('keywords', []))
        
        if not wordcloud_data:
            return None
        
        # 转换为词云需要的格式
        if isinstance(wordcloud_data, list) and len(wordcloud_data) > 0:
            if isinstance(wordcloud_data[0], dict):
                # 格式: [{"word": "xxx", "weight": 0.9, "count": 100}]
                word_freq = {item['word']: item.get('count', item.get('weight', 1) * 100) 
                            for item in wordcloud_data}
            else:
                word_freq = {str(item): 100 for item in wordcloud_data}
        else:
            word_freq = {"暂无数据": 100}
        
        # 创建词云
        wc = WordCloud(
            width=width,
            height=height,
            background_color='white',
            font_path=font_path if font_path else None,
            max_words=100,
            relative_scaling=0.5,
            colormap='viridis'
        ).generate_from_frequencies(word_freq)
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=self.dpi)
        ax.imshow(wc, interpolation='bilinear')
        ax.axis('off')
        ax.set_title('关键词词云', fontsize=16, fontweight='bold', pad=10)
        
        # 转换为base64
        return self._fig_to_base64(fig)
    
    def generate_sentiment_pie(self, sentiment_data: Dict[str, Any]) -> str:
        """生成情感分析饼图"""
        
        if isinstance(sentiment_data, dict):
            labels = list(sentiment_data.keys())
            sizes = list(sentiment_data.values())
        else:
            labels = ['正面', '中性', '负面']
            sizes = [40, 35, 25]
        
        colors = ['#28a745', '#ffc107', '#dc3545']
        explode = [0.05] * len(labels)
        
        fig, ax = plt.subplots(figsize=(10, 8), dpi=self.dpi)
        wedges, texts, autotexts = ax.pie(
            sizes, 
            explode=explode, 
            labels=labels, 
            colors=colors[:len(labels)],
            autopct='%1.1f%%',
            shadow=True,
            startangle=90,
            textprops={'fontsize': 12}
        )
        
        ax.set_title('情感分析分布', fontsize=16, fontweight='bold', pad=20)
        
        # 添加图例
        ax.legend(wedges, labels, title="情感类型", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def generate_category_bar(self, categories) -> str:
        """生成分类柱状图"""
        
        if not categories:
            return None
        
        # 处理数据，确保是字典格式
        processed_categories = {}
        
        if isinstance(categories, list):
            # 如果是列表，统计每个元素出现的次数
            for item in categories:
                if isinstance(item, str):
                    processed_categories[item] = processed_categories.get(item, 0) + 1
                elif isinstance(item, dict) and 'name' in item:
                    name = item['name']
                    processed_categories[name] = processed_categories.get(name, 0) + 1
        elif isinstance(categories, dict):
            # 如果是字典，处理每个键值对
            for key, value in categories.items():
                if isinstance(value, (int, float)):
                    processed_categories[key] = value
                elif isinstance(value, list):
                    processed_categories[key] = len(value)
                elif isinstance(value, dict):
                    processed_categories[key] = len(value)
                else:
                    processed_categories[key] = 1
        
        if not processed_categories:
            return None
        
        labels = list(processed_categories.keys())
        values = list(processed_categories.values())
        
        fig, ax = plt.subplots(figsize=(12, 6), dpi=self.dpi)
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        bars = ax.bar(labels, values, color=colors, edgecolor='black', linewidth=0.5)
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontsize=10)
        
        ax.set_xlabel('分类', fontsize=12, fontweight='bold')
        ax.set_ylabel('数量', fontsize=12, fontweight='bold')
        ax.set_title('数据分类统计', fontsize=16, fontweight='bold', pad=20)
        ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def generate_keyword_bar(self, keywords: List[Dict[str, Any]]) -> str:
        """生成关键词条形图"""
        
        if not keywords:
            return None
        
        # 取前15个关键词
        top_keywords = keywords[:15] if len(keywords) > 15 else keywords
        
        if isinstance(top_keywords[0], dict):
            words = [k['word'] for k in top_keywords]
            weights = [k.get('weight', k.get('count', 1)) for k in top_keywords]
        else:
            words = [str(k) for k in top_keywords]
            weights = [100 - i * 5 for i in range(len(words))]
        
        fig, ax = plt.subplots(figsize=(10, 8), dpi=self.dpi)
        
        colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(words)))
        bars = ax.barh(range(len(words)), weights, color=colors, edgecolor='black', linewidth=0.5)
        
        ax.set_yticks(range(len(words)))
        ax.set_yticklabels(words)
        ax.invert_yaxis()  # 最高的在顶部
        
        ax.set_xlabel('权重/频次', fontsize=12, fontweight='bold')
        ax.set_title('热门关键词TOP15', fontsize=16, fontweight='bold', pad=20)
        
        # 添加数值标签
        for i, (bar, weight) in enumerate(zip(bars, weights)):
            ax.text(weight, i, f' {weight:.1f}', va='center', fontsize=9)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def generate_stats_chart(self, statistics) -> str:
        """生成统计信息图表"""
        
        if not statistics:
            return None
        
        # 统一处理为字典格式
        if isinstance(statistics, list):
            # 如果是列表，尝试转换为字典
            stats_dict = {}
            for item in statistics:
                if isinstance(item, dict):
                    stats_dict.update(item)
                else:
                    stats_dict[str(item)] = 1
            statistics = stats_dict
        elif not isinstance(statistics, dict):
            return None
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=self.dpi)
        
        # 左图：数据质量饼图或分布图
        has_pie_data = False
        pie_labels = []
        pie_values = []
        pie_colors = []
        
        # 尝试找到可以做成饼图的数据
        for key, value in statistics.items():
            if isinstance(value, (int, float)) and value > 0:
                # 排除可能是ID或时间戳的大数字
                if value < 10000 or key in ['valid_count', 'invalid_count', 'duplicate_count', 'total_count']:
                    pie_labels.append(key)
                    pie_values.append(value)
                    has_pie_data = True
        
        if has_pie_data and len(pie_values) >= 2:
            # 使用预定义的颜色映射
            color_map = plt.cm.Set3(np.linspace(0, 1, len(pie_labels)))
            ax1.pie(pie_values, labels=pie_labels, colors=color_map,
                   autopct='%1.1f%%', startangle=90, textprops={'fontsize': 10})
            ax1.set_title('数据分布', fontsize=14, fontweight='bold')
        else:
            # 如果没有饼图数据，显示柱状图
            numeric_items = [(k, v) for k, v in statistics.items() 
                           if isinstance(v, (int, float)) and not isinstance(v, bool)]
            if numeric_items:
                labels, values = zip(*numeric_items[:8])  # 最多显示8个
                colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(labels)))
                bars = ax1.bar(range(len(labels)), values, color=colors)
                ax1.set_xticks(range(len(labels)))
                ax1.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
                ax1.set_title('关键指标', fontsize=14, fontweight='bold')
                # 添加数值标签
                for bar, val in zip(bars, values):
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height)}', ha='center', va='bottom', fontsize=9)
        
        # 右图：关键指标文本
        ax2.axis('off')
        stats_text = "数据统计概览\n" + "="*30 + "\n\n"
        
        # 将key转换为中文
        key_map = {
            'total_count': '总数据量',
            'valid_count': '有效数据',
            'invalid_count': '无效数据',
            'duplicate_count': '重复数据',
            'success_count': '成功数',
            'failed_count': '失败数',
            'total_books': '图书总数',
            'total_comments': '评论总数',
            'average_score': '平均评分',
            'max_score': '最高评分',
            'min_score': '最低评分',
            'publisher_count': '出版社数量',
            'author_count': '作者数量'
        }
        
        for key, value in list(statistics.items())[:15]:  # 最多显示15项
            cn_key = key_map.get(key, key)
            # 格式化显示
            if isinstance(value, float):
                stats_text += f"{cn_key}: {value:.2f}\n"
            elif isinstance(value, dict):
                stats_text += f"{cn_key}: {len(value)} 项\n"
            elif isinstance(value, list):
                stats_text += f"{cn_key}: {len(value)} 项\n"
            else:
                stats_text += f"{cn_key}: {value}\n"
        
        # 使用支持中文的字体
        ax2.text(0.05, 0.5, stats_text, fontsize=11,
                verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def generate_timeline(self, timeline_data: List[Dict[str, Any]]) -> str:
        """生成时间线图"""
        
        if not timeline_data:
            return None
        
        # 提取时间和事件
        times = []
        events = []
        values = []
        
        for item in timeline_data:
            if isinstance(item, dict):
                times.append(item.get('time', item.get('date', '')))
                events.append(item.get('event', item.get('title', '')))
                values.append(item.get('value', item.get('count', 1)))
            else:
                times.append(str(item))
                events.append('')
                values.append(1)
        
        fig, ax = plt.subplots(figsize=(14, 6), dpi=self.dpi)
        
        ax.plot(range(len(times)), values, marker='o', linewidth=2, markersize=8, color='#667eea')
        ax.fill_between(range(len(times)), values, alpha=0.3, color='#667eea')
        
        ax.set_xticks(range(len(times)))
        ax.set_xticklabels(times, rotation=45, ha='right')
        
        ax.set_xlabel('时间', fontsize=12, fontweight='bold')
        ax.set_ylabel('数量/热度', fontsize=12, fontweight='bold')
        ax.set_title('数据时间趋势', fontsize=16, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def generate_comparison_chart(self, data1: Dict[str, Any], data2: Dict[str, Any], 
                                  labels: Tuple[str, str] = ('数据集A', '数据集B')) -> str:
        """生成对比图表"""
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=self.dpi)
        
        # 这里可以实现对比逻辑
        # 暂时留空，根据实际需求实现
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _fig_to_base64(self, fig) -> str:
        """将matplotlib图形转换为base64编码的字符串"""
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=self.dpi)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return f"data:image/png;base64,{img_base64}"


# 便捷函数
def visualize_data(data: Dict[str, Any]) -> Dict[str, str]:
    """
    便捷函数：生成数据可视化
    
    Args:
        data: AI分析后的数据
    
    Returns:
        包含所有图表base64编码的字典
    """
    visualizer = DataVisualizer()
    return visualizer.generate_all_visualizations(data)


def visualize_single_chart(data: Dict[str, Any], chart_type: str) -> str:
    """
    便捷函数：生成单个图表
    
    Args:
        data: 数据
        chart_type: 图表类型 (wordcloud, sentiment_pie, category_bar, keyword_bar, stats_chart, timeline)
    
    Returns:
        图表的base64编码
    """
    visualizer = DataVisualizer()
    
    if chart_type == 'wordcloud':
        return visualizer.generate_wordcloud(data)
    elif chart_type == 'sentiment_pie':
        return visualizer.generate_sentiment_pie(data.get('sentiment_distribution', {}))
    elif chart_type == 'category_bar':
        return visualizer.generate_category_bar(data.get('categories', {}))
    elif chart_type == 'keyword_bar':
        return visualizer.generate_keyword_bar(data.get('keywords', []))
    elif chart_type == 'stats_chart':
        return visualizer.generate_stats_chart(data.get('statistics', {}))
    elif chart_type == 'timeline':
        return visualizer.generate_timeline(data.get('timeline', []))
    else:
        return None
