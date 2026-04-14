from datetime import datetime
from .database import get_db

class CrawlerTask:
    def __init__(self, id=None, user_id=None, config_id=None, time_config_id=None, 
                 status=None, create_time=None, start_time=None, end_time=None):
        self.id = id
        self.user_id = user_id
        self.config_id = config_id
        self.time_config_id = time_config_id
        self.status = status
        self.create_time = create_time
        self.start_time = start_time
        self.end_time = end_time
    
    @classmethod
    def create(cls, user_id, config_id, time_config_id=None):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO crawler_tasks (user_id, config_id, time_config_id, status) VALUES (?, ?, ?, ?)',
            (user_id, config_id, time_config_id, '未开始')
        )
        conn.commit()
        task_id = cursor.lastrowid
        conn.close()
        
        return cls.get_by_id(task_id)
    
    @classmethod
    def get_by_id(cls, task_id):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM crawler_tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return cls(
            id=row['id'],
            user_id=row['user_id'],
            config_id=row['config_id'],
            time_config_id=row['time_config_id'],
            status=row['status'],
            create_time=row['create_time'],
            start_time=row['start_time'],
            end_time=row['end_time']
        )
    
    @classmethod
    def get_by_user(cls, user_id, status=None):
        conn = get_db()
        cursor = conn.cursor()
        
        if status:
            cursor.execute(
                'SELECT * FROM crawler_tasks WHERE user_id = ? AND status = ? ORDER BY create_time DESC',
                (user_id, status)
            )
        else:
            cursor.execute(
                'SELECT * FROM crawler_tasks WHERE user_id = ? ORDER BY create_time DESC',
                (user_id,)
            )
        rows = cursor.fetchall()
        conn.close()
        
        return [cls(
            id=row['id'],
            user_id=row['user_id'],
            config_id=row['config_id'],
            time_config_id=row['time_config_id'],
            status=row['status'],
            create_time=row['create_time'],
            start_time=row['start_time'],
            end_time=row['end_time']
        ) for row in rows]
    
    def start(self):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE crawler_tasks SET status = ?, start_time = ? WHERE id = ?',
            ('进行中', datetime.now(), self.id)
        )
        conn.commit()
        conn.close()
        
        self.status = '进行中'
        self.start_time = datetime.now()
        return self
    
    def pause(self):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE crawler_tasks SET status = ? WHERE id = ?',
            ('已暂停', self.id)
        )
        conn.commit()
        conn.close()
        
        self.status = '已暂停'
        return self
    
    def resume(self):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE crawler_tasks SET status = ? WHERE id = ?',
            ('进行中', self.id)
        )
        conn.commit()
        conn.close()
        
        self.status = '进行中'
        return self
    
    def complete(self):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE crawler_tasks SET status = ?, end_time = ? WHERE id = ?',
            ('已完成', datetime.now(), self.id)
        )
        conn.commit()
        conn.close()
        
        self.status = '已完成'
        self.end_time = datetime.now()
        return self
    
    def stop(self):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE crawler_tasks SET status = ?, end_time = ? WHERE id = ?',
            ('已停止', datetime.now(), self.id)
        )
        conn.commit()
        conn.close()
        
        self.status = '已停止'
        self.end_time = datetime.now()
        return self
    
    def delete(self):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM crawler_results WHERE task_id = ?', (self.id,))
        cursor.execute('DELETE FROM crawler_tasks WHERE id = ?', (self.id,))
        conn.commit()
        conn.close()
        
        return True
