from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from functools import wraps
import os
import json
from datetime import datetime
import uuid
import threading
import time

from models import init_db, User, ConfigFile, CrawlerTask, CrawlerResult
from services.crawler_service import CrawlerService

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.secret_key = 'crawler_system_secret_key_2024'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24小时
CORS(app, supports_credentials=True, resources={
    r"/api/*": {
        "origins": ["http://127.0.0.1:5000", "http://localhost:5000"],
        "supports_credentials": True
    }
})

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

crawler_service = CrawlerService()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            response = jsonify({'success': False, 'message': '请先登录'})
            response.status_code = 401
            return response
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'sign.html')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory(BASE_DIR, filename)

@app.route('/static/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'static', 'css'), filename)

@app.route('/static/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'static', 'js'), filename)

@app.route('/static/images/<path:filename>')
def serve_images(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'static', 'images'), filename)

# ========== 用户认证路由 ==========

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'})
    
    user, error = User.register(username, password)
    if user:
        # 注册成功后自动登录
        session.permanent = True
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({'success': True, 'message': '注册成功', 'user_id': user.id, 'username': user.username})
    else:
        return jsonify({'success': False, 'message': error})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'})
    
    user, error = User.login(username, password)
    if user:
        session.permanent = True
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({'success': True, 'message': '登录成功', 'user_id': user.id, 'username': user.username})
    else:
        return jsonify({'success': False, 'message': error})

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    return jsonify({'success': True, 'message': '退出成功'})

@app.route('/api/user/info', methods=['GET'])
@login_required
def get_user_info():
    user = User.get_by_id(session['user_id'])
    if user:
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'create_time': user.create_time
            }
        })
    return jsonify({'success': False, 'message': '用户不存在'})

# ========== 配置文件路由 ==========

@app.route('/api/config/upload', methods=['POST'])
@login_required
def upload_config():
    user_id = session['user_id']
    
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '未选择文件'})
        
        try:
            content = file.read().decode('utf-8')
            data = json.loads(content)
            config_type = data.get('type', 'crawler')
            name = file.filename
        except:
            return jsonify({'success': False, 'message': '无效的JSON文件'})
    else:
        data = request.get_json()
        content = json.dumps(data.get('content'), ensure_ascii=False)
        config_type = data.get('type', 'crawler')
        name = data.get('name', f"config_{int(time.time())}.json")
    
    config = ConfigFile.create(user_id, name, config_type, content)
    return jsonify({
        'success': True,
        'message': '上传成功',
        'config': {
            'id': config.id,
            'name': config.name,
            'type': config.type,
            'create_time': config.create_time
        }
    })

@app.route('/api/config/list', methods=['GET'])
@login_required
def list_configs():
    user_id = session['user_id']
    config_type = request.args.get('type')
    
    configs = ConfigFile.get_by_user(user_id, config_type)
    return jsonify({
        'success': True,
        'configs': [{
            'id': c.id,
            'name': c.name,
            'type': c.type,
            'create_time': c.create_time
        } for c in configs]
    })

@app.route('/api/config/<int:config_id>', methods=['GET'])
@login_required
def get_config(config_id):
    user_id = session['user_id']
    config = ConfigFile.get_by_id(config_id)
    
    if not config or config.user_id != user_id:
        return jsonify({'success': False, 'message': '配置文件不存在'})
    
    return jsonify({
        'success': True,
        'config': {
            'id': config.id,
            'name': config.name,
            'type': config.type,
            'content': config.get_content_dict(),
            'create_time': config.create_time
        }
    })

@app.route('/api/config/<int:config_id>', methods=['PUT'])
@login_required
def update_config(config_id):
    user_id = session['user_id']
    config = ConfigFile.get_by_id(config_id)
    
    if not config or config.user_id != user_id:
        return jsonify({'success': False, 'message': '配置文件不存在'})
    
    data = request.get_json()
    name = data.get('name', config.name)
    content = json.dumps(data.get('content', config.get_content_dict()), ensure_ascii=False)
    
    config.update(name, content)
    return jsonify({'success': True, 'message': '更新成功'})

@app.route('/api/config/<int:config_id>', methods=['DELETE'])
@login_required
def delete_config(config_id):
    user_id = session['user_id']
    config = ConfigFile.get_by_id(config_id)
    
    if not config or config.user_id != user_id:
        return jsonify({'success': False, 'message': '配置文件不存在'})
    
    config.delete()
    return jsonify({'success': True, 'message': '删除成功'})

# ========== 爬虫任务路由 ==========

@app.route('/api/task/create', methods=['POST'])
@login_required
def create_task():
    user_id = session['user_id']
    data = request.get_json()
    
    config_id = data.get('config_id')
    time_config_id = data.get('time_config_id')
    
    if not config_id:
        return jsonify({'success': False, 'message': '请选择爬虫配置文件'})
    
    config = ConfigFile.get_by_id(config_id)
    if not config or config.user_id != user_id:
        return jsonify({'success': False, 'message': '配置文件不存在'})
    
    if time_config_id:
        time_config = ConfigFile.get_by_id(time_config_id)
        if not time_config or time_config.user_id != user_id:
            return jsonify({'success': False, 'message': '时间配置文件不存在'})
    
    task = CrawlerTask.create(user_id, config_id, time_config_id)
    
    if not time_config_id:
        crawler_service.start_task(task.id, config.get_content_dict())
    else:
        time_config_content = ConfigFile.get_by_id(time_config_id).get_content_dict()
        crawler_service.schedule_task(task.id, config.get_content_dict(), time_config_content)
    
    return jsonify({
        'success': True,
        'message': '任务创建成功',
        'task': {
            'id': task.id,
            'status': task.status,
            'create_time': task.create_time
        }
    })

@app.route('/api/task/list', methods=['GET'])
@login_required
def list_tasks():
    user_id = session['user_id']
    status = request.args.get('status')
    
    tasks = CrawlerTask.get_by_user(user_id, status)
    return jsonify({
        'success': True,
        'tasks': [{
            'id': t.id,
            'config_id': t.config_id,
            'time_config_id': t.time_config_id,
            'status': t.status,
            'create_time': t.create_time,
            'start_time': t.start_time,
            'end_time': t.end_time
        } for t in tasks]
    })

@app.route('/api/task/<int:task_id>/status', methods=['GET'])
@login_required
def get_task_status(task_id):
    user_id = session['user_id']
    task = CrawlerTask.get_by_id(task_id)
    
    if not task or task.user_id != user_id:
        return jsonify({'success': False, 'message': '任务不存在'})
    
    return jsonify({
        'success': True,
        'task': {
            'id': task.id,
            'status': task.status,
            'create_time': task.create_time,
            'start_time': t.start_time,
            'end_time': t.end_time
        }
    })

@app.route('/api/task/<int:task_id>/pause', methods=['POST'])
@login_required
def pause_task(task_id):
    user_id = session['user_id']
    task = CrawlerTask.get_by_id(task_id)
    
    if not task or task.user_id != user_id:
        return jsonify({'success': False, 'message': '任务不存在'})
    
    crawler_service.pause_task(task_id)
    task.pause()
    return jsonify({'success': True, 'message': '任务已暂停'})

@app.route('/api/task/<int:task_id>/resume', methods=['POST'])
@login_required
def resume_task(task_id):
    user_id = session['user_id']
    task = CrawlerTask.get_by_id(task_id)
    
    if not task or task.user_id != user_id:
        return jsonify({'success': False, 'message': '任务不存在'})
    
    config = ConfigFile.get_by_id(task.config_id)
    crawler_service.resume_task(task_id, config.get_content_dict())
    task.resume()
    return jsonify({'success': True, 'message': '任务已恢复'})

@app.route('/api/task/<int:task_id>/stop', methods=['POST'])
@login_required
def stop_task(task_id):
    user_id = session['user_id']
    task = CrawlerTask.get_by_id(task_id)
    
    if not task or task.user_id != user_id:
        return jsonify({'success': False, 'message': '任务不存在'})
    
    crawler_service.stop_task(task_id)
    task.stop()
    return jsonify({'success': True, 'message': '任务已停止'})

# ========== 爬虫结果路由 ==========

@app.route('/api/result/list', methods=['GET'])
@login_required
def list_results():
    user_id = session['user_id']
    is_saved = request.args.get('is_saved')
    
    if is_saved is not None:
        is_saved = is_saved.lower() == 'true'
        results = CrawlerResult.get_saved_by_user(user_id) if is_saved else CrawlerResult.get_unsaved_by_user(user_id)
    else:
        results = CrawlerResult.get_all_by_user(user_id)
    
    return jsonify({
        'success': True,
        'results': [{
            'id': r.id,
            'task_id': r.task_id,
            'is_saved': r.is_saved,
            'create_time': r.create_time,
            'preview': str(r.get_content_dict())[:100] + '...' if len(str(r.get_content_dict())) > 100 else str(r.get_content_dict())
        } for r in results]
    })

@app.route('/api/result/<int:result_id>', methods=['GET'])
@login_required
def get_result(result_id):
    user_id = session['user_id']
    result = CrawlerResult.get_by_id(result_id)
    
    if not result:
        return jsonify({'success': False, 'message': '结果不存在'})
    
    task = CrawlerTask.get_by_id(result.task_id)
    if not task or task.user_id != user_id:
        return jsonify({'success': False, 'message': '无权访问'})
    
    return jsonify({
        'success': True,
        'result': {
            'id': result.id,
            'task_id': result.task_id,
            'content': result.get_content_dict(),
            'is_saved': result.is_saved,
            'create_time': result.create_time
        }
    })

@app.route('/api/result/<int:result_id>/save', methods=['POST'])
@login_required
def save_result(result_id):
    user_id = session['user_id']
    result = CrawlerResult.get_by_id(result_id)
    
    if not result:
        return jsonify({'success': False, 'message': '结果不存在'})
    
    task = CrawlerTask.get_by_id(result.task_id)
    if not task or task.user_id != user_id:
        return jsonify({'success': False, 'message': '无权访问'})
    
    result.save_to_db()
    return jsonify({'success': True, 'message': '保存成功'})

@app.route('/api/result/<int:result_id>', methods=['DELETE'])
@login_required
def delete_result(result_id):
    user_id = session['user_id']
    result = CrawlerResult.get_by_id(result_id)
    
    if not result:
        return jsonify({'success': False, 'message': '结果不存在'})
    
    task = CrawlerTask.get_by_id(result.task_id)
    if not task or task.user_id != user_id:
        return jsonify({'success': False, 'message': '无权访问'})
    
    result.delete()
    return jsonify({'success': True, 'message': '删除成功'})

# ========== 示例配置路由 ==========

@app.route('/api/demo/config', methods=['GET'])
def get_demo_config():
    config_type = request.args.get('type', 'crawler')
    
    if config_type == 'crawler':
        return send_from_directory(BASE_DIR, 'crawl_demo_config.json')
    else:
        return send_from_directory(BASE_DIR, 'time_demo_config.json')

if __name__ == '__main__':
    init_db()
    print("Database initialized!")
    app.run(debug=True, host='0.0.0.0', port=5000)
