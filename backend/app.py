from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from functools import wraps
import os
import json
from datetime import datetime
import uuid
import threading
import time

from models import init_db, User, ConfigFile, CrawlerTask, CrawlerResult, AIConfig, Visualization
from services.crawler_service import CrawlerService
from call_ai import analyze_crawler_data
from show import visualize_data

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

@app.route('/api/task/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    user_id = session['user_id']
    task = CrawlerTask.get_by_id(task_id)
    
    if not task or task.user_id != user_id:
        return jsonify({'success': False, 'message': '任务不存在'})
    
    # 如果任务正在运行，先停止它
    if task.status == '进行中':
        crawler_service.stop_task(task_id)
    
    # 删除相关的爬虫结果
    CrawlerResult.delete_by_task_id(task_id)
    
    # 删除任务
    CrawlerTask.delete_by_id(task_id)
    
    return jsonify({'success': True, 'message': '任务已删除'})

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


# ========== AI配置路由 ==========

@app.route('/api/ai-config/list', methods=['GET'])
@login_required
def list_ai_configs():
    """获取用户的AI配置列表"""
    user_id = session['user_id']
    configs = AIConfig.get_by_user(user_id)
    
    return jsonify({
        'success': True,
        'configs': [config.to_dict() for config in configs]
    })


@app.route('/api/ai-config/<int:config_id>', methods=['GET'])
@login_required
def get_ai_config(config_id):
    """获取单个AI配置"""
    user_id = session['user_id']
    config = AIConfig.get_by_id(config_id)
    
    if not config or config.user_id != user_id:
        return jsonify({'success': False, 'message': '配置不存在'})
    
    return jsonify({
        'success': True,
        'config': config.to_dict(include_api_key=True)
    })


@app.route('/api/ai-config/create', methods=['POST'])
@login_required
def create_ai_config():
    """创建新的AI配置"""
    user_id = session['user_id']
    data = request.get_json()
    
    name = data.get('name')
    config_type = data.get('config_type', 'api')
    base_url = data.get('base_url')
    api_key = data.get('api_key')
    model_name = data.get('model_name')
    is_default = data.get('is_default', False)
    
    if not name:
        return jsonify({'success': False, 'message': '配置名称不能为空'})
    
    if config_type == 'api' and not base_url:
        return jsonify({'success': False, 'message': 'API配置需要Base URL'})
    
    try:
        config = AIConfig.create(
            user_id=user_id,
            name=name,
            config_type=config_type,
            base_url=base_url,
            api_key=api_key,
            model_name=model_name,
            is_default=is_default
        )
        
        return jsonify({
            'success': True,
            'message': '配置创建成功',
            'config': config.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'创建配置失败: {str(e)}'})


@app.route('/api/ai-config/<int:config_id>', methods=['PUT'])
@login_required
def update_ai_config(config_id):
    """更新AI配置"""
    user_id = session['user_id']
    config = AIConfig.get_by_id(config_id)
    
    if not config or config.user_id != user_id:
        return jsonify({'success': False, 'message': '配置不存在'})
    
    data = request.get_json()
    
    name = data.get('name')
    config_type = data.get('config_type')
    base_url = data.get('base_url')
    api_key = data.get('api_key')
    model_name = data.get('model_name')
    is_default = data.get('is_default')
    
    try:
        config.update(
            name=name,
            config_type=config_type,
            base_url=base_url,
            api_key=api_key,
            model_name=model_name,
            is_default=is_default
        )
        
        return jsonify({
            'success': True,
            'message': '配置更新成功',
            'config': config.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新配置失败: {str(e)}'})


@app.route('/api/ai-config/<int:config_id>', methods=['DELETE'])
@login_required
def delete_ai_config(config_id):
    """删除AI配置"""
    user_id = session['user_id']
    config = AIConfig.get_by_id(config_id)
    
    if not config or config.user_id != user_id:
        return jsonify({'success': False, 'message': '配置不存在'})
    
    try:
        AIConfig.delete(config_id)
        return jsonify({'success': True, 'message': '配置已删除'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除配置失败: {str(e)}'})


@app.route('/api/ai-config/<int:config_id>/set-default', methods=['POST'])
@login_required
def set_default_ai_config(config_id):
    """设置默认AI配置"""
    user_id = session['user_id']
    config = AIConfig.get_by_id(config_id)
    
    if not config or config.user_id != user_id:
        return jsonify({'success': False, 'message': '配置不存在'})
    
    try:
        AIConfig.set_default(user_id, config_id)
        return jsonify({'success': True, 'message': '默认配置已设置'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'设置默认配置失败: {str(e)}'})


# ========== 可视化路由 ==========

@app.route('/api/visualization/generate', methods=['POST'])
@login_required
def generate_visualization():
    """生成数据可视化"""
    user_id = session['user_id']
    data = request.get_json()
    
    result_id = data.get('result_id')
    analysis_type = data.get('analysis_type', 'general')
    model_type = data.get('model_type', 'local')  # 'local' 或 'api'
    config_id = data.get('config_id')  # API配置ID
    
    print(f"\n[DEBUG] ========== 开始生成可视化 ==========")
    print(f"[DEBUG] 用户ID: {user_id}")
    print(f"[DEBUG] 结果ID: {result_id}")
    print(f"[DEBUG] 分析类型: {analysis_type}")
    print(f"[DEBUG] 模型类型: {model_type}")
    print(f"[DEBUG] 配置ID: {config_id}")
    
    if not result_id:
        return jsonify({'success': False, 'message': '请选择爬虫结果'})
    
    # 获取爬虫结果
    result = CrawlerResult.get_by_id(result_id)
    if not result:
        return jsonify({'success': False, 'message': '结果不存在'})
    
    task = CrawlerTask.get_by_id(result.task_id)
    if not task or task.user_id != user_id:
        return jsonify({'success': False, 'message': '无权访问'})
    
    try:
        # 获取原始数据
        crawler_data = result.get_content_dict()
        print(f"[DEBUG] 爬虫数据条数: {len(crawler_data) if isinstance(crawler_data, list) else 1}")
        print(f"[DEBUG] 爬虫数据样本: {str(crawler_data)[:200]}...")
        
        # 准备AI配置
        ai_config = None
        if model_type == 'api':
            print(f"[DEBUG] 使用API模式，准备AI配置...")
            if config_id:
                # 使用指定的配置
                ai_config_obj = AIConfig.get_by_id(config_id)
                if ai_config_obj and ai_config_obj.user_id == user_id:
                    ai_config = ai_config_obj.to_dict(include_api_key=True)
                    print(f"[DEBUG] 使用指定配置ID={config_id}")
                    print(f"[DEBUG] 配置名称: {ai_config.get('name')}")
                    print(f"[DEBUG] Base URL: {ai_config.get('base_url')}")
                    print(f"[DEBUG] 模型名称: {ai_config.get('model_name')}")
                    print(f"[DEBUG] API Key存在: {bool(ai_config.get('api_key'))}")
                    if ai_config.get('api_key'):
                        print(f"[DEBUG] API Key前10位: {ai_config.get('api_key')[:10]}...")
                else:
                    print(f"[ERROR] API配置不存在或无权访问")
                    return jsonify({'success': False, 'message': 'API配置不存在'})
            else:
                # 使用默认配置
                print(f"[DEBUG] 未指定配置ID，尝试获取默认配置...")
                default_config = AIConfig.get_default_by_user(user_id)
                if default_config:
                    ai_config = default_config.to_dict(include_api_key=True)
                    print(f"[DEBUG] 使用默认配置ID={default_config.id}")
                    print(f"[DEBUG] 配置名称: {ai_config.get('name')}")
                    print(f"[DEBUG] Base URL: {ai_config.get('base_url')}")
                    print(f"[DEBUG] 模型名称: {ai_config.get('model_name')}")
                    print(f"[DEBUG] API Key存在: {bool(ai_config.get('api_key'))}")
                else:
                    print(f"[ERROR] 未找到默认配置")
                    return jsonify({'success': False, 'message': '请先配置API'})
        else:
            print(f"[DEBUG] 使用本地模型模式")
        
        print(f"[DEBUG] 开始调用AI模型进行数据分析...")
        # 调用AI模型进行数据分析
        ai_result = analyze_crawler_data(crawler_data, analysis_type, ai_config)
        
        print(f"[DEBUG] AI分析结果状态: {ai_result.get('success')}")
        if not ai_result['success']:
            print(f"[ERROR] AI分析失败: {ai_result.get('error')}")
            return jsonify({'success': False, 'message': f"AI分析失败: {ai_result.get('error', '未知错误')}"})
        
        print(f"[DEBUG] AI分析成功，数据键: {list(ai_result['data'].keys()) if isinstance(ai_result['data'], dict) else '非字典类型'}")
        print(f"[DEBUG] AI结果数据样本: {str(ai_result['data'])[:300]}...")
        
        print(f"[DEBUG] 开始生成可视化图表...")
        # 生成可视化
        visualization = visualize_data(ai_result['data'])
        
        print(f"[DEBUG] 可视化生成完成，图表数量: {len([v for v in visualization.values() if v])}")
        print(f"[DEBUG] ========== 生成可视化完成 ==========\n")
        
        return jsonify({
            'success': True,
            'visualization': visualization,
            'analysis_data': ai_result['data']
        })
    except Exception as e:
        print(f"[ERROR] 生成可视化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f"生成可视化失败: {str(e)}"})


@app.route('/api/visualization/save', methods=['POST'])
@login_required
def save_visualization():
    """保存可视化记录"""
    try:
        data = request.json
        user_id = session['user_id']
        
        result_id = data.get('result_id')
        name = data.get('name', f'可视化_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        visualization_data = data.get('visualization_data', {})
        analysis_type = data.get('analysis_type', 'general')
        model_type = data.get('model_type', 'local')
        
        if not result_id:
            return jsonify({'success': False, 'message': '缺少结果ID'})
        
        # 创建可视化记录
        viz = Visualization.create(
            user_id=user_id,
            result_id=result_id,
            name=name,
            visualization_data=visualization_data,
            analysis_type=analysis_type,
            model_type=model_type
        )
        
        return jsonify({
            'success': True,
            'message': '可视化保存成功',
            'visualization': viz.to_dict()
        })
    except Exception as e:
        print(f"[ERROR] 保存可视化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f"保存失败: {str(e)}"})


@app.route('/api/visualization/list', methods=['GET'])
@login_required
def list_visualizations():
    """获取用户的可视化列表"""
    try:
        user_id = session['user_id']
        result_id = request.args.get('result_id', type=int)
        
        if result_id:
            visualizations = Visualization.get_by_result(result_id, user_id)
        else:
            visualizations = Visualization.get_by_user(user_id)
        
        return jsonify({
            'success': True,
            'visualizations': [v.to_dict() for v in visualizations]
        })
    except Exception as e:
        print(f"[ERROR] 获取可视化列表失败: {str(e)}")
        return jsonify({'success': False, 'message': f"获取列表失败: {str(e)}"})


@app.route('/api/visualization/<int:viz_id>', methods=['GET'])
@login_required
def get_visualization(viz_id):
    """获取单个可视化详情"""
    try:
        user_id = session['user_id']
        viz = Visualization.get_by_id(viz_id)
        
        if not viz or viz.user_id != user_id:
            return jsonify({'success': False, 'message': '可视化记录不存在'})
        
        return jsonify({
            'success': True,
            'visualization': viz.to_dict()
        })
    except Exception as e:
        print(f"[ERROR] 获取可视化详情失败: {str(e)}")
        return jsonify({'success': False, 'message': f"获取详情失败: {str(e)}"})


@app.route('/api/visualization/<int:viz_id>', methods=['DELETE'])
@login_required
def delete_visualization(viz_id):
    """删除可视化记录"""
    try:
        user_id = session['user_id']
        viz = Visualization.get_by_id(viz_id)
        
        if not viz or viz.user_id != user_id:
            return jsonify({'success': False, 'message': '可视化记录不存在'})
        
        viz.delete()
        
        return jsonify({
            'success': True,
            'message': '可视化已删除'
        })
    except Exception as e:
        print(f"[ERROR] 删除可视化失败: {str(e)}")
        return jsonify({'success': False, 'message': f"删除失败: {str(e)}"})


if __name__ == '__main__':
    init_db()
    print("Database initialized!")
    app.run(debug=True, host='0.0.0.0', port=5000)
