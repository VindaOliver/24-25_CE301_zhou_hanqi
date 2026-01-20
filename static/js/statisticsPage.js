/**
 * Statistics Page JavaScript
 * Handles the statistics page specific functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Statistics page initialized');

    // Tab switching functionality
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });
    
    // Make sure the dropdown functionality works on the statistics page
    const userAvatar = document.getElementById('userAvatar');
    const userDropdown = document.getElementById('userDropdown');
    
    if (userAvatar && userDropdown) {
        console.log('Avatar and dropdown found in statistics page');
        
        // Force these elements to be visible
        userAvatar.style.visibility = 'visible';
        userAvatar.style.opacity = '1';
        
        // Additional click handler for the avatar on the statistics page
        userAvatar.addEventListener('click', function(e) {
            console.log('Avatar clicked on statistics page');
            e.stopPropagation();
            userDropdown.classList.toggle('show');
        });
    }
}); 