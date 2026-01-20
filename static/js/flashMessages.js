/**
 * Flash Messages JavaScript
 * Handles automatic dismissal of flash messages
 */
document.addEventListener('DOMContentLoaded', function() {
    // Auto dismiss flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert-dismissible');
    if (flashMessages.length > 0) {
        flashMessages.forEach(function(message) {
            setTimeout(function() {
                const closeButton = message.querySelector('.btn-close');
                if (closeButton) {
                    closeButton.click();
                } else {
                    message.style.display = 'none';
                }
            }, 5000);
        });
    }
}); 