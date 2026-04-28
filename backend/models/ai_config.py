import json
from .database import get_db
from datetime import datetime


class AIConfig:
    """用户AI配置模型"""
    
    def __init__(self, id=None, user_id=None, name=None, config_type=None,
                 base_url=None, api_key=None, model_name=None, 
                 is_default=False, create_time=None, update_time=None):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.config_type = config_type  # 'local' 或 'api'
        self.base_url = base_url
        self.api_key = api_key
        self.model_name = model_name
        self.is_default = is_default
        self.create_time = create_time
        self.update_time = update_time
    
    @classmethod
    def create(cls, user_id, name, config_type, base_url=None, api_key=None, 
               model_name=None, is_default=False):
        """创建新的AI配置"""
        conn = get_db()
        cursor = conn.cursor()
        
        # 如果设置为默认，先将该用户的其他配置设为非默认
        if is_default:
            cursor.execute(
                'UPDATE ai_configs SET is_default = 0 WHERE user_id = ?',
                (user_id,)
            )
        
        cursor.execute('''
            INSERT INTO ai_configs 
            (user_id, name, config_type, base_url, api_key, model_name, is_default)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, config_type, base_url, api_key, model_name, is_default))
        
        conn.commit()
        config_id = cursor.lastrowid
        conn.close()
        
        return cls.get_by_id(config_id)
    
    @classmethod
    def get_by_id(cls, config_id):
        """根据ID获取配置"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM ai_configs WHERE id = ?', (config_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return cls._row_to_object(row)
    
    @classmethod
    def get_by_user(cls, user_id):
        """获取用户的所有配置"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM ai_configs WHERE user_id = ? ORDER BY is_default DESC, create_time DESC',
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [cls._row_to_object(row) for row in rows]
    
    @classmethod
    def get_default_by_user(cls, user_id):
        """获取用户的默认配置"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM ai_configs WHERE user_id = ? AND is_default = 1',
            (user_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            # 如果没有默认配置，返回第一个配置
            configs = cls.get_by_user(user_id)
            return configs[0] if configs else None
        
        return cls._row_to_object(row)
    
    def update(self, name=None, config_type=None, base_url=None, 
               api_key=None, model_name=None, is_default=None):
        """更新配置"""
        conn = get_db()
        cursor = conn.cursor()
        
        # 如果设置为默认，先将该用户的其他配置设为非默认
        if is_default:
            cursor.execute(
                'UPDATE ai_configs SET is_default = 0 WHERE user_id = ? AND id != ?',
                (self.user_id, self.id)
            )
        
        updates = []
        params = []
        
        if name is not None:
            updates.append('name = ?')
            params.append(name)
        if config_type is not None:
            updates.append('config_type = ?')
            params.append(config_type)
        if base_url is not None:
            updates.append('base_url = ?')
            params.append(base_url)
        if api_key is not None:
            updates.append('api_key = ?')
            params.append(api_key)
        if model_name is not None:
            updates.append('model_name = ?')
            params.append(model_name)
        if is_default is not None:
            updates.append('is_default = ?')
            params.append(is_default)
        
        if updates:
            params.append(self.id)
            cursor.execute(
                f"UPDATE ai_configs SET {', '.join(updates)}, update_time = CURRENT_TIMESTAMP WHERE id = ?",
                params
            )
            conn.commit()
        
        conn.close()
        return AIConfig.get_by_id(self.id)
    
    def delete(self):
        """删除配置"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM ai_configs WHERE id = ?', (self.id,))
        conn.commit()
        conn.close()
    
    def to_dict(self, include_api_key=False):
        """转换为字典"""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'config_type': self.config_type,
            'base_url': self.base_url,
            'model_name': self.model_name,
            'is_default': self.is_default,
            'create_time': self.create_time,
            'update_time': self.update_time
        }
        if include_api_key:
            result['api_key'] = self.api_key
        return result
    
    @classmethod
    def _row_to_object(cls, row):
        """将数据库行转换为对象"""
        return cls(
            id=row['id'],
            user_id=row['user_id'],
            name=row['name'],
            config_type=row['config_type'],
            base_url=row['base_url'],
            api_key=row['api_key'],
            model_name=row['model_name'],
            is_default=row['is_default'],
            create_time=row['create_time'],
            update_time=row['update_time']
        )
