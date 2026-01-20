/**
 * Index Page JavaScript
 * Contains functionality specific to the index/home page
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Index page initialized');
    
    // 确保下拉菜单功能在主页正常工作
    setTimeout(function() {
        const userAvatar = document.getElementById('userAvatar');
        const userDropdown = document.getElementById('userDropdown');
        
        if (userAvatar && userDropdown) {
            console.log('Avatar and dropdown found in index page');
            
            // 重新绑定头像点击事件，以保证下拉菜单的正常显示
            userAvatar.addEventListener('click', function(e) {
                console.log('Avatar clicked on index page');
                e.stopPropagation();
                userDropdown.classList.toggle('show');
            });
            
            // 点击其他地方关闭下拉菜单
            document.addEventListener('click', function(e) {
                if (userDropdown.classList.contains('show') && !userDropdown.contains(e.target)) {
                    userDropdown.classList.remove('show');
                }
            });
        }
    }, 100);
}); 