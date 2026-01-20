/**
 * Main JavaScript file for Cat Breed Recognition app
 * Contains common functions and utilities
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap components if needed
    if (typeof bootstrap !== 'undefined') {
        // Enable tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Enable popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
    
    // Hide elements with .hidden class
    document.querySelectorAll('.hidden').forEach(function(el) {
        el.style.display = 'none';
    });
    
    console.log('Main JS initialized');
}); 