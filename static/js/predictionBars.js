/**
 * Prediction Bars Animation JavaScript
 * Handles animated display of prediction result bars
 */
document.addEventListener('DOMContentLoaded', function() {
    // Animate prediction bars with a small delay
    setTimeout(function() {
        const predictionBars = document.querySelectorAll('.prediction-bar');
        
        predictionBars.forEach(function(bar) {
            // Get the current width style
            const targetWidth = bar.style.width || '0%';
            
            // Set initial width to 0
            bar.style.width = '0%';
            
            // Trigger animation by setting the target width after a small delay
            setTimeout(function() {
                bar.style.width = targetWidth;
            }, 100);
        });
    }, 300);
}); 