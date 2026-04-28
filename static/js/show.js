const API_BASE = 'http://127.0.0.1:5000/api';

let currentResultId = null;
let currentAnalysisType = 'general';
let currentModelType = 'local';
let currentApiConfigId = null;
let currentVisualizationData = null;

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
            loadResultList();
            loadApiConfigs();
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
async function loadResultList() {
    try {
        const response = await fetch(`${API_BASE}/result/list`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        const listEl = document.getElementById('result-list-viz');
        
        if (!data.success || data.results.length === 0) {
            listEl.innerHTML = '<p style="color:#999;padding:10px;">暂无爬虫结果</p>';
            return;
        }
        
        listEl.innerHTML = data.results.map(r => `
            <div class="result-item-viz" onclick="selectResult(${r.id})" data-id="${r.id}">
                <div class="title">结果 #${r.id}</div>
                <div class="meta">任务 #${r.task_id} | ${new Date(r.create_time).toLocaleString()}</div>
            </div>
        `).join('');
        
        // 检查URL参数
        const urlParams = new URLSearchParams(window.location.search);
        const resultId = urlParams.get('result_id');
        if (resultId) {
            selectResult(parseInt(resultId));
        }
    } catch (error) {
        console.error('加载结果列表失败:', error);
        showMessage('加载结果列表失败', 'error');
    }
}

// 选择结果
function selectResult(resultId) {
    currentResultId = resultId;
    
    // 更新选中状态
    document.querySelectorAll('.result-item-viz').forEach(item => {
        item.classList.remove('active');
    });
    const activeItem = document.querySelector(`[data-id="${resultId}"]`);
    if (activeItem) activeItem.classList.add('active');
}

// 监听分析类型选择
document.querySelectorAll('input[name="analysis-type"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        currentAnalysisType = e.target.value;
    });
});

// 监听模型类型选择
document.querySelectorAll('input[name="model-type"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        currentModelType = e.target.value;
        updateApiInfoDisplay();
    });
});

// 更新API信息显示
function updateApiInfoDisplay() {
    const apiInfoDisplay = document.getElementById('api-info-display');
    const currentApiName = document.getElementById('current-api-name');
    
    if (currentModelType === 'api') {
        apiInfoDisplay.style.display = 'block';
        if (currentApiConfigId) {
            // 获取配置名称
            const configItem = document.querySelector(`#api-config-list [data-config-id="${currentApiConfigId}"]`);
            if (configItem) {
                currentApiName.textContent = configItem.querySelector('.config-name').textContent;
            }
        } else {
            currentApiName.textContent = '无';
        }
    } else {
        apiInfoDisplay.style.display = 'none';
    }
}

// ========== API配置管理 ==========

// 打开API配置弹窗
async function openApiConfigModal() {
    document.getElementById('api-config-modal').classList.add('active');
    await loadApiConfigs();
}

// 关闭API配置弹窗
function closeApiConfigModal() {
    document.getElementById('api-config-modal').classList.remove('active');
    clearConfigForm();
}

// 加载API配置列表
async function loadApiConfigs() {
    try {
        const response = await fetch(`${API_BASE}/ai-config/list`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        const listEl = document.getElementById('api-config-list');
        
        if (!data.success || data.configs.length === 0) {
            listEl.innerHTML = '<p style="color:#999;padding:10px;">暂无API配置，请添加</p>';
            return;
        }
        
        listEl.innerHTML = data.configs.map(config => `
            <div class="api-config-item ${config.is_default ? 'active' : ''}" 
                 data-config-id="${config.id}"
                 onclick="selectApiConfig(${config.id})">
                <div>
                    <span class="config-name">${config.name}</span>
                    ${config.is_default ? '<span class="config-default">默认</span>' : ''}
                </div>
                <div style="display:flex;align-items:center;gap:8px;">
                    <span class="config-type">${config.config_type === 'api' ? 'API' : '本地'}</span>
                    <button onclick="event.stopPropagation();editApiConfig(${config.id})" class="btn btn-small btn-info">编辑</button>
                    <button onclick="event.stopPropagation();deleteApiConfig(${config.id})" class="btn btn-small btn-delete">删除</button>
                </div>
            </div>
        `).join('');
        
        // 如果有默认配置，设置为当前选中
        const defaultConfig = data.configs.find(c => c.is_default);
        if (defaultConfig && !currentApiConfigId) {
            currentApiConfigId = defaultConfig.id;
            updateApiInfoDisplay();
        }
    } catch (error) {
        console.error('加载API配置失败:', error);
        showMessage('加载API配置失败', 'error');
    }
}

// 选择API配置
function selectApiConfig(configId) {
    currentApiConfigId = configId;
    
    // 更新选中状态
    document.querySelectorAll('.api-config-item').forEach(item => {
        item.classList.remove('active');
    });
    const activeItem = document.querySelector(`[data-config-id="${configId}"]`);
    if (activeItem) activeItem.classList.add('active');
    
    // 如果当前选择的是API模式，更新显示
    if (currentModelType === 'api') {
        updateApiInfoDisplay();
    }
    
    showMessage('API配置已选择');
}

// 编辑API配置
async function editApiConfig(configId) {
    try {
        const response = await fetch(`${API_BASE}/ai-config/${configId}`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            const config = data.config;
            document.getElementById('edit-config-id').value = config.id;
            document.getElementById('config-name').value = config.name;
            document.getElementById('config-base-url').value = config.base_url || '';
            document.getElementById('config-api-key').value = config.api_key || '';
            document.getElementById('config-model-name').value = config.model_name || '';
        }
    } catch (error) {
        showMessage('加载配置失败', 'error');
    }
}

// 保存API配置
async function saveApiConfig() {
    const configId = document.getElementById('edit-config-id').value;
    const name = document.getElementById('config-name').value.trim();
    const baseUrl = document.getElementById('config-base-url').value.trim();
    const apiKey = document.getElementById('config-api-key').value.trim();
    const modelName = document.getElementById('config-model-name').value.trim();
    
    if (!name) {
        showMessage('请输入配置名称', 'error');
        return;
    }
    
    if (!baseUrl) {
        showMessage('请输入Base URL', 'error');
        return;
    }
    
    try {
        const url = configId ? `${API_BASE}/ai-config/${configId}` : `${API_BASE}/ai-config/create`;
        const method = configId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                name: name,
                config_type: 'api',
                base_url: baseUrl,
                api_key: apiKey,
                model_name: modelName,
                is_default: true  // 新配置设为默认
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(configId ? '配置已更新' : '配置已创建');
            clearConfigForm();
            await loadApiConfigs();
            currentApiConfigId = data.config.id;
            updateApiInfoDisplay();
        } else {
            showMessage(data.message || '保存失败', 'error');
        }
    } catch (error) {
        showMessage('保存配置失败', 'error');
    }
}

// 删除API配置
async function deleteApiConfig(configId) {
    if (!confirm('确定要删除这个API配置吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/ai-config/${configId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('配置已删除');
            if (currentApiConfigId === configId) {
                currentApiConfigId = null;
                updateApiInfoDisplay();
            }
            await loadApiConfigs();
        } else {
            showMessage(data.message || '删除失败', 'error');
        }
    } catch (error) {
        showMessage('删除配置失败', 'error');
    }
}

// 清空配置表单
function clearConfigForm() {
    document.getElementById('edit-config-id').value = '';
    document.getElementById('config-name').value = '';
    document.getElementById('config-base-url').value = '';
    document.getElementById('config-api-key').value = '';
    document.getElementById('config-model-name').value = '';
}

// ========== 可视化生成 ==========

// 生成可视化
async function generateVisualization() {
    if (!currentResultId) {
        showMessage('请先选择一个爬虫结果', 'error');
        return;
    }
    
    // 如果选择API模式但没有选择配置
    if (currentModelType === 'api' && !currentApiConfigId) {
        showMessage('请先配置并选择API', 'error');
        openApiConfigModal();
        return;
    }
    
    showLoading(true);
    
    try {
        const requestBody = {
            result_id: currentResultId,
            analysis_type: 'general',  // 固定使用综合分析
            model_type: currentModelType
        };
        
        // 如果选择的是API模式，添加配置ID
        if (currentModelType === 'api' && currentApiConfigId) {
            requestBody.config_id = currentApiConfigId;
        }
        
        console.log('[DEBUG] 发送请求:', requestBody);
        
        const response = await fetch(`${API_BASE}/visualization/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentVisualizationData = data.visualization;
            displayVisualization(data.visualization);
            // 默认显示全部
            filterCharts('all');
            showMessage('可视化生成成功');
        } else {
            showMessage(data.message || '生成失败', 'error');
        }
    } catch (error) {
        console.error('生成可视化失败:', error);
        showMessage('生成可视化失败', 'error');
    } finally {
        showLoading(false);
    }
}

// 显示可视化
function displayVisualization(vizData) {
    document.getElementById('empty-viz').style.display = 'none';
    document.getElementById('viz-content').style.display = 'block';
    
    const gridEl = document.getElementById('charts-grid');
    gridEl.innerHTML = '';
    
    // 词云
    if (vizData.wordcloud) {
        gridEl.innerHTML += `
            <div class="chart-card wordcloud-card" data-type="wordcloud">
                <h3>关键词词云</h3>
                <img src="${vizData.wordcloud}" alt="词云" class="chart-image">
            </div>
        `;
    }
    
    // 情感分析饼图
    if (vizData.sentiment_pie) {
        gridEl.innerHTML += `
            <div class="chart-card" data-type="charts">
                <h3>情感分析分布</h3>
                <img src="${vizData.sentiment_pie}" alt="情感分析" class="chart-image">
            </div>
        `;
    }
    
    // 分类柱状图
    if (vizData.category_bar) {
        gridEl.innerHTML += `
            <div class="chart-card" data-type="charts">
                <h3>数据分类统计</h3>
                <img src="${vizData.category_bar}" alt="分类统计" class="chart-image">
            </div>
        `;
    }
    
    // 关键词条形图
    if (vizData.keyword_bar) {
        gridEl.innerHTML += `
            <div class="chart-card" data-type="keywords">
                <h3>热门关键词</h3>
                <img src="${vizData.keyword_bar}" alt="关键词" class="chart-image">
            </div>
        `;
    }
    
    // 统计图表
    if (vizData.stats_chart) {
        gridEl.innerHTML += `
            <div class="chart-card" data-type="summary">
                <h3>数据统计概览</h3>
                <img src="${vizData.stats_chart}" alt="统计概览" class="chart-image">
            </div>
        `;
    }
    
    // 时间线
    if (vizData.timeline) {
        gridEl.innerHTML += `
            <div class="chart-card" data-type="summary">
                <h3>数据时间趋势</h3>
                <img src="${vizData.timeline}" alt="时间趋势" class="chart-image">
            </div>
        `;
    }
    
    // 如果没有图表，显示提示
    if (gridEl.innerHTML === '') {
        gridEl.innerHTML = '<p style="color:#999;padding:20px;">暂无可视化数据</p>';
    }
}

// 切换标签
function switchTab(tab) {
    filterCharts(tab);
}

// 筛选图表显示
function filterCharts(tab) {
    // 更新标签样式
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    const activeTab = document.querySelector(`.nav-tab[onclick="switchTab('${tab}')"]`);
    if (activeTab) activeTab.classList.add('active');
    
    // 显示/隐藏图表
    const cards = document.querySelectorAll('.chart-card');
    
    cards.forEach(card => {
        if (tab === 'all') {
            card.style.display = 'block';
        } else if (tab === 'wordcloud') {
            card.style.display = card.dataset.type === 'wordcloud' ? 'block' : 'none';
        } else if (tab === 'charts') {
            // 图表视图：显示除词云外的所有图表（情感分析、分类统计、热门关键词、数据统计概览等）
            card.style.display = (card.dataset.type !== 'wordcloud') ? 'block' : 'none';
        } else if (tab === 'keywords') {
            // 关键词视图：显示热门关键词
            card.style.display = card.dataset.type === 'keywords' ? 'block' : 'none';
        } else if (tab === 'summary') {
            // 摘要视图：显示数据统计概览和时间线
            card.style.display = (card.dataset.type === 'summary') ? 'block' : 'none';
        }
    });
}

// 导出报告
function exportReport() {
    if (!currentVisualizationData) {
        showMessage('请先生成可视化', 'error');
        return;
    }
    
    // 创建报告内容
    let reportContent = `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>爬虫数据可视化报告</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 40px; max-width: 1200px; margin: 0 auto; }
        h1 { color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
        h2 { color: #667eea; margin-top: 30px; }
        .chart { margin: 20px 0; text-align: center; }
        .chart img { max-width: 100%; border: 1px solid #ddd; border-radius: 5px; }
        .meta { color: #666; margin-bottom: 20px; }
        .section { margin-bottom: 40px; }
    </style>
</head>
<body>
    <h1>爬虫数据可视化报告</h1>
    <div class="meta">
        <p>生成时间: ${new Date().toLocaleString()}</p>
        <p>分析类型: ${getAnalysisTypeName(currentAnalysisType)}</p>
        <p>结果ID: ${currentResultId}</p>
    </div>
`;
    
    // 添加各个图表
    if (currentVisualizationData.wordcloud) {
        reportContent += `
    <div class="section">
        <h2>关键词词云</h2>
        <div class="chart"><img src="${currentVisualizationData.wordcloud}"></div>
    </div>
`;
    }
    
    if (currentVisualizationData.sentiment_pie) {
        reportContent += `
    <div class="section">
        <h2>情感分析分布</h2>
        <div class="chart"><img src="${currentVisualizationData.sentiment_pie}"></div>
    </div>
`;
    }
    
    if (currentVisualizationData.category_bar) {
        reportContent += `
    <div class="section">
        <h2>数据分类统计</h2>
        <div class="chart"><img src="${currentVisualizationData.category_bar}"></div>
    </div>
`;
    }
    
    if (currentVisualizationData.keyword_bar) {
        reportContent += `
    <div class="section">
        <h2>热门关键词</h2>
        <div class="chart"><img src="${currentVisualizationData.keyword_bar}"></div>
    </div>
`;
    }
    
    if (currentVisualizationData.stats_chart) {
        reportContent += `
    <div class="section">
        <h2>数据统计概览</h2>
        <div class="chart"><img src="${currentVisualizationData.stats_chart}"></div>
    </div>
`;
    }
    
    if (currentVisualizationData.timeline) {
        reportContent += `
    <div class="section">
        <h2>数据时间趋势</h2>
        <div class="chart"><img src="${currentVisualizationData.timeline}"></div>
    </div>
`;
    }
    
    reportContent += `
</body>
</html>
`;
    
    // 下载报告
    const blob = new Blob([reportContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `可视化报告_${currentResultId}_${Date.now()}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showMessage('报告已导出');
}

// 获取分析类型名称
function getAnalysisTypeName(type) {
    const names = {
        'general': '综合分析',
        'sentiment': '情感分析',
        'keyword': '关键词提取',
        'summary': '内容摘要'
    };
    return names[type] || type;
}

// 显示/隐藏加载
function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (show) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

// ========== 保存可视化 ==========

// 打开保存弹窗
function openSaveVizModal() {
    if (!currentVisualizationData) {
        showMessage('请先生成可视化', 'error');
        return;
    }
    
    // 设置默认名称
    const defaultName = `可视化_${new Date().toISOString().slice(0, 19).replace(/[-:T]/g, '')}`;
    document.getElementById('viz-name-input').value = defaultName;
    
    document.getElementById('save-viz-modal').classList.add('active');
}

// 关闭保存弹窗
function closeSaveVizModal() {
    document.getElementById('save-viz-modal').classList.remove('active');
}

// 保存可视化
async function saveVisualization() {
    if (!currentVisualizationData || !currentResultId) {
        showMessage('没有可保存的可视化数据', 'error');
        return;
    }
    
    const name = document.getElementById('viz-name-input').value.trim();
    if (!name) {
        showMessage('请输入可视化名称', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/visualization/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                result_id: currentResultId,
                name: name,
                visualization_data: currentVisualizationData,
                analysis_type: 'general',
                model_type: currentModelType
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('可视化保存成功');
            closeSaveVizModal();
        } else {
            showMessage(data.message || '保存失败', 'error');
        }
    } catch (error) {
        console.error('保存可视化失败:', error);
        showMessage('保存可视化失败', 'error');
    }
}

// 定期刷新结果列表
setInterval(loadResultList, 30000);
