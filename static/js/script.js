document.getElementById('fetchBtn').addEventListener('click', async () => {
    const resultEl = document.getElementById('result');

    try {
        // 使用 fetch API 发送 GET 请求到根路径
        const response = await fetch('/', {
            method: 'GET',
            headers: { 'Accept': 'application/json, text/html;q=0.9, */*;q=0.8' },
        });

        // 检查响应状态
        if (!response.ok) {
            throw new Error(`HTTP ${response.status} ${response.statusText}`);
        }

        const contentType = response.headers.get('content-type') || '';

        if (contentType.includes('application/json')) {
            const data = await response.json();
            resultEl.textContent = JSON.stringify(data, null, 2);
        } else {
            const html = await response.text();
            resultEl.textContent = `请求成功（HTML，长度 ${html.length}）`;
        }
    } catch (error) {
        resultEl.textContent = '请求失败：' + (error?.message || String(error));
    }
});