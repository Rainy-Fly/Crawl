from .database import get_db
from typing import Dict, List, Any, Optional

class Visualization:
    """可视化记录模型"""
    
    def __init__(self, id=None, user_id=None, result_id=None, name=None,
                 wordcloud=None, sentiment_pie=None, category_bar=None,
                 keyword_bar=None, stats_chart=None, timeline=None,
                 analysis_type=None, model_type=None, create_time=None):
        self.id = id
        self.user_id = user_id
        self.result_id = result_id
        self.name = name
        self.wordcloud = wordcloud
        self.sentiment_pie = sentiment_pie
        self.category_bar = category_bar
        self.keyword_bar = keyword_bar
        self.stats_chart = stats_chart
        self.timeline = timeline
        self.analysis_type = analysis_type
        self.model_type = model_type
        self.create_time = create_time
    
    @staticmethod
    def create(user_id: int, result_id: int, name: str, 
               visualization_data: Dict[str, str],
               analysis_type: str = 'general',
               model_type: str = 'local') -> 'Visualization':
        """创建新的可视化记录"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO visualizations 
            (user_id, result_id, name, wordcloud, sentiment_pie, 
             category_bar, keyword_bar, stats_chart, timeline,
             analysis_type, model_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, result_id, name,
            visualization_data.get('wordcloud'),
            visualization_data.get('sentiment_pie'),
            visualization_data.get('category_bar'),
            visualization_data.get('keyword_bar'),
            visualization_data.get('stats_chart'),
            visualization_data.get('timeline'),
            analysis_type,
            model_type
        ))
        
        viz_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return Visualization.get_by_id(viz_id)
    
    @staticmethod
    def get_by_id(viz_id: int) -> Optional['Visualization']:
        """根据ID获取可视化记录"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM visualizations WHERE id = ?', (viz_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Visualization._row_to_obj(row)
        return None
    
    @staticmethod
    def get_by_user(user_id: int) -> List['Visualization']:
        """获取用户的所有可视化记录"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM visualizations 
            WHERE user_id = ? 
            ORDER BY create_time DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [Visualization._row_to_obj(row) for row in rows]
    
    @staticmethod
    def get_by_result(result_id: int, user_id: int) -> List['Visualization']:
        """获取特定结果的所有可视化记录"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM visualizations 
            WHERE result_id = ? AND user_id = ?
            ORDER BY create_time DESC
        ''', (result_id, user_id))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [Visualization._row_to_obj(row) for row in rows]
    
    def delete(self) -> bool:
        """删除可视化记录"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM visualizations WHERE id = ?', (self.id,))
        conn.commit()
        conn.close()
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'result_id': self.result_id,
            'name': self.name,
            'wordcloud': self.wordcloud,
            'sentiment_pie': self.sentiment_pie,
            'category_bar': self.category_bar,
            'keyword_bar': self.keyword_bar,
            'stats_chart': self.stats_chart,
            'timeline': self.timeline,
            'analysis_type': self.analysis_type,
            'model_type': self.model_type,
            'create_time': self.create_time
        }
    
    @staticmethod
    def _row_to_obj(row) -> 'Visualization':
        """将数据库行转换为对象"""
        return Visualization(
            id=row['id'],
            user_id=row['user_id'],
            result_id=row['result_id'],
            name=row['name'],
            wordcloud=row['wordcloud'],
            sentiment_pie=row['sentiment_pie'],
            category_bar=row['category_bar'],
            keyword_bar=row['keyword_bar'],
            stats_chart=row['stats_chart'],
            timeline=row['timeline'],
            analysis_type=row['analysis_type'],
            model_type=row['model_type'],
            create_time=row['create_time']
        )
