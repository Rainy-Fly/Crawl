const API_BASE = 'http://127.0.0.1:5000/api';

let currentConfigType = 'crawler';
let currentTaskStatus = '';
let currentResultFilter = '';

// 页面加载完成后检查登录状态
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
});

async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE}/user/info`, {
            credentials: 'include',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        // 如果返回 401，说明未登录
        if (response.status === 401) {
            if (!window.location.href.includes('sign.html')) {
                window.location.href = 'sign.html';
            }
            return;
        }
        
        const data = await response.json();
        
        if (!data.success) {
            if (!window.location.href.includes('sign.html')) {
                window.location.href = 'sign.html';
            }
        } else {
            const usernameEl = document.getElementById('username');
            if (usernameEl) {
                usernameEl.textContent = data.user.username;
            }
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        // 如果请求失败，也跳转到登录页
        if (!window.location.href.includes('sign.html')) {
            window.location.href = 'sign.html';
        }
    }
}

function showMessage(message, type = 'success') {
    const msgEl = document.getElementById('message');
    msgEl.textContent = message;
    msgEl.className = 'message ' + type;
    
    setTimeout(() => {
        msgEl.className = 'message';
    }, 3000);
}

async function logout() {
    try {
        await fetch(`${API_BASE}/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        window.location.href = 'sign.html';
    } catch (error) {
        showMessage('退出失败', 'error');
    }
}

// 显示不同区域
function showSection(section) {
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(section + '-section').classList.add('active');
    
    // 加载对应数据
    if (section === 'configs') {
        loadConfigList('crawler');
    } else if (section === 'tasks') {
        loadTaskConfigs();
        loadTaskList();
    } else if (section === 'results') {
        loadResultList();
    }
}

// 上传配置标签切换
function showUploadTab(type) {
    document.querySelectorAll('.upload-tabs .tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.upload-content').forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(type + '-upload').classList.add('active');
}

// 文件上传处理
document.addEventListener('DOMContentLoaded', function() {
    const crawlerFile = document.getElementById('crawler-file');
    const timeFile = document.getElementById('time-file');
    
    if (crawlerFile) {
        crawlerFile.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                // 自动填充文件名
                document.getElementById('crawler-filename').value = file.name;
                const reader = new FileReader();
                reader.onload = (event) => {
                    document.getElementById('crawler-json').value = event.target.result;
                };
                reader.readAsText(file);
            }
        });
    }
    
    if (timeFile) {
        timeFile.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                // 自动填充文件名
                document.getElementById('time-filename').value = file.name;
                const reader = new FileReader();
                reader.onload = (event) => {
                    document.getElementById('time-json').value = event.target.result;
                };
                reader.readAsText(file);
            }
        });
    }
});

// 上传配置
async function uploadConfig(type) {
    const textarea = document.getElementById(type + '-json');
    const filenameInput = document.getElementById(type + '-filename');
    const content = textarea.value.trim();
    let filename = filenameInput.value.trim();
    
    if (!content) {
        showMessage('请输入配置内容', 'error');
        return;
    }
    
    // 如果没有输入文件名，使用默认名称
    if (!filename) {
        filename = type + '_config_' + Date.now() + '.json';
    }
    
    // 确保文件名以 .json 结尾
    if (!filename.endsWith('.json')) {
        filename += '.json';
    }
    
    try {
        JSON.parse(content);
    } catch {
        showMessage('JSON格式错误', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/config/upload`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                content: JSON.parse(content),
                type: type,
                name: filename
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('上传成功！');
            textarea.value = '';
            filenameInput.value = '';
        } else {
            showMessage(data.message || '上传失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请稍后重试', 'error');
    }
}

// 显示示例配置
async function showDemoConfig(type) {
    try {
        const response = await fetch(`${API_BASE}/demo/config?type=${type}`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        document.getElementById('demo-modal-title').textContent = 
            type === 'crawler' ? '爬虫配置示例' : '时间配置示例';
        document.getElementById('demo-content').textContent = JSON.stringify(data, null, 2);
        
        openModal('demo-modal');
    } catch (error) {
        showMessage('加载示例失败', 'error');
    }
}

// 下载示例配置
function downloadDemoConfig(type) {
    const filename = type === 'crawler' ? 'crawl_demo_config.json' : 'time_demo_config.json';
    fetch(filename)
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        });
}

// 加载配置列表
async function loadConfigList(type) {
    currentConfigType = type;
    
    document.querySelectorAll('.config-tabs .tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    try {
        const response = await fetch(`${API_BASE}/config/list?type=${type}`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        const listEl = document.getElementById('config-list');
        
        if (!data.success || data.configs.length === 0) {
            listEl.innerHTML = '<div class="config-item"><p>暂无配置文件</p></div>';
            return;
        }
        
        listEl.innerHTML = data.configs.map(config => `
            <div class="config-item">
                <div class="config-info">
                    <h4>${config.name}</h4>
                    <p>创建时间: ${new Date(config.create_time).toLocaleString()}</p>
                </div>
                <div class="config-actions">
                    <button onclick="editConfig(${config.id})" class="btn btn-small btn-info">编辑</button>
                    <button onclick="deleteConfig(${config.id})" class="btn btn-small btn-danger">删除</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        showMessage('加载配置列表失败', 'error');
    }
}

// 编辑配置
async function editConfig(configId) {
    try {
        const response = await fetch(`${API_BASE}/config/${configId}`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('edit-config-id').value = configId;
            document.getElementById('edit-config-name').value = data.config.name;
            document.getElementById('edit-config-content').value = 
                JSON.stringify(data.config.content, null, 2);
            openModal('config-modal');
        }
    } catch (error) {
        showMessage('加载配置失败', 'error');
    }
}

// 保存配置编辑
async function saveConfigEdit() {
    const configId = document.getElementById('edit-config-id').value;
    const name = document.getElementById('edit-config-name').value;
    const contentStr = document.getElementById('edit-config-content').value;
    
    try {
        const content = JSON.parse(contentStr);
        
        const response = await fetch(`${API_BASE}/config/${configId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ name, content })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('保存成功！');
            closeModal('config-modal');
            loadConfigList(currentConfigType);
        } else {
            showMessage(data.message || '保存失败', 'error');
        }
    } catch {
        showMessage('JSON格式错误', 'error');
    }
}

// 删除配置
async function deleteConfig(configId) {
    if (!confirm('确定要删除这个配置文件吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/config/${configId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('删除成功！');
            loadConfigList(currentConfigType);
        } else {
            showMessage(data.message || '删除失败', 'error');
        }
    } catch (error) {
        showMessage('删除失败', 'error');
    }
}

// 加载任务配置选项
async function loadTaskConfigs() {
    try {
        const [crawlerRes, timeRes] = await Promise.all([
            fetch(`${API_BASE}/config/list?type=crawler`, { credentials: 'include' }),
            fetch(`${API_BASE}/config/list?type=time`, { credentials: 'include' })
        ]);
        
        const crawlerData = await crawlerRes.json();
        const timeData = await timeRes.json();
        
        const crawlerSelect = document.getElementById('task-crawler-config');
        const timeSelect = document.getElementById('task-time-config');
        
        if (crawlerSelect) {
            crawlerSelect.innerHTML = '<option value="">请选择...</option>' +
                (crawlerData.configs || []).map(c => `<option value="${c.id}">${c.name}</option>`).join('');
        }
        
        if (timeSelect) {
            timeSelect.innerHTML = '<option value="">立即执行</option>' +
                (timeData.configs || []).map(c => `<option value="${c.id}">${c.name}</option>`).join('');
        }
    } catch (error) {
        console.error('加载配置选项失败:', error);
    }
}

// 创建任务
async function createTask() {
    const configId = document.getElementById('task-crawler-config').value;
    const timeConfigId = document.getElementById('task-time-config').value;
    
    if (!configId) {
        showMessage('请选择爬虫配置文件', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/task/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ config_id: parseInt(configId), time_config_id: timeConfigId ? parseInt(timeConfigId) : null })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('任务创建成功！');
            loadTaskList();
        } else {
            showMessage(data.message || '创建失败', 'error');
        }
    } catch (error) {
        showMessage('网络错误，请稍后重试', 'error');
    }
}

// 加载任务列表
async function loadTaskList(status = '') {
    currentTaskStatus = status;
    
    document.querySelectorAll('.task-filters .btn').forEach(btn => btn.classList.remove('active'));
    if (event) event.target.classList.add('active');
    
    try {
        const url = status ? `${API_BASE}/task/list?status=${status}` : `${API_BASE}/task/list`;
        const response = await fetch(url, { credentials: 'include' });
        const data = await response.json();
        
        const listEl = document.getElementById('task-list');
        
        if (!data.success || data.tasks.length === 0) {
            listEl.innerHTML = '<p>暂无任务</p>';
            return;
        }
        
        listEl.innerHTML = data.tasks.map(task => {
            const statusClass = {
                '未开始': 'pending',
                '进行中': 'running',
                '已完成': 'completed',
                '已暂停': 'paused',
                '已停止': 'paused'
            }[task.status] || 'pending';
            
            let actions = '';
            if (task.status === '进行中') {
                actions = `
                    <button onclick="pauseTask(${task.id})" class="btn btn-small btn-warning">暂停</button>
                    <button onclick="stopTask(${task.id})" class="btn btn-small btn-danger">停止</button>
                `;
            } else if (task.status === '已暂停') {
                actions = `
                    <button onclick="resumeTask(${task.id})" class="btn btn-small btn-success">恢复</button>
                    <button onclick="stopTask(${task.id})" class="btn btn-small btn-danger">停止</button>
                `;
            } else if (task.status === '已完成') {
                actions = `
                    <button onclick="viewResult(${task.id})" class="btn btn-small btn-info">可视化</button>
                    <button onclick="saveResult(${task.id})" class="btn btn-small btn-success">保存</button>
                `;
            }
            // 所有状态的任务都可以删除
            actions += `<button onclick="deleteTask(${task.id})" class="btn btn-small btn-danger">删除</button>`;
            
            return `
                <div class="task-item">
                    <div class="task-info">
                        <h4>任务 #${task.id}</h4>
                        <div class="task-meta">
                            <span>配置ID: ${task.config_id}</span>
                            <span>创建时间: ${new Date(task.create_time).toLocaleString()}</span>
                            ${task.start_time ? `<span>开始: ${new Date(task.start_time).toLocaleString()}</span>` : ''}
                        </div>
                    </div>
                    <div>
                        <span class="task-status ${statusClass}">${task.status}</span>
                    </div>
                    <div class="task-actions">
                        ${actions}
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        showMessage('加载任务列表失败', 'error');
    }
}

// 任务操作
async function pauseTask(taskId) {
    try {
        const response = await fetch(`${API_BASE}/task/${taskId}/pause`, {
            method: 'POST',
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            showMessage('任务已暂停');
            loadTaskList(currentTaskStatus);
        }
    } catch (error) {
        showMessage('操作失败', 'error');
    }
}

async function resumeTask(taskId) {
    try {
        const response = await fetch(`${API_BASE}/task/${taskId}/resume`, {
            method: 'POST',
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            showMessage('任务已恢复');
            loadTaskList(currentTaskStatus);
        }
    } catch (error) {
        showMessage('操作失败', 'error');
    }
}

async function stopTask(taskId) {
    try {
        const response = await fetch(`${API_BASE}/task/${taskId}/stop`, {
            method: 'POST',
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            showMessage('任务已停止');
            loadTaskList(currentTaskStatus);
        }
    } catch (error) {
        showMessage('操作失败', 'error');
    }
}

function viewResult(taskId) {
    window.location.href = `show.html?task_id=${taskId}`;
}

// 删除任务
async function deleteTask(taskId) {
    if (!confirm('确定要删除这个任务吗？相关的爬虫结果也将被删除。')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/task/${taskId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            showMessage('任务删除成功！');
            loadTaskList(currentTaskStatus);
        } else {
            showMessage(data.message || '删除失败', 'error');
        }
    } catch (error) {
        showMessage('删除失败', 'error');
    }
}

async function saveResult(taskId) {
    try {
        const response = await fetch(`${API_BASE}/result/${taskId}/save`, {
            method: 'POST',
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            showMessage('结果已保存');
        } else {
            showMessage(data.message || '保存失败', 'error');
        }
    } catch (error) {
        showMessage('保存失败', 'error');
    }
}

// 加载结果列表
async function loadResultList(isSaved) {
    currentResultFilter = isSaved;
    
    document.querySelectorAll('.result-filters .btn').forEach(btn => btn.classList.remove('active'));
    if (event) event.target.classList.add('active');
    
    try {
        let url = `${API_BASE}/result/list`;
        if (isSaved !== undefined) {
            url += `?is_saved=${isSaved}`;
        }
        
        const response = await fetch(url, { credentials: 'include' });
        const data = await response.json();
        
        const listEl = document.getElementById('result-list');
        
        if (!data.success || data.results.length === 0) {
            listEl.innerHTML = '<div class="result-item"><p>暂无结果</p></div>';
            return;
        }
        
        listEl.innerHTML = data.results.map(result => `
            <div class="result-item">
                <div class="result-info">
                    <h4>结果 #${result.id} (任务 #${result.task_id})</h4>
                    <p>${result.preview}</p>
                    <p>创建时间: ${new Date(result.create_time).toLocaleString()}</p>
                </div>
                <div>
                    <span class="result-badge ${result.is_saved ? 'saved' : 'temp'}">
                        ${result.is_saved ? '已保存' : '临时'}
                    </span>
                    <div style="margin-top:10px">
                        <button onclick="viewResultDetail(${result.id})" class="btn btn-small btn-info">查看</button>
                        ${!result.is_saved ? `<button onclick="saveResultById(${result.id})" class="btn btn-small btn-success">保存</button>` : ''}
                        <button onclick="deleteResult(${result.id})" class="btn btn-small btn-danger">删除</button>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        showMessage('加载结果列表失败', 'error');
    }
}

function viewResultDetail(resultId) {
    window.location.href = `show.html?result_id=${resultId}`;
}

async function saveResultById(resultId) {
    try {
        const response = await fetch(`${API_BASE}/result/${resultId}/save`, {
            method: 'POST',
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            showMessage('结果已保存');
            loadResultList(currentResultFilter);
        } else {
            showMessage(data.message || '保存失败', 'error');
        }
    } catch (error) {
        showMessage('保存失败', 'error');
    }
}

async function deleteResult(resultId) {
    if (!confirm('确定要删除这个结果吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/result/${resultId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            showMessage('删除成功！');
            loadResultList(currentResultFilter);
        } else {
            showMessage(data.message || '删除失败', 'error');
        }
    } catch (error) {
        showMessage('删除失败', 'error');
    }
}

// 模态框操作
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// 点击模态框外部关闭
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
}
