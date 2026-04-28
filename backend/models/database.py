import sqlite3
from datetime import datetime
from pathlib import Path

DATABASE_PATH = Path(__file__).parent.parent.parent / 'database' / 'crawl.db'

def get_db():
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    DATABASE_PATH.parent.mkdir(exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            type VARCHAR(20) NOT NULL,
            content TEXT NOT NULL,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawler_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            config_id INTEGER NOT NULL,
            time_config_id INTEGER,
            status VARCHAR(20) DEFAULT '未开始',
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            start_time DATETIME,
            end_time DATETIME,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (config_id) REFERENCES config_files (id),
            FOREIGN KEY (time_config_id) REFERENCES config_files (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawler_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_saved BOOLEAN DEFAULT 0,
            FOREIGN KEY (task_id) REFERENCES crawler_tasks (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            config_type VARCHAR(20) NOT NULL,
            base_url VARCHAR(500),
            api_key VARCHAR(500),
            model_name VARCHAR(100),
            is_default BOOLEAN DEFAULT 0,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visualizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            result_id INTEGER NOT NULL,
            name VARCHAR(200) NOT NULL,
            wordcloud TEXT,
            sentiment_pie TEXT,
            category_bar TEXT,
            keyword_bar TEXT,
            stats_chart TEXT,
            timeline TEXT,
            analysis_type VARCHAR(50),
            model_type VARCHAR(50),
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (result_id) REFERENCES crawler_results (id)
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
