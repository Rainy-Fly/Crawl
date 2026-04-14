import bcrypt
from .database import get_db

class User:
    def __init__(self, id=None, username=None, password=None, create_time=None):
        self.id = id
        self.username = username
        self.password = password
        self.create_time = create_time
    
    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password, hashed):
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @classmethod
    def register(cls, username, password):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            conn.close()
            return None, "用户名已存在"
        
        hashed_password = cls.hash_password(password)
        
        cursor.execute(
            'INSERT INTO users (username, password) VALUES (?, ?)',
            (username, hashed_password)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return cls(id=user_id, username=username), None
    
    @classmethod
    def login(cls, username, password):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None, "用户不存在"
        
        if not cls.verify_password(password, row['password']):
            return None, "密码错误"
        
        return cls(
            id=row['id'],
            username=row['username'],
            password=row['password'],
            create_time=row['create_time']
        ), None
    
    @classmethod
    def get_by_id(cls, user_id):
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return cls(
            id=row['id'],
            username=row['username'],
            password=row['password'],
            create_time=row['create_time']
        )
