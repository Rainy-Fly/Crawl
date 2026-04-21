import json
from .database import get_db

class CrawlerResult:
    def __init__(self, id=None, task_id=None, content=None, create_time=None, is_saved=False):
        self.id = id
        self.task_id = task_id
        self.content = content
        self.create_time = create_time
        self.is_saved = is_saved
    
    @classmethod
    def create(cls, task_id, content):
        try:
            # 确保内容被正确序列化为 JSON 字符串
            if isinstance(content, (dict, list)):
                content = json.dumps(content, ensure_ascii=False)
            elif not isinstance(content, str):
                content = str(content)
            
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT INTO crawler_results (task_id, content, is_saved) VALUES (?, ?, ?)',
                (task_id, content, False)
            )
            conn.commit()
            result_id = cursor.lastrowid
            conn.close()
            
            return cls.get_by_id(result_id)
        except Exception as e:
            print(f"Error creating CrawlerResult: {e}")
            raise
    
    @classmethod
    def get_by_id(cls, result_id):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM crawler_results WHERE id = ?', (result_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return cls(
            id=row['id'],
            task_id=row['task_id'],
            content=row['content'],
            create_time=row['create_time'],
            is_saved=bool(row['is_saved'])
        )
    
    @classmethod
    def get_by_task(cls, task_id):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM crawler_results WHERE task_id = ?', (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return cls(
            id=row['id'],
            task_id=row['task_id'],
            content=row['content'],
            create_time=row['create_time'],
            is_saved=bool(row['is_saved'])
        )
    
    @classmethod
    def get_by_user(cls, user_id):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT cr.* FROM crawler_results cr
            JOIN crawler_tasks ct ON cr.task_id = ct.id
            WHERE ct.user_id = ?
            ORDER BY cr.create_time DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [cls(
            id=row['id'],
            task_id=row['task_id'],
            content=row['content'],
            create_time=row['create_time'],
            is_saved=bool(row['is_saved'])
        ) for row in rows]
    
    @classmethod
    def get_all_by_user(cls, user_id):
        return cls.get_by_user(user_id)
    
    @classmethod
    def get_saved_by_user(cls, user_id):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT cr.* FROM crawler_results cr
            JOIN crawler_tasks ct ON cr.task_id = ct.id
            WHERE ct.user_id = ? AND cr.is_saved = 1
            ORDER BY cr.create_time DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [cls(
            id=row['id'],
            task_id=row['task_id'],
            content=row['content'],
            create_time=row['create_time'],
            is_saved=bool(row['is_saved'])
        ) for row in rows]
    
    @classmethod
    def get_unsaved_by_user(cls, user_id):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT cr.* FROM crawler_results cr
            JOIN crawler_tasks ct ON cr.task_id = ct.id
            WHERE ct.user_id = ? AND cr.is_saved = 0
            ORDER BY cr.create_time DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [cls(
            id=row['id'],
            task_id=row['task_id'],
            content=row['content'],
            create_time=row['create_time'],
            is_saved=bool(row['is_saved'])
        ) for row in rows]
    
    def save_to_db(self):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE crawler_results SET is_saved = ? WHERE id = ?',
            (True, self.id)
        )
        conn.commit()
        conn.close()
        
        self.is_saved = True
        return self
    
    def update_content(self, content):
        if isinstance(content, (dict, list)):
            content = json.dumps(content, ensure_ascii=False)
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE crawler_results SET content = ? WHERE id = ?',
            (content, self.id)
        )
        conn.commit()
        conn.close()
        
        self.content = content
        return self
    
    def get_content_dict(self):
        try:
            if isinstance(self.content, str):
                return json.loads(self.content)
            elif isinstance(self.content, (dict, list)):
                return self.content
            else:
                return {}
        except Exception as e:
            print(f"Error parsing content: {e}, content type: {type(self.content)}")
            return {}
    
    def delete(self):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM crawler_results WHERE id = ?', (self.id,))
        conn.commit()
        conn.close()
        
        return True
    
    @classmethod
    def delete_by_task_id(cls, task_id):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM crawler_results WHERE task_id = ?', (task_id,))
        conn.commit()
        conn.close()
        
        return True
