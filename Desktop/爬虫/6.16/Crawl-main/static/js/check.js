const API_BASE = 'http://127.0.0.1:5000/api';

let currentResult = null;
let currentResultId = null;
let chartInstance = null;

// 检查登录状态
checkAuth();

async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE}/user/info`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (!data.success) {
            window.location.href = 'sign.html';
        } else {
            document.getElementById('username').textContent = data.user.username;
            loadResultLists();
            
            // 检查URL参数
            const urlParams = new URLSearchParams(window.location.search);
            const resultId = urlParams.get('result_id');
            if (resultId) {
                loadResultDetail(resultId);
            }
        }
    } catch (error) {
        console.error('Auth check failed:', error);
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

// 加载结果列表
async function loadResultLists() {
    try {
        // 加载已保存的结果
        const savedRes = await fetch(`${API_BASE}/result/list?is_saved=true`, {
            credentials: 'include'
        });
        const savedData = await savedRes.json();
        
        const savedEl = document.getElementById('saved-results');
        if (savedData.success && savedData.results.length > 0) {
            savedEl.innerHTML = savedData.results.map(r => `
                <div class="result-list-item" onclick="loadResultDetail(${r.id})" data-id="${r.id}">
                    <div class="title">结果 #${r.id}</div>
                    <div class="time">${new Date(r.create_time).toLocaleString()}</div>
                </div>
            `).join('');
        } else {
            savedEl.innerHTML = '<p style="color:#999;padding:10px;">暂无已保存结果</p>';
        }
        
        // 加载临时结果
        const tempRes = await fetch(`${API_BASE}/result/list?is_saved=false`, {
            credentials: 'include'
        });
        const tempData = await tempRes.json();
        
        const tempEl = document.getElementById('temp-results');
        if (tempData.success && tempData.results.length > 0) {
            tempEl.innerHTML = tempData.results.map(r => `
                <div class="result-list-item" onclick="loadResultDetail(${r.id})" data-id="${r.id}">
                    <div class="title">结果 #${r.id}</div>
                    <div class="time">${new Date(r.create_time).toLocaleString()}</div>
                </div>
            `).join('');
        } else {
            tempEl.innerHTML = '<p style="color:#999;padding:10px;">暂无临时结果</p>';
        }
    } catch (error) {
        console.error('加载结果列表失败:', error);
    }
}

// 加载结果详情
async function loadResultDetail(resultId) {
    try {
        const response = await fetch(`${API_BASE}/result/${resultId}`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            currentResult = data.result;
            currentResultId = resultId;
            
            // 更新选中状态
            document.querySelectorAll('.result-list-item').forEach(item => {
                item.classList.remove('active');
            });
            const activeItem = document.querySelector(`[data-id="${resultId}"]`);
            if (activeItem) activeItem.classList.add('active');
            
            // 显示内容
            document.getElementById('empty-state').style.display = 'none';
            document.getElementById('visualization-content').style.display = 'block';
            
            // 更新标题
            document.getElementById('result-title').textContent = `爬虫结果 #${resultId}`;
            
            // 更新统计
            updateStats(data.result.content);
            
            // 显示原始数据
            showRawData();
        }
    } catch (error) {
        showMessage('加载结果详情失败', 'error');
    }
}

// 更新统计数据
function updateStats(content) {
    let data;
    try {
        data = typeof content === 'string' ? JSON.parse(content) : content;
    } catch {
        data = [];
    }
    
    if (!Array.isArray(data)) data = [data];
    
    const totalUrls = data.length;
    const successCount = data.filter(item => !item.error).length;
    const failedCount = data.filter(item => item.error).length;
    
    // 计算数据条目数
    let itemCount = 0;
    data.forEach(item => {
        if (item.data) {
            Object.values(item.data).forEach(arr => {
                if (Array.isArray(arr)) itemCount += arr.length;
            });
        }
    });
    
    document.getElementById('stat-urls').textContent = totalUrls;
    document.getElementById('stat-success').textContent = successCount;
    document.getElementById('stat-failed').textContent = failedCount;
    document.getElementById('stat-items').textContent = itemCount;
}

// 显示原始数据
function showRawData() {
    if (!currentResult) return;
    
    document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
    document.getElementById('raw-view').classList.add('active');
    
    let content;
    try {
        content = typeof currentResult.content === 'string' 
            ? JSON.parse(currentResult.content) 
            : currentResult.content;
    } catch {
        content = currentResult.content;
    }
    
    document.getElementById('raw-json').textContent = JSON.stringify(content, null, 2);
}

// 显示表格视图
function showTableView() {
    if (!currentResult) return;
    
    document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
    document.getElementById('table-view').classList.add('active');
    
    let data;
    try {
        data = typeof currentResult.content === 'string' 
            ? JSON.parse(currentResult.content) 
            : currentResult.content;
    } catch {
        data = [];
    }
    
    if (!Array.isArray(data)) data = [data];
    
    const thead = document.querySelector('#data-table thead');
    const tbody = document.querySelector('#data-table tbody');
    
    if (data.length === 0) {
        thead.innerHTML = '';
        tbody.innerHTML = '<tr><td>暂无数据</td></tr>';
        return;
    }
    
    // 获取所有可能的列
    const columns = new Set(['url', 'title', 'error']);
    data.forEach(item => {
        if (item.data) {
            Object.keys(item.data).forEach(key => columns.add(key));
        }
    });
    
    // 渲染表头
    thead.innerHTML = '<tr>' + Array.from(columns).map(col => 
        `<th>${col}</th>`
    ).join('') + '</tr>';
    
    // 渲染数据行
    tbody.innerHTML = data.map(item => {
        return '<tr>' + Array.from(columns).map(col => {
            let value;
            if (col === 'url') value = item.url || '';
            else if (col === 'title') value = item.title || '';
            else if (col === 'error') value = item.error || '';
            else value = item.data?.[col] ? item.data[col].join(', ').substring(0, 100) : '';
            
            return `<td>${value}</td>`;
        }).join('') + '</tr>';
    }).join('');
}

// 显示图表视图
function showChartView() {
    if (!currentResult) return;
    
    document.querySelectorAll('.view-section').forEach(s => s.classList.remove('active'));
    document.getElementById('chart-view').classList.add('active');
    
    let data;
    try {
        data = typeof currentResult.content === 'string' 
            ? JSON.parse(currentResult.content) 
            : currentResult.content;
    } catch {
        data = [];
    }
    
    if (!Array.isArray(data)) data = [data];
    
    // 销毁旧图表
    if (chartInstance) {
        chartInstance.destroy();
    }
    
    // 统计数据
    const successCount = data.filter(item => !item.error).length;
    const failedCount = data.filter(item => item.error).length;
    
    // 创建图表
    const ctx = document.getElementById('data-chart').getContext('2d');
    chartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['成功', '失败'],
            datasets: [{
                data: [successCount, failedCount],
                backgroundColor: ['#28a745', '#dc3545'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                title: {
                    display: true,
                    text: '爬取结果统计'
                }
            }
        }
    });
}

// 导出数据
function exportData() {
    if (!currentResult) return;
    
    let content;
    try {
        content = typeof currentResult.content === 'string' 
            ? currentResult.content 
            : JSON.stringify(currentResult.content, null, 2);
    } catch {
        content = String(currentResult.content);
    }
    
    const blob = new Blob([content], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `crawler_result_${currentResultId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showMessage('数据已导出');
}

// 定期刷新结果列表
setInterval(loadResultLists, 30000);
