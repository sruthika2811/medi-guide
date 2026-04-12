document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const previewContainer = document.getElementById('preview-container');
    const previewImage = document.getElementById('preview-image');
    const fileNameText = document.getElementById('file-name');
    const uploadContent = document.querySelector('.upload-content');
    const removeBtn = document.getElementById('remove-file');
    const analyzeBtn = document.getElementById('analyze-btn');

    if (!dropZone) return;

    // Trigger file input on click
    dropZone.addEventListener('click', (e) => {
        if (e.target !== removeBtn && !removeBtn.contains(e.target)) {
            fileInput.click();
        }
    });

    // Handle File Selection
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });

    // Drag and Drop Events
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('dragging');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('dragging');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        handleFiles(dt.files);
    }, false);

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            if (!file.type.match('image.*')) {
                alert('Please upload an image file (JPG or PNG)');
                return;
            }

            const reader = new FileReader();
            reader.onload = (e) => {
                previewImage.src = e.target.result;
                fileNameText.textContent = file.name;
                uploadContent.style.display = 'none';
                previewContainer.style.display = 'block';
                analyzeBtn.disabled = false;
            };
            reader.readAsDataURL(file);
        }
    }

    // Remove File
    removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.value = '';
        previewImage.src = '';
        uploadContent.style.display = 'block';
        previewContainer.style.display = 'none';
        analyzeBtn.disabled = true;
    });

    // Analyze Button Logic
    analyzeBtn.addEventListener('click', () => {
        const spinner = analyzeBtn.querySelector('.spinner-border');
        const btnText = analyzeBtn.querySelector('.btn-text');
        
        if (spinner) spinner.style.display = 'inline-block';
        if (btnText) btnText.style.display = 'none';
        analyzeBtn.disabled = true;

        // Prepare File Data
        const formData = new FormData();
        formData.append('prescription', fileInput.files[0]);
        formData.append('language', document.getElementById('language-select').value);

        // Send to Flask Backend
        fetch('/analyze', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            // If the server responded with a non‑2xx status (e.g., 400 for non‑prescription), parse the error JSON
            if (!response.ok) {
                return response.json().then(err => { throw err; });
            }
            return response.json();
        })
        .then(data => {
            if (spinner) spinner.style.display = 'none';
            if (btnText) btnText.style.display = 'inline-block';
            analyzeBtn.disabled = false;

            // Successful analysis – navigate to results page
            window.location.href = '/results';
        })
        .catch(err => {
            // Handles both network errors and our custom error payload
            if (spinner) spinner.style.display = 'none';
            if (btnText) btnText.style.display = 'inline-block';
            analyzeBtn.disabled = false;
            const message = err.error || 'An error occurred during analysis.';
            alert('Error: ' + message);
        });
    });
});
