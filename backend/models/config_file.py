import json
from .database import get_db

class ConfigFile:
    def __init__(self, id=None, user_id=None, name=None, type=None, content=None, create_time=None):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.type = type
        self.content = content
        self.create_time = create_time
    
    @classmethod
    def create(cls, user_id, name, config_type, content):
        if isinstance(content, dict):
            content = json.dumps(content, ensure_ascii=False)
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO config_files (user_id, name, type, content) VALUES (?, ?, ?, ?)',
            (user_id, name, config_type, content)
        )
        conn.commit()
        config_id = cursor.lastrowid
        conn.close()
        
        return cls.get_by_id(config_id)
    
    @classmethod
    def get_by_id(cls, config_id):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM config_files WHERE id = ?', (config_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return cls(
            id=row['id'],
            user_id=row['user_id'],
            name=row['name'],
            type=row['type'],
            content=row['content'],
            create_time=row['create_time']
        )
    
    @classmethod
    def get_by_user(cls, user_id, config_type=None):
        conn = get_db()
        cursor = conn.cursor()
        
        if config_type:
            cursor.execute(
                'SELECT * FROM config_files WHERE user_id = ? AND type = ? ORDER BY create_time DESC',
                (user_id, config_type)
            )
        else:
            cursor.execute(
                'SELECT * FROM config_files WHERE user_id = ? ORDER BY create_time DESC',
                (user_id,)
            )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [cls(
            id=row['id'],
            user_id=row['user_id'],
            name=row['name'],
            type=row['type'],
            content=row['content'],
            create_time=row['create_time']
        ) for row in rows]
    
    def update(self, name=None, content=None):
        if content and isinstance(content, dict):
            content = json.dumps(content, ensure_ascii=False)
        
        conn = get_db()
        cursor = conn.cursor()
        
        if name and content:
            cursor.execute(
                'UPDATE config_files SET name = ?, content = ? WHERE id = ?',
                (name, content, self.id)
            )
        elif name:
            cursor.execute(
                'UPDATE config_files SET name = ? WHERE id = ?',
                (name, self.id)
            )
        elif content:
            cursor.execute(
                'UPDATE config_files SET content = ? WHERE id = ?',
                (content, self.id)
            )
        
        conn.commit()
        conn.close()
        
        if name:
            self.name = name
        if content:
            self.content = content
        
        return self
    
    def delete(self):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM config_files WHERE id = ?', (self.id,))
        conn.commit()
        conn.close()
        
        return True
    
    def get_content_dict(self):
        try:
            return json.loads(self.content)
        except:
            return {}
