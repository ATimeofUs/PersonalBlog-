// 页面切换核心逻辑
function router() {
    // 获取当前 hash，默认为 #home
    const hash = window.location.hash || '#home';

    // 1. 隐藏所有页面
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => page.classList.remove('active'));

    // 2. 显示匹配 hash 的页面
    const targetPage = document.querySelector(hash);
    if (targetPage) {
        targetPage.classList.add('active');
    }

    // 3. 自动更新导航链接样式（可选）
    document.querySelectorAll('nav a').forEach(link => {
        link.getAttribute('href') === hash
            ? link.setAttribute('aria-current', 'page')
            : link.removeAttribute('aria-current');
    });
}

// 监听 hash 变化
window.addEventListener('hashchange', router);
// 页面首次加载时运行一次
window.addEventListener('load', router);

// 演示：点击联系我时的加载效果
function showLoading() {
    const loader = document.getElementById('loading-status');
    loader.style.display = 'block';
    setTimeout(() => {
        loader.style.display = 'none';
        alert('功能开发中...');
    }, 1500);
}
