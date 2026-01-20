/**
 * File Upload JavaScript
 * Handles file selection, preview, and upload for image recognition
 */
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.getElementById('uploadArea');
    const imagePreview = document.getElementById('imagePreview');
    const retryButton = document.getElementById('retryButton');
    const loadingSpinner = document.querySelector('.loading-spinner');
    const resultsContainer = document.querySelector('.results-container');
    const predictionsContainer = document.getElementById('predictions');
    const breedInfoContainer = document.getElementById('breedInfo');
    
    if (!fileInput || !uploadArea) return;
    
    // Handle file selection via button
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Handle drag and drop
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', function() {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            fileInput.files = e.dataTransfer.files;
            handleFileChange();
        }
    });
    
    // Handle file selection change
    fileInput.addEventListener('change', handleFileChange);
    
    function handleFileChange() {
        if (fileInput.files && fileInput.files[0]) {
            // Show preview
            const reader = new FileReader();
            
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                imagePreview.style.display = 'block';
                retryButton.style.display = 'inline-block';
                uploadArea.style.display = 'none';
                
                // Show loading spinner
                loadingSpinner.style.display = 'block';
                
                // Submit the image for recognition
                submitImage(fileInput.files[0]);
            };
            
            reader.readAsDataURL(fileInput.files[0]);
        }
    }
    
    // Handle retry button
    if (retryButton) {
        retryButton.addEventListener('click', function() {
            // Reset the form
            imagePreview.style.display = 'none';
            retryButton.style.display = 'none';
            uploadArea.style.display = 'block';
            loadingSpinner.style.display = 'none';
            resultsContainer.style.display = 'none';
            predictionsContainer.innerHTML = '';
            breedInfoContainer.innerHTML = '';
            fileInput.value = '';
        });
    }
    
    // Function to submit image for recognition
    function submitImage(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        fetch('/predict', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading spinner
            loadingSpinner.style.display = 'none';
            
            // Show results
            resultsContainer.style.display = 'block';
            
            // Display predictions
            if (data.predictions && data.predictions.length > 0) {
                let predictionsHTML = '';
                
                data.predictions.forEach(function(prediction) {
                    predictionsHTML += `
                        <div class="prediction-item">
                            <span>${prediction.breed}</span>
                            <div class="prediction-bar-container">
                                <div class="prediction-bar" data-width="${prediction.probability}"></div>
                            </div>
                            <span class="prediction-value">${prediction.probability.toFixed(1)}%</span>
                        </div>
                    `;
                });
                
                predictionsContainer.innerHTML = predictionsHTML;
                
                // Animate prediction bars
                setTimeout(function() {
                    const predictionBars = document.querySelectorAll('.results-container .prediction-bar');
                    predictionBars.forEach(function(bar) {
                        const width = bar.getAttribute('data-width') + '%';
                        setTimeout(function() {
                            bar.style.width = width;
                        }, 100);
                    });
                }, 200);
                
                // Display breed info
                if (data.breed_info) {
                    let breedHTML = `
                        <h3>${data.predictions[0].breed} Information</h3>
                    `;
                    
                    if (data.breed_info.description) {
                        breedHTML += `<p>${data.breed_info.description}</p>`;
                    }
                    
                    if (data.breed_info.characteristics) {
                        breedHTML += `
                            <div class="breed-section">
                                <h4>Characteristics</h4>
                                <ul class="breed-details-list">
                        `;
                        
                        const characteristics = data.breed_info.characteristics;
                        if (characteristics.size) breedHTML += `<li><strong>Size:</strong> ${characteristics.size}</li>`;
                        if (characteristics.coat) breedHTML += `<li><strong>Coat:</strong> ${characteristics.coat}</li>`;
                        if (characteristics.color) breedHTML += `<li><strong>Color:</strong> ${characteristics.color}</li>`;
                        if (characteristics.lifespan) breedHTML += `<li><strong>Lifespan:</strong> ${characteristics.lifespan}</li>`;
                        if (characteristics.origin) breedHTML += `<li><strong>Origin:</strong> ${characteristics.origin}</li>`;
                        
                        breedHTML += `
                                </ul>
                            </div>
                        `;
                    }
                    
                    if (data.breed_info.personality && data.breed_info.personality.length > 0) {
                        breedHTML += `
                            <div class="breed-section">
                                <h4>Personality</h4>
                                <div class="personality-tags">
                        `;
                        
                        data.breed_info.personality.forEach(function(trait) {
                            breedHTML += `<span class="personality-tag">${trait}</span>`;
                        });
                        
                        breedHTML += `
                                </div>
                            </div>
                        `;
                    }
                    
                    breedInfoContainer.innerHTML = breedHTML;
                }
            } else {
                predictionsContainer.innerHTML = '<p>Unable to determine the cat breed. Please try with a clearer image.</p>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            loadingSpinner.style.display = 'none';
            predictionsContainer.innerHTML = '<p>An error occurred during recognition. Please try again.</p>';
        });
    }
}); 