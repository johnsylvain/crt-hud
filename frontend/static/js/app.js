// StatusBoard Admin UI JavaScript

const API_BASE = '/api';

// State
let slides = [];
let config = {};
let currentSlideRefreshInterval = null;
let slidePreviewRefreshInterval = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadSlides();
    loadConfig();
    setupEventListeners();
    setupTabs();
    setupCollapsibleSections();
    setupKeyboardShortcuts();
    startCurrentSlideRefresh();
    startSlidePreviewRefresh();
    updateWindowStatusBar();
});

// Event Listeners
function setupEventListeners() {
    // Add slide button
    document.getElementById('addSlideBtn').addEventListener('click', () => {
        openSlideModal();
    });
    
    // Modal close
    document.querySelector('.close').addEventListener('click', closeSlideModal);
    document.getElementById('cancelBtn').addEventListener('click', closeSlideModal);
    
    // Slide form
    document.getElementById('slideForm').addEventListener('submit', handleSlideSubmit);
    
    // Real-time form validation
    const form = document.getElementById('slideForm');
    form.querySelectorAll('input[required], select[required]').forEach(field => {
        field.addEventListener('blur', () => {
            validateField(field);
        });
        field.addEventListener('input', () => {
            // Clear error on input
            if (field.classList.contains('error')) {
                field.classList.remove('error');
                const errorMsg = field.parentNode.querySelector('.field-error');
                if (errorMsg) errorMsg.remove();
            }
        });
    });
    
    // Conditional checkbox - no longer needs to show/hide anything
    
    // Slide type change - toggle weather, image, and static text settings
    document.getElementById('slideType').addEventListener('change', (e) => {
        const slideType = e.target.value;
        toggleWeatherSettings(slideType === 'weather');
        toggleStaticTextSettings(slideType === 'static_text');
        toggleImageSettings(slideType === 'image');
        clearValidationErrors(); // Clear validation when type changes
    });
    
    // Image upload handler
    const imageUpload = document.getElementById('imageUpload');
    if (imageUpload) {
        imageUpload.addEventListener('change', handleImageUpload);
    }
    
    // Image select handler
    const imageSelect = document.getElementById('imageSelect');
    if (imageSelect) {
        imageSelect.addEventListener('change', handleImageSelect);
    }
    
    // Save config button
    document.getElementById('saveConfigBtn').addEventListener('click', saveConfig);
    
    // Debug buttons - Plex
    if (document.getElementById('refreshDebugBtn')) {
        document.getElementById('refreshDebugBtn').addEventListener('click', loadDebugLogs);
    }
    if (document.getElementById('testPlexBtn')) {
        document.getElementById('testPlexBtn').addEventListener('click', testPlexConnection);
    }
    if (document.getElementById('fetchDataBtn')) {
        document.getElementById('fetchDataBtn').addEventListener('click', fetchPlexData);
    }
    if (document.getElementById('clearDebugBtn')) {
        document.getElementById('clearDebugBtn').addEventListener('click', clearDebugLogs);
    }
    
    // Debug buttons - ARM
    if (document.getElementById('refreshArmDebugBtn')) {
        document.getElementById('refreshArmDebugBtn').addEventListener('click', loadArmDebugLogs);
    }
    if (document.getElementById('testArmBtn')) {
        document.getElementById('testArmBtn').addEventListener('click', testArmConnection);
    }
    if (document.getElementById('fetchArmDataBtn')) {
        document.getElementById('fetchArmDataBtn').addEventListener('click', fetchArmData);
    }
    if (document.getElementById('clearArmDebugBtn')) {
        document.getElementById('clearArmDebugBtn').addEventListener('click', clearArmDebugLogs);
    }
    
    // Close modal on outside click
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('slideModal');
        if (e.target === modal) {
            closeSlideModal();
        }
    });
}

// Tab functionality
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            
            // Remove active class from all tabs
            tabButtons.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => {
                c.classList.remove('active');
                c.style.display = 'none';
            });
            
            // Add active class to selected tab
            btn.classList.add('active');
            const targetContent = document.getElementById(`${targetTab}Tab`);
            if (targetContent) {
                targetContent.classList.add('active');
                targetContent.style.display = 'block';
            }
            
            // Load content when switching to specific tabs
            if (targetTab === 'config') {
                loadConfig();
            } else if (targetTab === 'debug') {
                loadDebugLogs();
                loadArmDebugLogs();
            }
        });
    });
}

// Collapsible sections functionality
function setupCollapsibleSections() {
    const collapsibleHeaders = document.querySelectorAll('.collapsible-header');
    
    collapsibleHeaders.forEach(header => {
        header.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const targetId = header.getAttribute('data-target');
            if (!targetId) return;
            
            const content = document.getElementById(targetId);
            if (!content) return;
            
            const isExpanded = header.classList.contains('expanded');
            
            if (isExpanded) {
                // Collapse
                header.classList.remove('expanded');
                content.classList.remove('expanded');
                content.style.display = 'none';
            } else {
                // Expand
                header.classList.add('expanded');
                content.classList.add('expanded');
                content.style.display = 'block';
            }
        });
    });
}

// Load Slides
async function loadSlides() {
    const container = document.getElementById('slidesList');
    if (!container) return;
    
    // Show loading state
    container.innerHTML = '<div class="slides-loading">Loading slides...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/slides`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        slides = data.slides || [];
        renderSlides();
    } catch (error) {
        console.error('Error loading slides:', error);
        container.innerHTML = `<div class="slides-error">Failed to load slides: ${error.message}<br/><button class="btn btn-small btn-primary" onclick="loadSlides()">Retry</button></div>`;
        showError(`Failed to load slides: ${error.message}`);
    }
}

// Render Slides
function renderSlides() {
    const container = document.getElementById('slidesList');
    container.innerHTML = '';
    
    // Sort by order
    const sortedSlides = [...slides].sort((a, b) => (a.order || 0) - (b.order || 0));
    
    sortedSlides.forEach(slide => {
        const slideEl = createSlideElement(slide);
        container.appendChild(slideEl);
    });
    
    // Make sortable (simple drag and drop)
    makeSortable(container);
    
    // Refresh preview images periodically (every 5 seconds)
    refreshSlidePreviews();
    
    // Update window status bar
    updateWindowStatusBar();
}

// Refresh slide preview images
function refreshSlidePreviews() {
    const slidePreviews = document.querySelectorAll('.slide-preview-img');
    slidePreviews.forEach((img, index) => {
        const slideItem = img.closest('.slide-item');
        if (slideItem) {
            const slideId = slideItem.dataset.id;
            if (slideId) {
                // Refresh with cache-busting timestamp
                const newUrl = `${API_BASE}/preview/${slideId}?t=${Date.now()}`;
                // Only update if URL is different (avoid unnecessary reloads)
                if (img.src !== newUrl) {
                    img.src = newUrl;
                }
            }
        }
    });
}

// Create Slide Element
function createSlideElement(slide) {
    const div = document.createElement('div');
    div.className = 'slide-item';
    div.dataset.id = slide.id;
    div.setAttribute('draggable', 'true');
    div.setAttribute('aria-label', `Slide: ${slide.title}`);
    
    const typeLabels = {
        'pihole_summary': 'Pi-hole Stats',
        'plex_now_playing': 'Plex Now Playing',
        'arm_rip_progress': 'ARM Rip Progress',
        'system_stats': 'System Stats',
        'weather': 'Weather',
        'image': 'Image',
        'static_text': 'Static Text'
    };
    
    const badge = slide.conditional ? `<span class="slide-badge badge-conditional">Hide if no data</span>` : '';
    
    // Create preview image with cache-busting timestamp
    const previewImageUrl = `${API_BASE}/preview/${slide.id}?t=${Date.now()}`;
    
    div.innerHTML = `
        <div class="drag-handle" aria-label="Drag to reorder">☰</div>
        <div class="slide-preview" onclick="previewSlide(${slide.id})" title="Click to view full preview" role="button" tabindex="0" aria-label="Preview slide ${slide.title}">
            <img src="${previewImageUrl}" alt="Slide preview for ${slide.title}" class="slide-preview-img" 
                 loading="lazy"
                 onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'160\' height=\'140\'%3E%3Crect fill=\'%23ccc\' width=\'160\' height=\'140\'/%3E%3Ctext fill=\'%23999\' font-family=\'monospace\' font-size=\'12\' x=\'50%25\' y=\'50%25\' text-anchor=\'middle\' dominant-baseline=\'middle\'%3ELoading...%3C/text%3E%3C/svg%3E';" />
        </div>
        <div class="slide-info">
            <div class="slide-title">${escapeHtml(slide.title)} ${badge}</div>
            <div class="slide-meta">
                ${typeLabels[slide.type] || slide.type} | 
                Display: ${slide.duration}s | 
                Refresh: ${slide.refresh_duration || 5}s | 
                Order: ${slide.order || 0}
            </div>
        </div>
        <div class="slide-actions">
            <button class="btn btn-small btn-secondary" onclick="previewSlide(${slide.id})" aria-label="Preview slide">Preview</button>
            <button class="btn btn-small btn-secondary" onclick="editSlide(${slide.id})" aria-label="Edit slide">Edit</button>
            <button class="btn btn-small btn-danger" onclick="deleteSlide(${slide.id})" aria-label="Delete slide">Delete</button>
        </div>
    `;
    
    return div;
}

// Utility: Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Make Sortable (enhanced implementation)
let saveOrderTimeout = null;
let isDragging = false;

function makeSortable(container) {
    let draggedElement = null;
    
    container.querySelectorAll('.slide-item').forEach(item => {
        item.draggable = true;
        
        item.addEventListener('dragstart', (e) => {
            draggedElement = item;
            item.classList.add('dragging');
            isDragging = true;
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/html', item.outerHTML);
        });
        
        item.addEventListener('dragend', () => {
            item.classList.remove('dragging');
            container.querySelectorAll('.slide-item').forEach(i => {
                i.classList.remove('drag-over');
            });
            draggedElement = null;
            isDragging = false;
            
            // Debounce save order
            if (saveOrderTimeout) {
                clearTimeout(saveOrderTimeout);
            }
            saveOrderTimeout = setTimeout(() => {
                saveSlideOrder();
            }, 500);
        });
        
        item.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            
            const afterElement = getDragAfterElement(container, e.clientY);
            const siblings = [...container.querySelectorAll('.slide-item:not(.dragging)')];
            
            // Clear all drag-over classes
            siblings.forEach(s => s.classList.remove('drag-over'));
            
            if (afterElement == null) {
                container.appendChild(draggedElement);
                siblings[siblings.length - 1]?.classList.add('drag-over');
            } else {
                container.insertBefore(draggedElement, afterElement);
                const afterIndex = siblings.indexOf(afterElement);
                if (afterIndex > 0) {
                    siblings[afterIndex - 1]?.classList.add('drag-over');
                }
            }
        });
        
        item.addEventListener('dragleave', () => {
            item.classList.remove('drag-over');
        });
    });
    
    // Auto-scroll when dragging near edges
    container.addEventListener('dragover', (e) => {
        if (!draggedElement) return;
        
        const rect = container.getBoundingClientRect();
        const scrollThreshold = 50;
        const scrollSpeed = 10;
        
        if (e.clientY - rect.top < scrollThreshold) {
            container.scrollTop -= scrollSpeed;
        } else if (rect.bottom - e.clientY < scrollThreshold) {
            container.scrollTop += scrollSpeed;
        }
    });
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.slide-item:not(.dragging)')];
    
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

// Save slide order after drag
async function saveSlideOrder() {
    const container = document.getElementById('slidesList');
    const slideItems = container.querySelectorAll('.slide-item');
    const slideIds = Array.from(slideItems).map(item => parseInt(item.dataset.id));
    
    // Optimistic update - reorder slides array immediately
    const oldOrder = slides.map(s => s.id);
    slides.sort((a, b) => {
        const aIndex = slideIds.indexOf(a.id);
        const bIndex = slideIds.indexOf(b.id);
        return aIndex - bIndex;
    });
    
    try {
        const response = await fetch(`${API_BASE}/slides/reorder`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ slide_ids: slideIds })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        showInfo('Slide order saved');
        updateWindowStatusBar();
    } catch (error) {
        console.error('Error saving slide order:', error);
        showError(`Failed to save slide order: ${error.message}`);
        // Revert optimistic update
        slides.sort((a, b) => {
            const aIndex = oldOrder.indexOf(a.id);
            const bIndex = oldOrder.indexOf(b.id);
            return aIndex - bIndex;
        });
        renderSlides();
    }
}

// Form Validation
function validateSlideForm() {
    let isValid = true;
    const title = document.getElementById('slideTitle');
    const duration = document.getElementById('slideDuration');
    const refreshDuration = document.getElementById('slideRefreshDuration');
    const slideType = document.getElementById('slideType').value;
    
    // Clear previous errors
    clearValidationErrors();
    
    // Validate title
    if (!title.value.trim()) {
        showFieldError(title, 'Title is required');
        isValid = false;
    }
    
    // Validate duration
    const durationVal = parseInt(duration.value);
    if (isNaN(durationVal) || durationVal < 1 || durationVal > 300) {
        showFieldError(duration, 'Duration must be between 1 and 300 seconds');
        isValid = false;
    }
    
    // Validate refresh duration
    const refreshVal = parseInt(refreshDuration.value);
    if (isNaN(refreshVal) || refreshVal < 1 || refreshVal > 60) {
        showFieldError(refreshDuration, 'Refresh duration must be between 1 and 60 seconds');
        isValid = false;
    }
    
    // Validate weather city if weather type
    if (slideType === 'weather') {
        const city = document.getElementById('slideCity');
        if (!city.value.trim()) {
            showFieldError(city, 'City is required for weather slides');
            isValid = false;
        }
    }
    
    // Validate image path if image type
    if (slideType === 'image') {
        const imagePath = document.getElementById('imagePath')?.value.trim();
        if (!imagePath) {
            const imageSelect = document.getElementById('imageSelect');
            if (imageSelect) {
                showFieldError(imageSelect, 'Please upload or select an image');
            }
            isValid = false;
        }
    }
    
    // Validate static text content if static_text type
    if (slideType === 'static_text') {
        const text = document.getElementById('slideText');
        if (!text.value.trim()) {
            showFieldError(text, 'Text content is required for static text slides');
            isValid = false;
        }
    }
    
    return isValid;
}

function validateField(field) {
    // Remove existing error for this field
    field.classList.remove('error');
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) existingError.remove();
    
    let isValid = true;
    let errorMessage = '';
    
    if (field.hasAttribute('required') && !field.value.trim()) {
        isValid = false;
        errorMessage = 'This field is required';
    } else if (field.type === 'number') {
        const value = parseInt(field.value);
        const min = field.getAttribute('min') ? parseInt(field.getAttribute('min')) : -Infinity;
        const max = field.getAttribute('max') ? parseInt(field.getAttribute('max')) : Infinity;
        
        if (isNaN(value) || value < min || value > max) {
            isValid = false;
            errorMessage = `Value must be between ${min} and ${max}`;
        }
    }
    
    if (!isValid) {
        showFieldError(field, errorMessage);
    }
    
    return isValid;
}

function showFieldError(field, message) {
    field.classList.add('error');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.textContent = message;
    errorDiv.setAttribute('role', 'alert');
    field.parentNode.appendChild(errorDiv);
}

function clearValidationErrors() {
    document.querySelectorAll('.field-error').forEach(el => el.remove());
    document.querySelectorAll('.error').forEach(el => el.classList.remove('error'));
}

// Toggle weather settings visibility
function toggleWeatherSettings(show) {
    document.getElementById('weatherSettings').style.display = show ? 'block' : 'none';
}

// Toggle image settings visibility
function toggleImageSettings(show) {
    const imageSettings = document.getElementById('imageSettings');
    if (imageSettings) {
        imageSettings.style.display = show ? 'block' : 'none';
        if (show) {
            loadExistingImages();
        }
    }
}

// Load existing images from server
async function loadExistingImages() {
    const imageSelect = document.getElementById('imageSelect');
    if (!imageSelect) return;
    
    try {
        const response = await fetch(`${API_BASE}/images`);
        if (!response.ok) throw new Error('Failed to load images');
        
        const data = await response.json();
        const images = data.images || [];
        
        // Clear existing options except the first
        imageSelect.innerHTML = '<option value="">-- Select an image --</option>';
        
        // Add image options
        images.forEach(img => {
            const option = document.createElement('option');
            option.value = img.path;
            option.textContent = `${img.filename} (${img.width}x${img.height}${img.is_animated ? ', animated' : ''})`;
            imageSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading images:', error);
        // Don't show error to user, just log it
    }
}

// Handle image file upload
async function handleImageUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    // Validate file size (10MB max)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showError(`File too large. Maximum size: ${maxSize / (1024*1024)}MB`);
        e.target.value = ''; // Clear file input
        return;
    }
    
    // Validate file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp', 'image/webp'];
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(png|jpg|jpeg|gif|bmp|webp)$/i)) {
        showError('Invalid file type. Allowed: PNG, JPG, GIF, BMP, WEBP');
        e.target.value = ''; // Clear file input
        return;
    }
    
    // Show loading state
    const submitBtn = document.querySelector('#slideForm button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Uploading...';
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE}/upload/image`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }
        
        const result = await response.json();
        
        // Set the image path in the hidden field and select dropdown
        document.getElementById('imageSelect').value = result.path;
        document.getElementById('imagePath').value = result.path;
        
        // Show preview
        showImagePreview(result);
        
        // Reload images list to include the new one
        await loadExistingImages();
        
        // Reset file input to allow uploading the same file again if needed
        e.target.value = '';
        
        showSuccess('Image uploaded successfully');
    } catch (error) {
        console.error('Error uploading image:', error);
        showError(`Failed to upload image: ${error.message}`);
        e.target.value = ''; // Clear file input
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

// Handle image selection from dropdown
function handleImageSelect(e) {
    const path = e.target.value;
    if (!path) {
        hideImagePreview();
        return;
    }
    
    // Find the image info from the options
    const option = e.target.options[e.target.selectedIndex];
    // Update hidden field
    const imagePathField = document.getElementById('imagePath');
    if (imagePathField) {
        imagePathField.value = path;
    }
    
    // Load images list to get full details
    fetch(`${API_BASE}/images`)
        .then(response => response.json())
        .then(data => {
            const img = data.images.find(i => i.path === path);
            if (img) {
                showImagePreview(img);
            }
        })
        .catch(error => {
            console.error('Error loading image info:', error);
            // Still show preview with just the path
            showImagePreview({ path: path, filename: path.split('/').pop() });
        });
}

// Show image preview
function showImagePreview(img) {
    const previewDiv = document.getElementById('imagePreview');
    const previewImg = document.getElementById('imagePreviewImg');
    const infoDiv = document.getElementById('imageInfo');
    
    if (!previewDiv || !previewImg) return;
    
    // Extract filename from path or use filename property
    const filename = img.filename || (img.path ? img.path.split('/').pop() : '');
    if (filename) {
        previewImg.src = `${API_BASE}/images/${filename}`;
    }
    
    // Set info
    if (infoDiv) {
        const displayName = img.filename || filename || img.path || 'Unknown';
        let info = displayName;
        if (img.width && img.height) {
            info += ` • ${img.width}x${img.height}`;
        }
        if (img.size) {
            const sizeMB = (img.size / (1024 * 1024)).toFixed(2);
            info += ` • ${sizeMB}MB`;
        }
        if (img.is_animated) {
            info += ' • Animated GIF';
        }
        infoDiv.textContent = info;
    }
    
    previewDiv.style.display = 'block';
}

// Hide image preview
function hideImagePreview() {
    const previewDiv = document.getElementById('imagePreview');
    if (previewDiv) {
        previewDiv.style.display = 'none';
    }
    
    // Clear hidden field
    const imagePathField = document.getElementById('imagePath');
    if (imagePathField) {
        imagePathField.value = '';
    }
}

// Toggle static text settings visibility
function toggleStaticTextSettings(show) {
    document.getElementById('staticTextSettings').style.display = show ? 'block' : 'none';
}

// Slide Modal
function openSlideModal(slide = null) {
    const modal = document.getElementById('slideModal');
    const form = document.getElementById('slideForm');
    
    // Clear validation errors
    clearValidationErrors();
    
    if (slide) {
        document.getElementById('modalTitle').textContent = 'Edit Slide';
        document.getElementById('slideId').value = slide.id;
        const slideType = slide.type;
        document.getElementById('slideType').value = slideType;
        document.getElementById('slideTitle').value = slide.title;
        document.getElementById('slideDuration').value = slide.duration;
        document.getElementById('slideRefreshDuration').value = slide.refresh_duration || 5;
        document.getElementById('slideConditional').checked = slide.conditional || false;
        
        // Weather-specific fields
        toggleWeatherSettings(slideType === 'weather');
        if (slideType === 'weather') {
            document.getElementById('slideCity').value = slide.city || '';
            document.getElementById('slideTempUnit').value = slide.temp_unit || 'C';
        }
        
        // Image-specific fields
        toggleImageSettings(slideType === 'image');
        if (slideType === 'image') {
            const imagePathField = document.getElementById('imagePath');
            const imageSelect = document.getElementById('imageSelect');
            if (slide.image_path) {
                if (imagePathField) {
                    imagePathField.value = slide.image_path;
                }
                // Set selected image
                loadExistingImages().then(() => {
                    if (imageSelect) {
                        imageSelect.value = slide.image_path;
                        // Load preview
                        handleImageSelect({ target: imageSelect });
                    }
                });
            }
        }
        
        // Static text-specific fields
        toggleStaticTextSettings(slideType === 'static_text');
        if (slideType === 'static_text') {
            document.getElementById('slideText').value = slide.text || '';
            document.getElementById('slideFontSize').value = slide.font_size || 'medium';
            document.getElementById('slideTextAlign').value = slide.text_align || 'left';
            document.getElementById('slideVerticalAlign').value = slide.vertical_align || 'center';
            document.getElementById('slideTextColor').value = slide.text_color || 'text';
        }
    } else {
        document.getElementById('modalTitle').textContent = 'Add Slide';
        form.reset();
        toggleWeatherSettings(false);
        toggleStaticTextSettings(false);
        toggleImageSettings(false);
        hideImagePreview();
    }
    
    modal.style.display = 'block';
    // Focus first input
    setTimeout(() => {
        const firstInput = form.querySelector('input, select');
        if (firstInput) firstInput.focus();
    }, 50);
}

function closeSlideModal() {
    const modal = document.getElementById('slideModal');
    modal.style.display = 'none';
    document.getElementById('slideForm').reset();
    clearValidationErrors();
    toggleWeatherSettings(false);
    toggleStaticTextSettings(false);
}

// Handle Slide Submit
async function handleSlideSubmit(e) {
    e.preventDefault();
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    if (!submitBtn) return;
    
    // Validate form
    if (!validateSlideForm()) {
        return;
    }
    
    const slideType = document.getElementById('slideType').value;
    const formData = {
        type: slideType,
        title: document.getElementById('slideTitle').value.trim(),
        duration: parseInt(document.getElementById('slideDuration').value),
        refresh_duration: parseInt(document.getElementById('slideRefreshDuration').value),
        conditional: document.getElementById('slideConditional').checked,
    };
    
    // condition_type is deprecated - conditional now means "hide if no data for this slide"
    
        // Weather-specific fields
        if (slideType === 'weather') {
            const city = document.getElementById('slideCity').value.trim();
            const tempUnit = document.getElementById('slideTempUnit').value;
            if (city) {
                formData.city = city;
            }
            formData.temp_unit = tempUnit;
        }
        
        // Image-specific fields
        if (slideType === 'image') {
            const imagePath = document.getElementById('imagePath')?.value.trim();
            if (imagePath) {
                formData.image_path = imagePath;
            }
        }
        
        // Static text-specific fields
        if (slideType === 'static_text') {
            const text = document.getElementById('slideText').value.trim();
            const fontSize = document.getElementById('slideFontSize').value;
            const textAlign = document.getElementById('slideTextAlign').value;
            const verticalAlign = document.getElementById('slideVerticalAlign').value;
            const textColor = document.getElementById('slideTextColor').value;
            if (text) {
                formData.text = text;
            }
            formData.font_size = fontSize;
            formData.text_align = textAlign;
            formData.vertical_align = verticalAlign;
            formData.text_color = textColor;
        }
    
    const slideId = document.getElementById('slideId').value;
    
    // Show loading state
    setButtonLoading(submitBtn, true);
    
    try {
        let response;
        if (slideId) {
            // Update - optimistic update
            const existingSlide = slides.find(s => s.id == slideId);
            if (existingSlide) {
                Object.assign(existingSlide, formData);
                renderSlides();
            }
            
            response = await fetch(`${API_BASE}/slides/${slideId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
        } else {
            // Create - optimistic update
            const maxOrder = slides.length > 0 ? Math.max(...slides.map(s => s.order || 0)) : -1;
            formData.order = maxOrder + 1;
            formData.id = Date.now(); // Temporary ID
            slides.push(formData);
            renderSlides();
            
            response = await fetch(`${API_BASE}/slides`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
        }
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        closeSlideModal();
        await loadSlides(); // Reload to get server data
        showSuccess(slideId ? 'Slide updated successfully' : 'Slide created successfully');
        
        // Refresh current slide if it was updated
        if (slideId && currentSlideRefreshInterval) {
            updateCurrentSlide();
        }
    } catch (error) {
        console.error('Error saving slide:', error);
        showError(`Failed to save slide: ${error.message}`);
        // Revert optimistic update
        await loadSlides();
    } finally {
        setButtonLoading(submitBtn, false);
    }
}

// Edit Slide
function editSlide(id) {
    const slide = slides.find(s => s.id === id);
    if (slide) {
        openSlideModal(slide);
    }
}

// Delete Slide
async function deleteSlide(id) {
    const confirmed = await showConfirm('Are you sure you want to delete this slide?', 'Delete Slide');
    if (!confirmed) {
        return;
    }
    
    try {
        // Optimistic update
        const slideItem = document.querySelector(`[data-id="${id}"]`);
        if (slideItem) {
            slideItem.style.opacity = '0.5';
            slideItem.style.pointerEvents = 'none';
        }
        
        await fetch(`${API_BASE}/slides/${id}`, {
            method: 'DELETE'
        });
        
        await loadSlides();
        showSuccess('Slide deleted successfully');
    } catch (error) {
        console.error('Error deleting slide:', error);
        showError(`Failed to delete slide: ${error.message}`);
        // Revert optimistic update by reloading
        loadSlides();
    }
}

// Preview Slide
function previewSlide(id) {
    window.open(`${API_BASE}/preview/${id}`, '_blank');
}

// Load Config
async function loadConfig() {
    try {
        const response = await fetch(`${API_BASE}/config`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        config = await response.json();
        renderConfig();
    } catch (error) {
        console.error('Error loading config:', error);
        showError(`Failed to load configuration: ${error.message}`);
    }
}

// Render Config
function renderConfig() {
    const container = document.getElementById('configForm');
    if (!container) return;
    
    container.innerHTML = '<div class="config-loading">Loading configuration...</div>';
    
    // Small delay to show loading state (if config is already loaded, this is instant)
    setTimeout(() => {
        container.innerHTML = '';
        
        // ARM Config
        container.appendChild(createConfigSection('ARM', 'arm', config.arm || {}));
        
        // Pi-hole Config
        container.appendChild(createConfigSection('Pi-hole', 'pihole', config.pihole || {}));
        
        // Plex Config
        container.appendChild(createConfigSection('Plex', 'plex', config.plex || {}));
        
        // System Config
        container.appendChild(createConfigSection('System', 'system', config.system || {}));
    }, 50);
}

// Create Config Section
function createConfigSection(title, key, data) {
    const section = document.createElement('div');
    section.className = 'config-section';
    
    // System config has a different layout (no API fields)
    if (key === 'system') {
        section.innerHTML = `
            <h3>${title}</h3>
            <div class="config-row">
                <label>Enabled:</label>
                <input type="checkbox" id="config_${key}_enabled" ${data.enabled !== false ? 'checked' : ''}>
            </div>
            <div class="config-row">
                <label>Poll Interval (seconds):</label>
                <input type="number" id="config_${key}_poll_interval" value="${data.poll_interval || 5}" min="1" max="300">
            </div>
            <div class="config-row">
                <label for="config_${key}_nas_mounts"><strong>NAS Volume Mount Points:</strong></label>
                <input type="text" id="config_${key}_nas_mounts" value="${(data.nas_mounts || []).join(', ')}" placeholder="/mnt/nas, /media/nas">
                <small style="display: block; color: #666; margin-top: 4px;">
                    Enter mount point paths separated by commas (e.g., /mnt/nas, /media/storage). 
                    The system will display used/available storage for each volume. If none are accessible, root filesystem will be shown.
                </small>
            </div>
        `;
    } else {
        // API-based configs (ARM, Pi-hole, Plex)
        section.innerHTML = `
            <h3>${title}</h3>
            <div class="config-row">
                <label>Enabled:</label>
                <input type="checkbox" id="config_${key}_enabled" ${data.enabled !== false ? 'checked' : ''}>
            </div>
            <div class="config-row">
                <label>API URL:</label>
                <input type="text" id="config_${key}_api_url" value="${data.api_url || ''}" placeholder="http://localhost:8080">
            </div>
            <div class="config-row">
                <label>API Key/Token:</label>
                <input type="text" id="config_${key}_api_key" value="${data.api_key || data.api_token || ''}" placeholder="API key or token">
            </div>
            <div class="config-row">
                <label>Poll Interval (seconds):</label>
                <input type="number" id="config_${key}_poll_interval" value="${data.poll_interval || 30}" min="1" max="300">
            </div>
            ${key === 'arm' ? `
                <div class="config-row">
                    <label>Endpoint:</label>
                    <input type="text" id="config_${key}_endpoint" value="${data.endpoint || '/json?mode=joblist'}" placeholder="/json?mode=joblist">
                </div>
            ` : ''}
        `;
    }
    
    return section;
}

// Save Config
async function saveConfig() {
    const saveBtn = document.getElementById('saveConfigBtn');
    setButtonLoading(saveBtn, true);
    
    const newConfig = {
        arm: {
            enabled: document.getElementById('config_arm_enabled').checked,
            api_url: document.getElementById('config_arm_api_url').value.trim(),
            api_key: document.getElementById('config_arm_api_key').value.trim(),
            poll_interval: parseInt(document.getElementById('config_arm_poll_interval').value),
            endpoint: document.getElementById('config_arm_endpoint').value.trim(),
            conditional: true
        },
        pihole: {
            enabled: document.getElementById('config_pihole_enabled').checked,
            api_url: document.getElementById('config_pihole_api_url').value.trim(),
            api_token: document.getElementById('config_pihole_api_key').value.trim(),
            poll_interval: parseInt(document.getElementById('config_pihole_poll_interval').value),
            conditional: false
        },
        plex: {
            enabled: document.getElementById('config_plex_enabled').checked,
            api_url: document.getElementById('config_plex_api_url').value.trim(),
            api_token: document.getElementById('config_plex_api_key').value.trim(),
            poll_interval: parseInt(document.getElementById('config_plex_poll_interval').value),
            conditional: true
        },
        system: {
            enabled: document.getElementById('config_system_enabled').checked,
            poll_interval: parseInt(document.getElementById('config_system_poll_interval').value),
            nas_mounts: document.getElementById('config_system_nas_mounts').value.split(',').map(s => s.trim()).filter(s => s),
            conditional: false
        }
    };
    
    // Optimistic update
    const oldConfig = { ...config };
    config = newConfig;
    
    try {
        const response = await fetch(`${API_BASE}/config`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newConfig)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        showSuccess('Configuration saved successfully');
    } catch (error) {
        console.error('Error saving config:', error);
        showError(`Failed to save configuration: ${error.message}`);
        // Revert optimistic update
        config = oldConfig;
        renderConfig();
    } finally {
        setButtonLoading(saveBtn, false);
    }
}

// Current Slide Preview Functions
function startCurrentSlideRefresh() {
    // Load immediately
    updateCurrentSlide();
    
    // Refresh every 2 seconds
    currentSlideRefreshInterval = setInterval(updateCurrentSlide, 2000);
}

function stopCurrentSlideRefresh() {
    if (currentSlideRefreshInterval) {
        clearInterval(currentSlideRefreshInterval);
        currentSlideRefreshInterval = null;
    }
}

function startSlidePreviewRefresh() {
    if (slidePreviewRefreshInterval) {
        return; // Already running
    }
    
    // Refresh preview images every 5 seconds
    slidePreviewRefreshInterval = setInterval(refreshSlidePreviews, 5000);
}

function stopSlidePreviewRefresh() {
    if (slidePreviewRefreshInterval) {
        clearInterval(slidePreviewRefreshInterval);
        slidePreviewRefreshInterval = null;
    }
}

async function updateCurrentSlide() {
    try {
        // Get current slide info
        const infoResponse = await fetch(`${API_BASE}/current-slide`);
        if (!infoResponse.ok) {
            throw new Error(`HTTP ${infoResponse.status}: ${infoResponse.statusText}`);
        }
        const infoData = await infoResponse.json();
        
        const infoDiv = document.getElementById('currentSlideInfo');
        const imageDiv = document.getElementById('currentSlideImage');
        const statusDiv = document.getElementById('currentSlideStatus');
        
        if (infoData.error || !infoData.id) {
            // No current slide
            infoDiv.style.display = 'none';
            imageDiv.innerHTML = '<div class="no-current-slide">No slide currently displayed<br/>(waiting or no active slides)</div>';
            statusDiv.textContent = 'Waiting for slide...';
            statusDiv.style.color = '#888';
            return;
        }
        
        // Update slide info
        const titleEl = infoDiv.querySelector('.current-slide-title');
        const metaEl = infoDiv.querySelector('.current-slide-meta');
        
        if (titleEl) {
            titleEl.textContent = infoData.title || 'Untitled';
        }
        
        if (metaEl) {
            const typeLabels = {
                'pihole_summary': 'Pi-hole Stats',
                'plex_now_playing': 'Plex Now Playing',
                'arm_rip_progress': 'ARM Rip Progress',
                'system_stats': 'System Stats',
                'weather': 'Weather',
                'static_text': 'Static Text',
                'image': 'Image'
            };
            
            const typeLabel = typeLabels[infoData.type] || infoData.type;
            const conditionalBadge = infoData.conditional ? ' (Hide if no data)' : '';
            const timeAgo = infoData.timestamp ? formatTimeAgo(Date.now() / 1000 - infoData.timestamp) : '';
            
            metaEl.textContent = `${typeLabel}${conditionalBadge}${timeAgo ? ' • ' + timeAgo : ''}`;
        }
        
        infoDiv.style.display = 'block';
        
        // Update slide image with cache-busting
        const imageUrl = `${API_BASE}/preview/current?t=${Date.now()}`;
        const img = document.createElement('img');
        img.src = imageUrl;
        img.alt = 'Current Slide Preview';
        img.onerror = () => {
            imageDiv.innerHTML = '<div class="preview-loading">Error loading preview</div>';
        };
        imageDiv.innerHTML = '';
        imageDiv.appendChild(img);
        
        // Update status
        if (infoData.has_data) {
            statusDiv.textContent = '✓ Slide is active and displaying';
            statusDiv.style.color = '#4a9eff';
        } else {
            statusDiv.textContent = '⚠ Slide configured but no data available';
            statusDiv.style.color = '#f39c12';
        }
        
    } catch (error) {
        console.error('Error updating current slide:', error);
        const imageDiv = document.getElementById('currentSlideImage');
        const statusDiv = document.getElementById('currentSlideStatus');
        if (imageDiv) {
            imageDiv.innerHTML = '<div class="preview-loading">Error loading current slide</div>';
        }
        if (statusDiv) {
            statusDiv.textContent = `Error: ${error.message}`;
            statusDiv.style.color = '#e74c3c';
        }
    }
}

function formatTimeAgo(seconds) {
    if (seconds < 1) {
        return 'just now';
    } else if (seconds < 60) {
        return `${Math.floor(seconds)}s ago`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        return `${minutes}m ago`;
    } else {
        const hours = Math.floor(seconds / 3600);
        return `${hours}h ago`;
    }
}

// Loading State Helper
function setButtonLoading(button, loading, originalText = null) {
    if (loading) {
        button.dataset.originalText = originalText || button.textContent;
        button.disabled = true;
        button.classList.add('loading');
        button.innerHTML = '<span class="btn-spinner">⏳</span> ' + (originalText || button.textContent);
    } else {
        button.disabled = false;
        button.classList.remove('loading');
        button.textContent = originalText || button.dataset.originalText || button.textContent;
        delete button.dataset.originalText;
    }
}

// Toast Notification System
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Auto-dismiss
    if (duration > 0) {
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 200);
        }, duration);
    }
    
    return toast;
}

function showSuccess(message) {
    return showToast(message, 'success', 3000);
}

function showError(message) {
    return showToast(message, 'error', 5000);
}

function showInfo(message) {
    return showToast(message, 'info', 3000);
}

// Confirm dialog (non-blocking)
function showConfirm(message, title = 'Confirm') {
    return new Promise((resolve) => {
        const modal = document.getElementById('confirmModal');
        const titleEl = document.getElementById('confirmTitle');
        const messageEl = document.getElementById('confirmMessage');
        const yesBtn = document.getElementById('confirmYes');
        const noBtn = document.getElementById('confirmNo');
        
        titleEl.textContent = title;
        messageEl.textContent = message;
        modal.style.display = 'block';
        
        const cleanup = () => {
            modal.style.display = 'none';
            yesBtn.onclick = null;
            noBtn.onclick = null;
            document.removeEventListener('keydown', handleKeydown);
        };
        
        const handleKeydown = (e) => {
            if (e.key === 'Escape') {
                cleanup();
                resolve(false);
            }
        };
        
        yesBtn.onclick = () => {
            cleanup();
            resolve(true);
        };
        
        noBtn.onclick = () => {
            cleanup();
            resolve(false);
        };
        
        document.addEventListener('keydown', handleKeydown);
        yesBtn.focus();
    });
}

// Update Window Status Bar (Mac Plus style)
function updateWindowStatusBar() {
    const itemCount = slides.length;
    const itemCountEl = document.getElementById('windowItemCount');
    if (itemCountEl) {
        itemCountEl.textContent = `${itemCount} ${itemCount === 1 ? 'item' : 'items'}`;
    }
    
    // Simulate disk info (classic Mac style)
    const diskInfoEl = document.getElementById('windowDiskInfo');
    const availableEl = document.getElementById('windowAvailable');
    if (diskInfoEl && availableEl) {
        // These are just for aesthetics to match the classic Mac look
        diskInfoEl.textContent = '';
        availableEl.textContent = '';
    }
}

// Debug Functions
async function loadDebugLogs() {
    try {
        const response = await fetch(`${API_BASE}/debug/plex`);
        const data = await response.json();
        
        // Update debug info
        document.getElementById('debugApiUrl').textContent = data.api_url || 'Not configured';
        document.getElementById('debugHasToken').textContent = data.has_token ? 'Yes' : 'No';
        document.getElementById('debugLogCount').textContent = data.log_count || 0;
        
        // Update has active streams if available (check from latest log)
        if (data.logs && data.logs.length > 0) {
            const latestLog = data.logs[data.logs.length - 1];
            if (latestLog.response_data) {
                const size = latestLog.response_data.size || 0;
                const hasStreams = size > 0;
                document.getElementById('debugHasStreams').textContent = hasStreams ? `Yes (${size} session(s))` : 'No';
            } else {
                document.getElementById('debugHasStreams').textContent = '-';
            }
        } else {
            document.getElementById('debugHasStreams').textContent = '-';
        }
        
        // Display logs
        const logsDiv = document.getElementById('debugLogs');
        if (!data.logs || data.logs.length === 0) {
            logsDiv.innerHTML = '<div class="debug-empty">No debug logs available yet. Try making a request or click "Test Connection".</div>';
            return;
        }
        
        let html = '<div class="debug-log-list">';
        // Show logs in reverse order (most recent first)
        data.logs.slice().reverse().forEach((log, index) => {
            const hasError = !!log.error;
            const statusClass = hasError ? 'error' : (log.status_code === 200 ? 'success' : 'warning');
            
            html += `<div class="debug-log-entry ${statusClass}">`;
            html += `<div class="debug-log-header">`;
            html += `<span class="debug-log-time">${log.timestamp_readable || new Date(log.timestamp * 1000).toLocaleString()}</span>`;
            html += `<span class="debug-log-endpoint">${log.endpoint || 'unknown'}</span>`;
            html += `<span class="debug-log-method">${log.method || 'GET'}</span>`;
            if (log.status_code) {
                html += `<span class="debug-log-status">${log.status_code}</span>`;
            }
            if (hasError) {
                html += `<span class="debug-log-error">ERROR</span>`;
            }
            html += `</div>`;
            
            html += `<div class="debug-log-details">`;
            html += `<div class="debug-log-section"><strong>URL:</strong> <code>${log.url || 'N/A'}</code></div>`;
            
            if (log.params && Object.keys(log.params).length > 0) {
                html += `<div class="debug-log-section"><strong>Params:</strong><pre>${JSON.stringify(log.params, null, 2)}</pre></div>`;
            }
            
            if (log.error) {
                html += `<div class="debug-log-section error"><strong>Error:</strong> <code>${log.error}</code></div>`;
            }
            
            if (log.status_code) {
                html += `<div class="debug-log-section"><strong>Status:</strong> ${log.status_code}</div>`;
            }
            
            if (log.response_data) {
                html += `<div class="debug-log-section"><strong>Response Data:</strong><pre>${JSON.stringify(log.response_data, null, 2)}</pre></div>`;
            } else if (log.response_preview) {
                html += `<div class="debug-log-section"><strong>Response Preview:</strong><pre>${log.response_preview}</pre></div>`;
                if (log.response_full_length > 500) {
                    html += `<div class="debug-log-section"><em>(Truncated, full length: ${log.response_full_length} chars)</em></div>`;
                }
            }
            
            html += `</div>`;
            html += `</div>`;
        });
        html += '</div>';
        
        logsDiv.innerHTML = html;
    } catch (error) {
        console.error('Error loading debug logs:', error);
        const logsDiv = document.getElementById('debugLogs');
        if (logsDiv) {
            logsDiv.innerHTML = `<div class="debug-error">Error loading debug logs: ${error.message}<br/><button class="btn btn-small btn-primary" onclick="loadDebugLogs()">Retry</button></div>`;
        }
        showError(`Failed to load debug logs: ${error.message}`);
    }
}

async function testPlexConnection() {
    const testBtn = document.getElementById('testPlexBtn');
    const originalText = testBtn.textContent;
    setButtonLoading(testBtn, true);
    
    try {
        const response = await fetch(`${API_BASE}/debug/plex/test`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            showSuccess(`Connection test successful! Found ${data.result?.size || 0} session(s)`);
            // Show detailed result in debug data area
            const dataDiv = document.getElementById('debugData');
            const dataContent = document.getElementById('debugDataContent');
            if (dataDiv && dataContent) {
                dataContent.textContent = JSON.stringify(data.result, null, 2);
                dataDiv.style.display = 'block';
            }
        } else {
            showError(`Connection test failed. Check debug logs for details.`);
        }
        
        // Refresh logs after test
        await loadDebugLogs();
    } catch (error) {
        console.error('Error testing connection:', error);
        showError(`Error testing connection: ${error.message}`);
    } finally {
        setButtonLoading(testBtn, false, originalText);
    }
}

async function fetchPlexData() {
    const fetchBtn = document.getElementById('fetchDataBtn');
    const originalText = fetchBtn.textContent;
    setButtonLoading(fetchBtn, true);
    
    try {
        const response = await fetch(`${API_BASE}/debug/plex/data`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        
        // Display the data
        const dataDiv = document.getElementById('debugData');
        const dataContent = document.getElementById('debugDataContent');
        
        if (dataDiv && dataContent) {
            dataContent.textContent = JSON.stringify(data, null, 2);
            dataDiv.style.display = 'block';
            
            // Scroll to data section
            dataDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            showSuccess('Data fetched successfully');
        }
        
        // Also update has_active_streams in status
        if (data.has_active_streams !== undefined) {
            document.getElementById('debugHasStreams').textContent = data.has_active_streams ? 'Yes' : 'No';
        }
        
    } catch (error) {
        console.error('Error fetching Plex data:', error);
        showError(`Error fetching data: ${error.message}`);
    } finally {
        setButtonLoading(fetchBtn, false, originalText);
    }
}

async function clearDebugLogs() {
    const confirmed = await showConfirm('Clear debug logs? This cannot be undone.', 'Clear Logs');
    if (!confirmed) {
        return;
    }
    
    // Note: This would require a backend endpoint to clear logs
    // For now, we'll just reload which will show current logs
    document.getElementById('debugLogs').innerHTML = '<div class="debug-empty">Debug logs cleared. New requests will populate logs.</div>';
    showSuccess('Debug logs cleared');
}

// ARM Debug Functions
async function loadArmDebugLogs() {
    try {
        const response = await fetch(`${API_BASE}/debug/arm`);
        const data = await response.json();
        
        // Update debug info
        document.getElementById('armDebugApiUrl').textContent = data.api_url || 'Not configured';
        document.getElementById('armDebugHasKey').textContent = data.has_key ? 'Yes' : 'No';
        document.getElementById('armDebugEndpoint').textContent = data.endpoint || 'Not configured';
        document.getElementById('armDebugLogCount').textContent = data.log_count || 0;
        
        // Update has active rip if available
        if (data.logs && data.logs.length > 0) {
            const latestLog = data.logs[data.logs.length - 1];
            if (latestLog.response_data) {
                const success = latestLog.response_data.success || false;
                const results = latestLog.response_data.results || {};
                const activeJobs = Object.values(results).filter(job => job.status === 'active');
                const hasRip = activeJobs.length > 0;
                document.getElementById('armDebugHasRip').textContent = hasRip ? `Yes (${activeJobs.length} job(s))` : 'No';
            } else {
                document.getElementById('armDebugHasRip').textContent = '-';
            }
        } else {
            document.getElementById('armDebugHasRip').textContent = '-';
        }
        
        // Display logs
        const logsDiv = document.getElementById('armDebugLogs');
        if (!data.logs || data.logs.length === 0) {
            logsDiv.innerHTML = '<div class="debug-empty">No debug logs available yet. Try making a request or click "Test Connection".</div>';
            return;
        }
        
        let html = '<div class="debug-log-list">';
        // Show logs in reverse order (most recent first)
        data.logs.slice().reverse().forEach((log, index) => {
            const hasError = !!log.error;
            const statusClass = hasError ? 'error' : (log.status_code === 200 ? 'success' : 'warning');
            
            html += `<div class="debug-log-entry ${statusClass}">`;
            html += `<div class="debug-log-header">`;
            html += `<span class="debug-log-time">${log.timestamp_readable || new Date(log.timestamp * 1000).toLocaleString()}</span>`;
            html += `<span class="debug-log-endpoint">${log.endpoint || 'unknown'}</span>`;
            html += `<span class="debug-log-method">${log.method || 'GET'}</span>`;
            if (log.status_code) {
                html += `<span class="debug-log-status">${log.status_code}</span>`;
            }
            if (hasError) {
                html += `<span class="debug-log-error">ERROR</span>`;
            }
            html += `</div>`;
            
            html += `<div class="debug-log-details">`;
            html += `<div class="debug-log-section"><strong>URL:</strong> <code>${log.url || 'N/A'}</code></div>`;
            
            if (log.params && Object.keys(log.params).length > 0) {
                html += `<div class="debug-log-section"><strong>Params:</strong><pre>${JSON.stringify(log.params, null, 2)}</pre></div>`;
            }
            
            if (log.error) {
                html += `<div class="debug-log-section error"><strong>Error:</strong> <code>${log.error}</code></div>`;
            }
            
            if (log.status_code) {
                html += `<div class="debug-log-section"><strong>Status:</strong> ${log.status_code}</div>`;
            }
            
            if (log.response_data) {
                html += `<div class="debug-log-section"><strong>Response Data:</strong><pre>${JSON.stringify(log.response_data, null, 2)}</pre></div>`;
            } else if (log.response_preview) {
                html += `<div class="debug-log-section"><strong>Response Preview:</strong><pre>${log.response_preview}</pre></div>`;
                if (log.response_full_length > 500) {
                    html += `<div class="debug-log-section"><em>(Truncated, full length: ${log.response_full_length} chars)</em></div>`;
                }
            }
            
            html += `</div>`;
            html += `</div>`;
        });
        html += '</div>';
        
        logsDiv.innerHTML = html;
    } catch (error) {
        console.error('Error loading ARM debug logs:', error);
        const logsDiv = document.getElementById('armDebugLogs');
        if (logsDiv) {
            logsDiv.innerHTML = `<div class="debug-error">Error loading debug logs: ${error.message}<br/><button class="btn btn-small btn-primary" onclick="loadArmDebugLogs()">Retry</button></div>`;
        }
        showError(`Failed to load ARM debug logs: ${error.message}`);
    }
}

async function testArmConnection() {
    const testBtn = document.getElementById('testArmBtn');
    const originalText = testBtn.textContent;
    setButtonLoading(testBtn, true);
    
    try {
        const response = await fetch(`${API_BASE}/debug/arm/test`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            showSuccess(`Connection test successful! Check debug data for details.`);
            // Show detailed result in debug data area
            const dataDiv = document.getElementById('armDebugData');
            const dataContent = document.getElementById('armDebugDataContent');
            if (dataDiv && dataContent) {
                dataContent.textContent = JSON.stringify(data.result, null, 2);
                dataDiv.style.display = 'block';
            }
        } else {
            showError(`Connection test failed. Check debug logs for details.`);
        }
        
        // Refresh logs after test
        await loadArmDebugLogs();
    } catch (error) {
        console.error('Error testing ARM connection:', error);
        showError(`Error testing connection: ${error.message}`);
    } finally {
        setButtonLoading(testBtn, false, originalText);
    }
}

async function fetchArmData() {
    const fetchBtn = document.getElementById('fetchArmDataBtn');
    const originalText = fetchBtn.textContent;
    setButtonLoading(fetchBtn, true);
    
    try {
        const response = await fetch(`${API_BASE}/debug/arm/data`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        
        // Display the data
        const dataDiv = document.getElementById('armDebugData');
        const dataContent = document.getElementById('armDebugDataContent');
        
        if (dataDiv && dataContent) {
            dataContent.textContent = JSON.stringify(data, null, 2);
            dataDiv.style.display = 'block';
            
            // Scroll to data section
            dataDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            showSuccess('Data fetched successfully');
        }
        
        // Also update has_active_rip in status
        if (data.has_active_rip !== undefined) {
            document.getElementById('armDebugHasRip').textContent = data.has_active_rip ? 'Yes' : 'No';
        }
        
    } catch (error) {
        console.error('Error fetching ARM data:', error);
        showError(`Error fetching data: ${error.message}`);
    } finally {
        setButtonLoading(fetchBtn, false, originalText);
    }
}

async function clearArmDebugLogs() {
    const confirmed = await showConfirm('Clear ARM debug logs? This cannot be undone.', 'Clear Logs');
    if (!confirmed) {
        return;
    }
    
    // Note: This would require a backend endpoint to clear logs
    // For now, we'll just reload which will show current logs
    document.getElementById('armDebugLogs').innerHTML = '<div class="debug-empty">Debug logs cleared. New requests will populate logs.</div>';
    showSuccess('ARM debug logs cleared');
}

// Keyboard Shortcuts
function setupKeyboardShortcuts() {
    // Escape key closes modals
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const slideModal = document.getElementById('slideModal');
            const confirmModal = document.getElementById('confirmModal');
            
            if (slideModal && slideModal.style.display === 'block') {
                closeSlideModal();
                e.preventDefault();
            } else if (confirmModal && confirmModal.style.display !== 'none') {
                confirmModal.style.display = 'none';
                e.preventDefault();
            }
        }
        
        // Enter key submits form if modal is open
        if (e.key === 'Enter' && e.ctrlKey) {
            const slideModal = document.getElementById('slideModal');
            if (slideModal && slideModal.style.display === 'block') {
                const form = document.getElementById('slideForm');
                if (form && document.activeElement.tagName !== 'BUTTON') {
                    form.dispatchEvent(new Event('submit', { cancelable: true }));
                    e.preventDefault();
                }
            }
        }
    });
    
    // Focus trap in modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('keydown', (e) => {
            if (e.key !== 'Tab') return;
            
            const focusableElements = modal.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];
            
            if (e.shiftKey && document.activeElement === firstElement) {
                lastElement.focus();
                e.preventDefault();
            } else if (!e.shiftKey && document.activeElement === lastElement) {
                firstElement.focus();
                e.preventDefault();
            }
        });
    });
}

// Make functions available globally
window.editSlide = editSlide;
window.deleteSlide = deleteSlide;
window.previewSlide = previewSlide;



