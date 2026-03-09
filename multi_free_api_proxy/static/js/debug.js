// 从服务器获取的默认配置
const DEFAULT_MAX_TOKENS = 2000;
const DEFAULT_TEMPERATURE = 0.7;

// 自动刷新相关变量
let autoRefreshTimer = null;
let autoRefreshEnabled = false;
let refreshInterval = 30;

function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    document.getElementById(tabName + '-tab').classList.add('active');
    event.target.classList.add('active');
}

function refreshStats() {
    Promise.all([
        fetch('/debug/stats').then(r => r.json()),
        fetch('/debug/concurrency').then(r => r.json())
    ])
        .then(([statsData, concurrencyData]) => {
            document.getElementById('totalCount').textContent = statsData.total || 0;
            document.getElementById('successCount').textContent = statsData.success || 0;
            document.getElementById('failedCount').textContent = statsData.failed || 0;
            document.getElementById('timeoutCount').textContent = statsData.timeout || 0;
            document.getElementById('retryCount').textContent = statsData.retry || 0;
            document.getElementById('date').textContent = statsData.date || '-';
            document.getElementById('lastUpdated').textContent = statsData.last_updated ? new Date(statsData.last_updated).toLocaleString() : '-';
            document.getElementById('refreshTime').textContent = '刷新于: ' + new Date().toLocaleTimeString();
            
            const errorStatus = document.getElementById('error-status');
            const lastError = concurrencyData.last_error;
            
            if (lastError && lastError.type && lastError.type !== 'none') {
                errorStatus.style.display = 'block';
                errorStatus.className = 'error-status ' + lastError.type;
                
                const errorTypeNames = {
                    'none': '无错误',
                    'timeout': '⏱️ 超时',
                    'upstream_unreachable': '🔴 上游服务器无法连接',
                    'api_error': '❌ API 错误',
                    'concurrent_limit': '⚠️ 并发限制',
                    'proxy_error': '🔗 代理错误',
                    'unknown': '❓ 未知错误'
                };
                
                document.getElementById('errorType').textContent = errorTypeNames[lastError.type] || lastError.type;
                document.getElementById('errorMessage').textContent = lastError.message || '-';
                document.getElementById('errorTime').textContent = lastError.timestamp ? new Date(lastError.timestamp).toLocaleString() : '-';
            } else {
                errorStatus.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('totalCount').textContent = '错误';
        });
}

function refreshApis() {
    fetch('/debug/apis')
        .then(r => r.json())
        .then(data => {
            const apiListDiv = document.getElementById('apiList');
            apiListDiv.innerHTML = '';
            
            const apis = data.free_apis || {};
            const availableApis = data.available_apis || [];
            
            for (const [name, config] of Object.entries(apis)) {
                const isAvailable = availableApis.includes(name);
                const div = document.createElement('div');
                div.className = 'api-status ' + (isAvailable ? 'available' : 'unavailable');
                div.innerHTML = `
                    <strong>${name}</strong>
                    <span style="float: right;">${isAvailable ? '✅ 可用' : '❌ 不可用'}</span>
                    <br><small>模型: ${config.model || 'gpt-3.5-turbo'}</small>
                    <br><small>成功: ${config.success_count || 0} | 失败: ${config.failure_count || 0}</small>
                    ${config.last_test_result ? '<br><small>最后测试: ' + config.last_test_result + '</small>' : ''}
                `;
                apiListDiv.appendChild(div);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('apiList').innerHTML = '<p style="color: red;">获取API状态失败</p>';
        });
}

function addMessage(role, content, latency = null, error = false) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role} ${error ? 'error' : ''}`;
    
    let contentHtml = content.replace(/\n/g, '<br>');
    let metadataHtml = `<div class="time">${new Date().toLocaleString()}</div>`;
    
    if (latency !== null) {
        metadataHtml += `<div class="latency">响应时间: ${latency}ms</div>`;
    }
    
    messageDiv.innerHTML = contentHtml + metadataHtml;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    const sendBtn = document.getElementById('sendBtn');
    const maxTokensInput = document.getElementById('maxTokensInput');
    
    if (!message) return;
    
    addMessage('user', message);
    
    input.value = '';
    sendBtn.disabled = true;
    sendBtn.textContent = '发送中...';
    
    addMessage('assistant', '<span class="loading">AI 正在思考...</span>', null, false);
    
    const startTime = Date.now();
    
    fetch('/v1/chat/completions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            model: 'any-model',
            messages: [
                { role: 'user', content: message }
            ],
            max_tokens: parseInt(maxTokensInput.value) || DEFAULT_MAX_TOKENS,
            temperature: DEFAULT_TEMPERATURE
        })
    })
    .then(response => {
        const endTime = Date.now();
        const latency = endTime - startTime;
        
        const loadingMessages = document.querySelectorAll('.message .loading');
        loadingMessages.forEach(msg => msg.parentElement.remove());
        
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || `HTTP ${response.status}`);
            });
        }
        
        return response.json();
    })
    .then(data => {
        const endTime = Date.now();
        const latency = endTime - startTime;
        
        const content = data.choices?.[0]?.message?.content || '无回复内容';
        addMessage('assistant', content, latency);
    })
    .catch(error => {
        const endTime = Date.now();
        const latency = endTime - startTime;
        
        const loadingMessages = document.querySelectorAll('.message .loading');
        loadingMessages.forEach(msg => msg.parentElement.remove());
        
        addMessage('assistant', `错误: ${error.message}`, latency, true);
    })
    .finally(() => {
        sendBtn.disabled = false;
        sendBtn.textContent = '发送';
    });
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function toggleAutoRefresh() {
    const checkbox = document.getElementById('autoRefreshCheckbox');
    autoRefreshEnabled = checkbox.checked;

    if (autoRefreshEnabled) {
        updateRefreshInterval();
    } else {
        if (autoRefreshTimer) {
            clearInterval(autoRefreshTimer);
            autoRefreshTimer = null;
        }
        document.getElementById('autoRefreshStatus').textContent = '自动刷新: 已关闭';
    }
}

function updateRefreshInterval() {
    const intervalInput = document.getElementById('refreshInterval');
    let newInterval = parseInt(intervalInput.value);

    if (newInterval < 15) newInterval = 15;
    if (newInterval > 120) newInterval = 120;

    refreshInterval = newInterval;
    intervalInput.value = newInterval;

    if (autoRefreshEnabled) {
        if (autoRefreshTimer) {
            clearInterval(autoRefreshTimer);
        }

        autoRefreshTimer = setInterval(refreshStats, refreshInterval * 1000);
        document.getElementById('autoRefreshStatus').textContent = `自动刷新: 已启用 (${refreshInterval}秒)`;
    }
}

function refreshManage() {
    fetch('/debug/api/weight')
        .then(r => r.json())
        .then(data => {
            const tbody = document.getElementById('manageTableBody');
            tbody.innerHTML = '';
            
            const details = data.api_details || {};
            const weights = data.api_weights || {};
            
            for (const [apiName, info] of Object.entries(details)) {
                const tr = document.createElement('tr');
                const isEnabled = info.enabled;
                const weight = info.weight;
                
                tr.innerHTML = `
                    <td><strong>${apiName}</strong></td>
                    <td><small>${details[apiName]?.weight !== undefined ? 'N/A' : 'N/A'}</small></td>
                    <td><span class="status-badge ${isEnabled ? 'enabled' : 'disabled'}">${isEnabled ? '已启用' : '已停用'}</span></td>
                    <td>
                        <input type="number" class="weight-input" id="weight_${apiName}" value="${weight}" min="0" max="999">
                        <button class="btn-save-weight" onclick="saveWeight('${apiName}')">保存</button>
                    </td>
                    <td>
                        ${isEnabled 
                            ? `<button class="btn-disable" onclick="disableApi('${apiName}')">停用</button>`
                            : `<button class="btn-enable" onclick="enableApi('${apiName}')">启用</button>`
                        }
                    </td>
                `;
                tbody.appendChild(tr);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('manageTableBody').innerHTML = '<tr><td colspan="5" style="color: red;">加载失败</td></tr>';
        });
}

function saveWeight(apiName) {
    const weightInput = document.getElementById('weight_' + apiName);
    const weight = parseInt(weightInput.value);
    
    if (isNaN(weight) || weight < 0) {
        alert('权重必须 >= 0');
        return;
    }
    
    fetch('/debug/api/weight', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({api_name: apiName, weight: weight})
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const weightMsg = weight > 100 ? ` (特别权重: 下次请求必然选中)` : '';
            alert('权重已更新' + weightMsg);
            refreshManage();
        } else {
            alert('更新失败: ' + (data.error || '未知错误'));
        }
    })
    .catch(error => {
        alert('请求失败: ' + error);
    });
}

function enableApi(apiName) {
    fetch('/debug/api/enable', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({api_name: apiName})
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            alert('API 已启用');
            refreshManage();
        } else {
            alert('启用失败: ' + (data.error || '未知错误'));
        }
    })
    .catch(error => {
        alert('请求失败: ' + error);
    });
}

function disableApi(apiName) {
    fetch('/debug/api/disable', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({api_name: apiName})
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            alert('API 已停用');
            refreshManage();
        } else {
            alert('停用失败: ' + (data.error || '未知错误'));
        }
    })
    .catch(error => {
        alert('请求失败: ' + error);
    });
}

function resetWeights() {
    if (!confirm('确定要重置所有权重为默认值吗？')) {
        return;
    }
    
    fetch('/debug/api/weight/reset', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            alert('权重已重置');
            refreshManage();
        } else {
            alert('重置失败: ' + (data.error || '未知错误'));
        }
    })
    .catch(error => {
        alert('请求失败: ' + error);
    });
}

function saveModel(apiName) {
    const select = document.getElementById('model_' + apiName);
    if (!select) {
        alert('找不到模型选择器');
        return;
    }
    const value = select.value;
    
    if (!value) {
        alert('请选择一个模型');
        return;
    }
    
    const useWeighted = value === '__weighted__';
    const model = useWeighted ? null : value;
    
    fetch('/debug/api/model', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            api_name: apiName, 
            model: model,
            use_weighted: useWeighted
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            alert('模型已更新: ' + data.message);
            refreshManage();
        } else {
            alert('更新失败: ' + (data.error || '未知错误'));
        }
    })
    .catch(error => {
        alert('请求失败: ' + error);
    });
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    refreshStats();
    refreshApis();
    refreshManage();
    
    // 初始化聊天界面
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.innerHTML = '<div class="message assistant">欢迎使用多Free API聊天测试！您可以在这里直接测试代理功能。</div>';
    }
});
