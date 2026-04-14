const API_BASE = 'http://127.0.0.1:5000/api';

function showTab(tab) {
    console.log('Switching to tab:', tab);
    
    // 切换按钮状态
    const tabBtns = document.querySelectorAll('.tab-btn');
    const formPanels = document.querySelectorAll('.form-panel');
    
    tabBtns.forEach(btn => btn.classList.remove('active'));
    formPanels.forEach(panel => panel.classList.remove('active'));
    
    if (tab === 'login') {
        document.getElementById('login-tab-btn').classList.add('active');
        document.getElementById('login-panel').classList.add('active');
    } else {
        document.getElementById('register-tab-btn').classList.add('active');
        document.getElementById('register-panel').classList.add('active');
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

// 登录表单提交
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;
            
            try {
                const response = await fetch(`${API_BASE}/login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('登录成功！');
                    setTimeout(() => {
                        window.location.href = 'index.html';
                    }, 1000);
                } else {
                    showMessage(data.message || '登录失败', 'error');
                }
            } catch (error) {
                showMessage('网络错误，请稍后重试', 'error');
            }
        });
    }
    
    // 注册表单提交
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('register-username').value;
            const password = document.getElementById('register-password').value;
            const passwordConfirm = document.getElementById('register-password-confirm').value;
            
            if (password !== passwordConfirm) {
                showMessage('两次输入的密码不一致', 'error');
                return;
            }
            
            if (password.length < 6) {
                showMessage('密码长度至少6位', 'error');
                return;
            }
            
            try {
                const response = await fetch(`${API_BASE}/register`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('注册成功！正在跳转...');
                    setTimeout(() => {
                        window.location.href = 'index.html';
                    }, 1000);
                } else {
                    showMessage(data.message || '注册失败', 'error');
                }
            } catch (error) {
                showMessage('网络错误，请稍后重试', 'error');
            }
        });
    }
});
