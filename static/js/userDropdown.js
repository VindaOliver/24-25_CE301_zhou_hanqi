/**
 * User Dropdown Menu Functionality
 * Handles the avatar click and dropdown menu display
 */
document.addEventListener('DOMContentLoaded', function() {
    const userAvatar = document.getElementById('userAvatar');
    const userDropdown = document.getElementById('userDropdown');
    const avatarInput = document.getElementById('avatarInput');
    const avatarPreview = document.getElementById('avatarPreview');
    
    if (userAvatar && userDropdown) {
        // Click avatar to show/hide dropdown menu
        userAvatar.addEventListener('click', function(e) {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
        });
        
        // Click elsewhere to close dropdown menu
        document.addEventListener('click', function(e) {
            if (userDropdown.classList.contains('show') && !userDropdown.contains(e.target)) {
                userDropdown.classList.remove('show');
            }
        });
        
        // Prevent closing when clicking inside dropdown
        userDropdown.addEventListener('click', function(e) {
            e.stopPropagation();
        });
        
        // Avatar preview functionality
        if (avatarInput && avatarPreview) {
            avatarInput.addEventListener('change', function() {
                if (this.files && this.files[0]) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        avatarPreview.src = e.target.result;
                    };
                    reader.readAsDataURL(this.files[0]);
                }
            });
        }
    }
}); 