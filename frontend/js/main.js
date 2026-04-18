// AP Learning Web 主JavaScript文件

document.addEventListener('DOMContentLoaded', function() {
    console.log('AP Learning Web 已加载');
    
    // 初始化应用
    initApp();
});

function initApp() {
    // 设置导航栏活动状态
    setupNavigation();
    
    // 加载初始数据
    loadInitialData();
}

function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-links a');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // 移除所有活动状态
            navLinks.forEach(l => l.classList.remove('active'));
            
            // 添加当前活动状态
            this.classList.add('active');
        });
    });
}

function loadInitialData() {
    // 这里可以添加从API加载数据的逻辑
    console.log('正在加载初始数据...');
    
    // 模拟数据加载
    setTimeout(() => {
        console.log('数据加载完成');
    }, 1000);
}

// 工具函数
function formatDate(date) {
    return new Date(date).toLocaleDateString('zh-CN');
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}