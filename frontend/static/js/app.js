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
    
    // Check for hash on initial load
    handleHashNavigation();
    
    // Listen for hash changes (browser back/forward buttons)
    window.addEventListener('hashchange', handleHashNavigation);
});

// Event Listeners
function setupEventListeners() {
    // Apple menu - About dialog
    const appleMenu = document.querySelector('.apple-menu');
    if (appleMenu) {
        appleMenu.addEventListener('click', () => {
            openAboutDialog();
        });
    }
    
    // About dialog close button
    const aboutCloseBtn = document.getElementById('aboutCloseBtn');
    if (aboutCloseBtn) {
        aboutCloseBtn.addEventListener('click', closeAboutDialog);
    }
    
    // Close About dialog on outside click
    const aboutModal = document.getElementById('aboutModal');
    if (aboutModal) {
        aboutModal.addEventListener('click', (e) => {
            if (e.target === aboutModal) {
                closeAboutDialog();
            }
        });
    }
    
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
    
    // Slide type change - load schema and render config fields
    document.getElementById('slideType').addEventListener('change', async (e) => {
        const slideType = e.target.value;
        await loadSlideTypeConfig(slideType);
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
    
    // JSON viewer buttons
    const refreshJsonBtn = document.getElementById('refreshJsonBtn');
    const editJsonBtn = document.getElementById('editJsonBtn');
    const exportJsonBtn = document.getElementById('exportJsonBtn');
    const importJsonBtn = document.getElementById('importJsonBtn');
    const importJsonFile = document.getElementById('importJsonFile');
    const saveJsonBtn = document.getElementById('saveJsonBtn');
    const cancelJsonEditBtn = document.getElementById('cancelJsonEditBtn');
    const importSelectedSlidesBtn = document.getElementById('importSelectedSlidesBtn');
    const cancelImportBtn = document.getElementById('cancelImportBtn');
    
    if (refreshJsonBtn) {
        refreshJsonBtn.addEventListener('click', refreshJsonViewer);
    }
    if (editJsonBtn) {
        editJsonBtn.addEventListener('click', enableJsonEditing);
    }
    if (exportJsonBtn) {
        exportJsonBtn.addEventListener('click', exportJsonConfig);
    }
    if (importJsonBtn) {
        importJsonBtn.addEventListener('click', () => importJsonFile?.click());
    }
    if (importJsonFile) {
        importJsonFile.addEventListener('change', handleJsonFileImport);
    }
    if (saveJsonBtn) {
        saveJsonBtn.addEventListener('click', saveJsonConfig);
    }
    if (cancelJsonEditBtn) {
        cancelJsonEditBtn.addEventListener('click', cancelJsonEdit);
    }
    if (importSelectedSlidesBtn) {
        importSelectedSlidesBtn.addEventListener('click', importSelectedSlides);
    }
    if (cancelImportBtn) {
        cancelImportBtn.addEventListener('click', cancelImport);
    }
    
    // Enable JSON viewer editing on input
    const jsonViewer = document.getElementById('jsonViewer');
    if (jsonViewer) {
        jsonViewer.addEventListener('input', () => {
            if (jsonViewer.contentEditable === 'true') {
                saveJsonBtn.style.display = 'inline-block';
                cancelJsonEditBtn.style.display = 'inline-block';
            }
        });
    }
    
    // Slide modal API test button
    const slideTestApiBtn = document.getElementById('slideTestApiBtn');
    if (slideTestApiBtn) {
        slideTestApiBtn.addEventListener('click', testSlideAPI);
    }
    
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
    
    // Debug buttons - System
    if (document.getElementById('refreshSystemDebugBtn')) {
        document.getElementById('refreshSystemDebugBtn').addEventListener('click', loadSystemDebugLogs);
    }
    if (document.getElementById('testSystemBtn')) {
        document.getElementById('testSystemBtn').addEventListener('click', testSystemCollection);
    }
    if (document.getElementById('clearSystemDebugBtn')) {
        document.getElementById('clearSystemDebugBtn').addEventListener('click', clearSystemDebugLogs);
    }
    
    // Close modal on outside click
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('slideModal');
        if (e.target === modal) {
            closeSlideModal();
        }
    });
}

// Switch to a specific tab by name
function switchToTab(tabName, updateHash = true) {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    let targetBtn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    
    if (!targetBtn) {
        // Invalid tab name, default to 'main'
        tabName = 'main';
        targetBtn = document.querySelector('.tab-btn[data-tab="main"]');
        if (!targetBtn) {
            return; // No tabs found at all
        }
    }
    
    // Check if tab is already active to avoid unnecessary work
    if (targetBtn.classList.contains('active')) {
        return;
    }
    
    // Remove active class from all tabs
    tabButtons.forEach(b => b.classList.remove('active'));
    tabContents.forEach(c => {
        c.classList.remove('active');
        c.style.display = 'none';
    });
    
    // Add active class to selected tab
    targetBtn.classList.add('active');
    const targetContent = document.getElementById(`${tabName}Tab`);
    if (targetContent) {
        targetContent.classList.add('active');
        targetContent.style.display = 'block';
    }
    
    // Load content when switching to specific tabs
    if (tabName === 'config') {
        loadConfig();
    } else if (tabName === 'debug') {
        loadDebugLogs();
        loadArmDebugLogs();
        loadSystemDebugLogs();
    } else if (tabName === 'designer') {
        // Widget designer tab - already initialized on DOMContentLoaded
        // Just ensure designer is visible
    }
    
    // Update URL hash if requested (avoid infinite loop when called from hashchange)
    if (updateHash && window.location.hash !== `#${tabName}`) {
        window.history.replaceState(null, '', `#${tabName}`);
    }
}

// Handle hash navigation from URL
function handleHashNavigation() {
    const hash = window.location.hash.substring(1); // Remove the # symbol
    const validTabs = ['main', 'designer', 'config', 'debug'];
    
    if (hash && validTabs.includes(hash)) {
        // Don't update hash again since we're responding to hash change
        switchToTab(hash, false);
        
        // Load JSON viewer when Config tab is opened
        if (hash === 'config' && typeof refreshJsonViewer === 'function') {
            refreshJsonViewer();
        }
    } else {
        // No hash or invalid hash, default to main tab
        if (!hash || !validTabs.includes(hash)) {
            // Set hash to main if no hash exists
            if (!hash) {
                window.history.replaceState(null, '', '#main');
            }
            switchToTab('main', false);
        }
    }
}

// Tab functionality
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    
    tabButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const targetTab = btn.getAttribute('data-tab');
            
            // Switch tab immediately for responsive UI
            switchToTab(targetTab, false);
            
            // Load JSON viewer when Config tab is opened
            if (targetTab === 'config' && typeof refreshJsonViewer === 'function') {
                refreshJsonViewer();
            }
            
            // Update URL hash - this will trigger hashchange event, but we've already switched so it won't do anything
            // Setting location.hash automatically adds to browser history for back/forward support
            window.location.hash = targetTab;
        });
    });
}

// Collapsible sections functionality
function setupCollapsibleSections() {
    const collapsibleHeaders = document.querySelectorAll('.collapsible-header');
    
    collapsibleHeaders.forEach(header => {
        // Initialize sections - if header has expanded class, ensure content is visible
        const targetId = header.getAttribute('data-target');
        if (targetId) {
            const content = document.getElementById(targetId);
            if (content && header.classList.contains('expanded')) {
                content.style.display = 'block';
                const icon = header.querySelector('.collapse-icon');
                if (icon) {
                    icon.textContent = '▼';
                }
            }
        }
        
        header.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const targetId = header.getAttribute('data-target');
            if (!targetId) return;
            
            const content = document.getElementById(targetId);
            if (!content) return;
            
            const isExpanded = header.classList.contains('expanded');
            const icon = header.querySelector('.collapse-icon');
            
            if (isExpanded) {
                // Collapse
                header.classList.remove('expanded');
                content.classList.remove('expanded');
                content.style.display = 'none';
                if (icon) {
                    icon.textContent = '▶';
                }
            } else {
                // Expand
                header.classList.add('expanded');
                content.classList.add('expanded');
                content.style.display = 'block';
                if (icon) {
                    icon.textContent = '▼';
                }
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
        'static_text': 'Static Text',
        'clock': 'Clock',
        'custom': 'Custom Widget'
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
    const slideTypeEl = document.getElementById('slideType');
    
    // Clear previous errors
    clearValidationErrors();
    
    // Check if required elements exist
    if (!title || !duration || !refreshDuration || !slideTypeEl) {
        console.error('Required form elements not found');
        return false;
    }
    
    const slideType = slideTypeEl.value;
    
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
    
    // Validate slide type-specific required fields using dynamic schema fields
    // For weather, city field is now serviceConfig_city
    if (slideType === 'weather') {
        const city = document.getElementById('serviceConfig_city');
        if (city && !city.value.trim()) {
            showFieldError(city, 'City is required for weather slides');
            isValid = false;
        }
    }
    
    // Validate image path if image type
    if (slideType === 'image') {
        const imageSelect = document.getElementById('imageSelect');
        if (!imageSelect || !imageSelect.value) {
            const imagePath = document.getElementById('imagePath');
            if (!imagePath || !imagePath.value.trim()) {
                if (imageSelect) {
                    showFieldError(imageSelect, 'Please upload or select an image');
                }
                isValid = false;
            }
        }
    }
    
    // Validate static text content if static_text type
    // Static text fields are now serviceConfig_text, serviceConfig_font_size, etc.
    if (slideType === 'static_text') {
        const text = document.getElementById('serviceConfig_text');
        if (text && !text.value.trim()) {
            showFieldError(text, 'Text content is required for static text slides');
            isValid = false;
        }
    }
    
    // Validate all required fields from dynamically rendered schema fields
    const serviceConfigContainer = document.getElementById('slideServiceConfig');
    if (serviceConfigContainer) {
        const requiredFields = serviceConfigContainer.querySelectorAll('input[required], select[required], textarea[required]');
        requiredFields.forEach(fieldEl => {
            if (fieldEl.required) {
                const value = fieldEl.type === 'number' ? fieldEl.value : fieldEl.value.trim();
                if (!value) {
                    const label = fieldEl.closest('.config-field')?.querySelector('label')?.textContent || 'This field';
                    showFieldError(fieldEl, `${label} is required`);
                    isValid = false;
                }
            }
        });
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

// Get API config from slide modal form
function getAPIConfigFromSlideModal() {
    const endpoint = document.getElementById('slideApiEndpoint')?.value.trim();
    if (!endpoint) return null;
    
    const method = document.getElementById('slideApiMethod')?.value || 'GET';
    const headersText = document.getElementById('slideApiHeaders')?.value.trim() || '{}';
    const bodyText = document.getElementById('slideApiBody')?.value.trim() || null;
    const dataPath = document.getElementById('slideApiDataPath')?.value.trim() || '$';
    const refreshInterval = parseInt(document.getElementById('slideApiRefreshInterval')?.value || 30);
    
    let headers = {};
    try {
        headers = JSON.parse(headersText);
    } catch (e) {
        console.error('Invalid headers JSON:', e);
        headers = {};
    }
    
    let body = null;
    if (bodyText && (method === 'POST' || method === 'PUT')) {
        try {
            body = JSON.parse(bodyText);
        } catch (e) {
            body = bodyText; // Use as string if not valid JSON
        }
    }
    
    return {
        endpoint: endpoint,
        method: method,
        headers: headers,
        body: body,
        data_path: dataPath,
        refresh_interval: refreshInterval,
        enabled: true
    };
}

// Update API config form in slide modal
function updateAPIConfigInSlideModal(apiConfig) {
    if (!apiConfig) {
        // Reset to defaults
        const endpointInput = document.getElementById('slideApiEndpoint');
        const methodSelect = document.getElementById('slideApiMethod');
        const headersTextarea = document.getElementById('slideApiHeaders');
        const bodyTextarea = document.getElementById('slideApiBody');
        const dataPathInput = document.getElementById('slideApiDataPath');
        const refreshInput = document.getElementById('slideApiRefreshInterval');
        
        if (endpointInput) endpointInput.value = '';
        if (methodSelect) methodSelect.value = 'GET';
        if (headersTextarea) headersTextarea.value = '';
        if (bodyTextarea) bodyTextarea.value = '';
        if (dataPathInput) dataPathInput.value = '$';
        if (refreshInput) refreshInput.value = 30;
        return;
    }
    
    const endpointInput = document.getElementById('slideApiEndpoint');
    const methodSelect = document.getElementById('slideApiMethod');
    const headersTextarea = document.getElementById('slideApiHeaders');
    const bodyTextarea = document.getElementById('slideApiBody');
    const dataPathInput = document.getElementById('slideApiDataPath');
    const refreshInput = document.getElementById('slideApiRefreshInterval');
    
    if (endpointInput) endpointInput.value = apiConfig.endpoint || '';
    if (methodSelect) methodSelect.value = apiConfig.method || 'GET';
    if (headersTextarea) headersTextarea.value = JSON.stringify(apiConfig.headers || {}, null, 2);
    if (bodyTextarea) bodyTextarea.value = apiConfig.body ? (typeof apiConfig.body === 'string' ? apiConfig.body : JSON.stringify(apiConfig.body, null, 2)) : '';
    if (dataPathInput) dataPathInput.value = apiConfig.data_path || '$';
    if (refreshInput) refreshInput.value = apiConfig.refresh_interval || 30;
}

// Setup collapsible API section in slide modal
function setupSlideAPISection() {
    const apiHeader = document.getElementById('slideApiConfigHeader');
    const apiContent = document.getElementById('slideApiConfigContent');
    
    if (!apiHeader || !apiContent) return;
    
    // Initialize as expanded by default
    if (apiHeader.classList.contains('expanded')) {
        apiContent.style.display = 'block';
        const icon = apiHeader.querySelector('.collapse-icon');
        if (icon) {
            icon.textContent = '▼';
        }
    }
    
    // Remove existing listener if any
    const newHeader = apiHeader.cloneNode(true);
    apiHeader.parentNode.replaceChild(newHeader, apiHeader);
    
    newHeader.addEventListener('click', () => {
        const isExpanded = newHeader.classList.contains('expanded');
        apiContent.style.display = isExpanded ? 'none' : 'block';
        newHeader.classList.toggle('expanded', !isExpanded);
        
        const icon = newHeader.querySelector('.collapse-icon');
        if (icon) {
            icon.textContent = isExpanded ? '▶' : '▼';
        }
    });
}

// Load slide type configuration schema and render fields
async function loadSlideTypeConfig(slideTypeName) {
    try {
        const response = await fetch(`${API_BASE}/slides/types/${slideTypeName}/schema`);
        if (!response.ok) {
            throw new Error(`Failed to load schema: ${response.statusText}`);
        }
        const schema = await response.json();
        renderSlideTypeConfig(schema);
    } catch (error) {
        console.error('Error loading slide type config:', error);
        showError(`Failed to load slide type configuration: ${error.message}`);
    }
}

// Render slide type configuration fields based on schema
function renderSlideTypeConfig(schema) {
    const container = document.getElementById('slideServiceConfig');
    if (!container) return;
    
    // Clear existing fields
    container.innerHTML = '';
    
    // Hide/show conditional checkbox based on schema
    const conditionalContainer = document.getElementById('slideConditionalContainer');
    const conditionalHelp = document.getElementById('slideConditionalHelp');
    const conditionalCheckbox = document.getElementById('slideConditional');
    
    if (schema.conditional) {
        if (conditionalContainer) conditionalContainer.style.display = 'block';
        if (conditionalHelp) conditionalHelp.style.display = 'block';
        if (conditionalCheckbox) conditionalCheckbox.checked = schema.default_conditional !== false;
    } else {
        if (conditionalContainer) conditionalContainer.style.display = 'none';
        if (conditionalHelp) conditionalHelp.style.display = 'none';
        if (conditionalCheckbox) conditionalCheckbox.checked = false;
    }
    
    // Hide/show old API section based on slide type
    const slideType = document.getElementById('slideType')?.value;
    const oldApiSection = document.querySelector('.slide-api-section');
    if (oldApiSection) {
        // Only show old API section for custom slides (they use api_config separately)
        oldApiSection.style.display = slideType === 'custom' ? 'block' : 'none';
    }
    
    // Hide legacy settings for slide types that now use dynamic config
    toggleWeatherSettings(false); // Always hide legacy - use schema
    toggleStaticTextSettings(false); // Always hide legacy - use schema
    toggleImageSettings(false); // Always hide legacy - use schema (but keep image select for file upload)
    
    // Show note if present
    if (schema.note) {
        const noteDiv = document.createElement('p');
        noteDiv.className = 'schema-note';
        noteDiv.style.cssText = 'color: #666; font-size: 13px; margin-bottom: 16px; font-style: italic;';
        noteDiv.textContent = schema.note;
        container.appendChild(noteDiv);
    }
    
    // Render fields based on schema
    schema.fields.forEach(fieldGroup => {
        if (fieldGroup.type === 'group') {
            const groupDiv = document.createElement('div');
            groupDiv.className = 'service-config-group';
            groupDiv.style.cssText = 'margin-bottom: 20px;';
            
            const groupTitle = document.createElement('h4');
            groupTitle.style.cssText = 'margin-bottom: 12px; font-size: 14px; font-weight: bold; color: #000;';
            groupTitle.textContent = fieldGroup.label;
            groupDiv.appendChild(groupTitle);
            
            fieldGroup.fields.forEach(field => {
                const fieldDiv = createConfigFieldElement(field);
                groupDiv.appendChild(fieldDiv);
            });
            
            container.appendChild(groupDiv);
        } else {
            // Direct field (not in a group - like city, temp_unit, text, image_path)
            const fieldDiv = createConfigFieldElement(fieldGroup);
            container.appendChild(fieldDiv);
        }
    });
    
    // Special handling for image slides - use custom image select/upload UI
    // Filter out image_path from schema fields since we handle it separately
    if (slideType === 'image') {
        schema.fields = schema.fields.filter(f => f.name !== 'image_path');
        
        // Add image upload/select UI
        const imageDiv = document.createElement('div');
        imageDiv.className = 'image-upload-section';
        imageDiv.style.cssText = 'margin-top: 16px;';
        imageDiv.innerHTML = `
            <label for="imageUpload">Upload New Image:</label>
            <input type="file" id="imageUpload" accept="image/*" style="width: 100%; padding: 6px; margin-top: 4px;">
            <small style="display: block; color: #666; margin-top: 4px; font-size: 12px;">
                Supported formats: PNG, JPG, GIF, BMP, WEBP (max 10MB). Images will be displayed in black and white with dithering.
            </small>
            <div style="margin-top: 16px;">
                <label for="imageSelect">Or Select Existing Image:</label>
                <select id="imageSelect" style="width: 100%; padding: 6px; margin-top: 4px;">
                    <option value="">-- Select an image --</option>
                </select>
            </div>
            <div id="imagePreview" style="margin-top: 16px; display: none;">
                <img id="imagePreviewImg" src="" alt="Image preview" style="max-width: 100%; max-height: 200px; border: 1px solid #ccc; border-radius: 4px;">
                <div id="imageInfo" style="margin-top: 8px; font-size: 12px; color: #666;"></div>
            </div>
            <input type="hidden" id="imagePath">
        `;
        container.appendChild(imageDiv);
        
        // Load existing images
        loadExistingImages().then(() => {
            const imageSelect = document.getElementById('imageSelect');
            const imageUpload = document.getElementById('imageUpload');
            if (imageSelect) {
                imageSelect.addEventListener('change', handleImageSelect);
            }
            if (imageUpload) {
                imageUpload.addEventListener('change', handleImageUpload);
            }
        });
    }
}

// Create a form field element from schema field definition
function createConfigFieldElement(field) {
    const div = document.createElement('div');
    div.className = 'config-field';
    div.style.cssText = 'margin-bottom: 12px;';
    
    const label = document.createElement('label');
    label.textContent = field.label;
    label.setAttribute('for', `serviceConfig_${field.name}`);
    if (field.required) {
        label.classList.add('required');
    }
    div.appendChild(label);
    
    let input;
    switch (field.type) {
        case 'url':
        case 'text':
            input = document.createElement('input');
            input.type = field.type === 'url' ? 'url' : 'text';
            input.id = `serviceConfig_${field.name}`;
            input.value = field.default || '';
            input.placeholder = field.placeholder || '';
            input.style.cssText = 'width: 100%; padding: 6px; margin-top: 4px;';
            break;
        case 'password':
            input = document.createElement('input');
            input.type = 'password';
            input.id = `serviceConfig_${field.name}`;
            input.value = field.default || '';
            input.placeholder = field.placeholder || '';
            input.style.cssText = 'width: 100%; padding: 6px; margin-top: 4px;';
            break;
        case 'number':
            input = document.createElement('input');
            input.type = 'number';
            input.id = `serviceConfig_${field.name}`;
            input.value = field.default || '';
            input.min = field.min || '';
            input.max = field.max || '';
            input.style.cssText = 'width: 100%; padding: 6px; margin-top: 4px;';
            break;
        case 'select':
            input = document.createElement('select');
            input.id = `serviceConfig_${field.name}`;
            input.style.cssText = 'width: 100%; padding: 6px; margin-top: 4px;';
            if (field.options) {
                field.options.forEach(option => {
                    const optionEl = document.createElement('option');
                    optionEl.value = option.value;
                    optionEl.textContent = option.label;
                    if (option.value === field.default) {
                        optionEl.selected = true;
                    }
                    input.appendChild(optionEl);
                });
            }
            break;
        case 'textarea':
            input = document.createElement('textarea');
            input.id = `serviceConfig_${field.name}`;
            input.value = field.default || '';
            input.placeholder = field.placeholder || '';
            input.rows = field.rows || 3;
            input.style.cssText = 'width: 100%; padding: 6px; margin-top: 4px; font-family: monospace; resize: vertical;';
            break;
        case 'file':
            input = document.createElement('input');
            input.type = 'file';
            input.id = `serviceConfig_${field.name}`;
            input.accept = field.accept || '*/*';
            input.style.cssText = 'width: 100%; padding: 6px; margin-top: 4px;';
            break;
        case 'checkbox':
            input = document.createElement('input');
            input.type = 'checkbox';
            input.id = `serviceConfig_${field.name}`;
            input.checked = field.default !== undefined ? field.default : false;
            input.style.cssText = 'margin-top: 4px; margin-right: 8px;';
            // For checkboxes, put the label after the input
            label.removeAttribute('for');
            label.style.cssText = 'display: inline-flex; align-items: center; cursor: pointer;';
            label.insertBefore(input, label.firstChild);
            div.appendChild(label);
            return div;
        default:
            input = document.createElement('input');
            input.type = 'text';
            input.id = `serviceConfig_${field.name}`;
            input.value = field.default || '';
            input.style.cssText = 'width: 100%; padding: 6px; margin-top: 4px;';
    }
    
    div.appendChild(input);
    
    if (field.help) {
        const helpText = document.createElement('small');
        helpText.style.cssText = 'display: block; color: #666; margin-top: 4px; font-size: 12px;';
        helpText.textContent = field.help;
        div.appendChild(helpText);
    }
    
    return div;
}

// Get service config from form
function getServiceConfigFromForm(schema) {
    const serviceConfig = {};
    const apiConfig = {};
    
    if (!schema || !schema.fields) return { service_config: serviceConfig, api_config: apiConfig };
    
    schema.fields.forEach(fieldGroup => {
        if (fieldGroup.type === 'group') {
            const configDict = fieldGroup.name === 'service_config' ? serviceConfig : apiConfig;
            
            fieldGroup.fields.forEach(field => {
                const input = document.getElementById(`serviceConfig_${field.name}`);
                if (input) {
                    if (field.type === 'checkbox') {
                        configDict[field.name] = input.checked;
                    } else if (field.type === 'number') {
                        configDict[field.name] = input.value ? parseInt(input.value) : (field.default || null);
                    } else if (field.type === 'textarea') {
                        // For JSON fields like headers, try to parse
                        if (field.name === 'headers' || field.name === 'body') {
                            try {
                                configDict[field.name] = JSON.parse(input.value || '{}');
                            } catch (e) {
                                configDict[field.name] = input.value || '';
                            }
                        } else {
                            configDict[field.name] = input.value.trim();
                        }
                    } else {
                        configDict[field.name] = input.value.trim();
                    }
                }
            });
        } else {
            // Direct field (like city, temp_unit for weather)
            const fieldName = fieldGroup.name;  // fieldGroup is the direct field definition
            const input = document.getElementById(`serviceConfig_${fieldName}`);
            if (input) {
                if (fieldGroup.type === 'checkbox') {
                    serviceConfig[fieldName] = input.checked;
                } else if (fieldGroup.type === 'number') {
                    serviceConfig[fieldName] = input.value ? parseInt(input.value) : (fieldGroup.default || null);
                } else {
                    serviceConfig[fieldName] = input.value.trim();
                }
            }
        }
    });
    
    return {
        service_config: Object.keys(serviceConfig).length > 0 ? serviceConfig : undefined,
        api_config: Object.keys(apiConfig).length > 0 ? apiConfig : undefined
    };
}

// Populate service config form from slide data
function populateServiceConfigForm(slide, schema) {
    if (!schema || !schema.fields) return;
    
    const serviceConfig = slide.service_config || {};
    const apiConfig = slide.api_config || {};
    
    schema.fields.forEach(fieldDef => {
        if (fieldDef.type === 'group') {
            const configDict = fieldDef.name === 'service_config' ? serviceConfig : apiConfig;
            
            fieldDef.fields.forEach(field => {
                const input = document.getElementById(`serviceConfig_${field.name}`);
                if (input && configDict[field.name] !== undefined) {
                    if (field.type === 'checkbox') {
                        input.checked = configDict[field.name] === true || configDict[field.name] === 'true';
                    } else if (field.type === 'textarea' && (field.name === 'headers' || field.name === 'body')) {
                        // Format JSON for display
                        input.value = typeof configDict[field.name] === 'string' 
                            ? configDict[field.name] 
                            : JSON.stringify(configDict[field.name], null, 2);
                    } else {
                        input.value = configDict[field.name];
                    }
                }
            });
        } else {
            // Direct field (like city, temp_unit, text, image_path)
            const fieldName = fieldDef.name;
            const input = document.getElementById(`serviceConfig_${fieldName}`);
            if (input && slide[fieldName] !== undefined) {
                if (fieldDef.type === 'checkbox') {
                    input.checked = slide[fieldName] === true || slide[fieldName] === 'true';
                } else {
                    input.value = slide[fieldName];
                }
            }
        }
    });
}

// Test API from slide modal
async function testSlideAPI() {
    const apiConfig = getAPIConfigFromSlideModal();
    if (!apiConfig || !apiConfig.endpoint) {
        showError('Please enter an API endpoint');
        return;
    }
    
    const testResult = document.getElementById('slideApiTestResult');
    if (testResult) {
        testResult.style.display = 'block';
        testResult.className = 'api-test-result';
        testResult.innerHTML = 'Testing API...';
    }
    
    try {
        const response = await fetch(`${API_BASE}/widgets/test-api`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ api_config: apiConfig })
        });
        
        const data = await response.json();
        
        if (testResult) {
            if (data.success) {
                testResult.className = 'api-test-result success';
                testResult.innerHTML = `✓ API Test Successful\n\nResult:\n${JSON.stringify(data.result, null, 2)}\n\nKeys: ${data.result_keys ? data.result_keys.join(', ') : 'N/A'}`;
            } else {
                testResult.className = 'api-test-result error';
                testResult.innerHTML = `✗ API Test Failed\n\nError: ${data.error || 'Unknown error'}`;
            }
        }
    } catch (error) {
        if (testResult) {
            testResult.className = 'api-test-result error';
            testResult.innerHTML = `✗ API Test Failed\n\nError: ${error.message}`;
        }
    }
}

// Slide Modal
async function openSlideModal(slide = null) {
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
        
        // Load schema and populate config fields
        await loadSlideTypeConfig(slideType);
        document.getElementById('slideConditional').checked = slide.conditional || false;
        
        // Populate service config from slide
        try {
            const schemaResponse = await fetch(`${API_BASE}/slides/types/${slideType}/schema`);
            if (schemaResponse.ok) {
                const schema = await schemaResponse.json();
                populateServiceConfigForm(slide, schema);
            }
        } catch (error) {
            console.error('Error loading schema for edit:', error);
        }
        
        // Legacy field handling (for backwards compatibility during transition)
        if (slideType === 'weather') {
            const cityInput = document.getElementById('serviceConfig_city');
            if (cityInput && slide.city) {
                cityInput.value = slide.city;
            }
            const tempUnitInput = document.getElementById('serviceConfig_temp_unit');
            if (tempUnitInput && slide.temp_unit) {
                tempUnitInput.value = slide.temp_unit;
            }
        }
        
        // Image-specific fields (legacy handling)
        toggleImageSettings(false); // Don't use legacy, use schema
        if (slideType === 'image' && slide.image_path) {
            loadExistingImages().then(() => {
                const imageSelect = document.getElementById('imageSelect');
                if (imageSelect) {
                    imageSelect.value = slide.image_path;
                    handleImageSelect({ target: imageSelect });
                }
            });
        }
    } else {
        document.getElementById('modalTitle').textContent = 'Add Slide';
        form.reset();
        toggleWeatherSettings(false);
        toggleStaticTextSettings(false);
        toggleImageSettings(false);
        hideImagePreview();
        
        // Load schema for default slide type
        const defaultType = document.getElementById('slideType').value;
        await loadSlideTypeConfig(defaultType);
    }
    
    // Setup API section collapsible (for custom slides)
    setupSlideAPISection();
    
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
    updateAPIConfigInSlideModal(null);
    // Hide test result
    const testResult = document.getElementById('slideApiTestResult');
    if (testResult) {
        testResult.style.display = 'none';
        testResult.innerHTML = '';
    }
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
    
    // Load schema and collect service_config and type-specific fields
    try {
        const schemaResponse = await fetch(`${API_BASE}/slides/types/${slideType}/schema`);
        if (schemaResponse.ok) {
            const schema = await schemaResponse.json();
            const config = getServiceConfigFromForm(schema);
            
            // Add service_config if present
            if (config.service_config && Object.keys(config.service_config).length > 0) {
                formData.service_config = config.service_config;
            }
            
            // For custom slides, also add api_config from old API section or from schema
            if (slideType === 'custom') {
                // Try to get from old API section first (for backwards compatibility)
                const oldApiConfig = getAPIConfigFromSlideModal();
                if (oldApiConfig && oldApiConfig.endpoint) {
                    formData.api_config = oldApiConfig;
                } else if (config.api_config && Object.keys(config.api_config).length > 0) {
                    formData.api_config = config.api_config;
                }
            }
            
            // Extract direct fields (like city, temp_unit, text, image_path) from form
            // These should be at the root level of formData (not in service_config)
            schema.fields.forEach(fieldDef => {
                if (fieldDef.type !== 'group') {
                    // Direct field (like city, temp_unit, text, image_path)
                    const input = document.getElementById(`serviceConfig_${fieldDef.name}`);
                    if (input) {
                        if (fieldDef.type === 'number') {
                            const value = input.value ? parseInt(input.value) : (fieldDef.default || null);
                            if (value !== null && value !== undefined) {
                                formData[fieldDef.name] = value;
                            }
                        } else if (fieldDef.type === 'checkbox') {
                            formData[fieldDef.name] = input.checked;
                        } else if (fieldDef.type === 'select') {
                            const value = input.value;
                            if (value) {
                                formData[fieldDef.name] = value;
                            }
                        } else if (fieldDef.type === 'textarea') {
                            const value = input.value.trim();
                            if (value) {
                                formData[fieldDef.name] = value;
                            }
                        } else if (fieldDef.type === 'file') {
                            // File uploads handled separately via image select/upload
                        } else {
                            // text, url, password
                            const value = input.value.trim();
                            if (value) {
                                formData[fieldDef.name] = value;
                            }
                        }
                    }
                }
            });
        }
    } catch (error) {
        console.error('Error loading schema for save:', error);
        showError('Failed to load slide configuration schema');
        setButtonLoading(submitBtn, false);
        return;
    }
    
    // Legacy handling for image path (from image select)
    if (slideType === 'image') {
        const imageSelect = document.getElementById('imageSelect');
        if (imageSelect && imageSelect.value) {
            formData.image_path = imageSelect.value;
        }
        // Also check for uploaded file
        const imageUpload = document.getElementById('imageUpload');
        if (imageUpload && imageUpload.files && imageUpload.files.length > 0) {
            // File upload will be handled by the upload endpoint
            // The image_path will be set after upload
        }
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
        
        // Note about per-slide configuration
        const noteDiv = document.createElement('div');
        noteDiv.style.cssText = 'padding: 16px; margin-bottom: 16px; background: #e8f4f8; border: 1px solid #b3d9e6; border-radius: 4px;';
        noteDiv.innerHTML = `
            <p style="margin: 0 0 8px 0; font-weight: bold; color: #000;">Configuration moved to slides</p>
            <p style="margin: 0; color: #333; font-size: 13px; line-height: 1.5;">
                Service configurations (ARM, Pi-hole, Plex, System) are now configured individually for each slide 
                in the Edit/New Slide dialog. Each slide can have its own API endpoints, credentials, and settings.
            </p>
        `;
        container.appendChild(noteDiv);
        
        // Only show application-wide configs (like weather API key if needed)
        // For now, weather uses wttr.in which doesn't need an API key
        // If we add other application-wide settings in the future, add them here
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
    
    // Application-wide configuration (minimal - only weather if needed in future)
    const newConfig = {
        weather: config.weather || {},  // Keep weather config if present
        // Other application-wide settings can be added here
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
        
        showSuccess('Application configuration saved successfully');
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

// JSON Viewer State
let jsonViewerOriginalData = null;
let importedConfigData = null;

// Refresh JSON Viewer
async function refreshJsonViewer() {
    const jsonViewer = document.getElementById('jsonViewer');
    if (!jsonViewer) return;
    
    try {
        const response = await fetch(`${API_BASE}/slides`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        jsonViewerOriginalData = data;
        jsonViewer.textContent = JSON.stringify(data, null, 2);
        jsonViewer.contentEditable = 'false';
        jsonViewer.style.backgroundColor = '#f9f9f9';
        jsonViewer.classList.remove('json-error');
        
        // Hide save/cancel buttons and show edit button
        document.getElementById('saveJsonBtn').style.display = 'none';
        document.getElementById('cancelJsonEditBtn').style.display = 'none';
        document.getElementById('editJsonBtn').style.display = 'inline-block';
        
        // Hide import slide selector
        document.getElementById('importSlideSelector').style.display = 'none';
        importedConfigData = null;
    } catch (error) {
        console.error('Error loading JSON:', error);
        jsonViewer.textContent = `Error loading configuration: ${error.message}`;
        jsonViewer.classList.add('json-error');
        showError(`Failed to load configuration: ${error.message}`);
    }
}

// Enable JSON Editing
function enableJsonEditing() {
    const jsonViewer = document.getElementById('jsonViewer');
    if (!jsonViewer) return;
    
    jsonViewer.contentEditable = 'true';
    jsonViewer.style.backgroundColor = '#fff';
    jsonViewer.focus();
    
    // Hide edit button, show save/cancel buttons
    document.getElementById('editJsonBtn').style.display = 'none';
    document.getElementById('saveJsonBtn').style.display = 'inline-block';
    document.getElementById('cancelJsonEditBtn').style.display = 'inline-block';
}

// Export JSON Config
function exportJsonConfig() {
    const jsonViewer = document.getElementById('jsonViewer');
    if (!jsonViewer) return;
    
    try {
        const jsonText = jsonViewer.textContent;
        const data = JSON.parse(jsonText);
        const jsonString = JSON.stringify(data, null, 2);
        
        // Create blob and download
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `slides-config-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showSuccess('Configuration exported successfully');
    } catch (error) {
        console.error('Error exporting JSON:', error);
        showError(`Failed to export configuration: ${error.message}. Please ensure the JSON is valid.`);
    }
}

// Handle JSON File Import
async function handleJsonFileImport(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const jsonText = e.target.result;
            const data = JSON.parse(jsonText);
            
            // Validate structure
            if (!data || typeof data !== 'object') {
                throw new Error('Invalid JSON: must be an object');
            }
            
            if (!data.slides || !Array.isArray(data.slides)) {
                throw new Error('Invalid configuration: missing or invalid "slides" array');
            }
            
            // Show import options: import all or select individual slides
            importedConfigData = data;
            showImportSlideSelector(data.slides);
            
            // Also update the JSON viewer with imported data
            const jsonViewer = document.getElementById('jsonViewer');
            jsonViewer.textContent = JSON.stringify(data, null, 2);
            jsonViewer.contentEditable = 'false';
            jsonViewer.style.backgroundColor = '#f9f9f9';
            jsonViewer.classList.remove('json-error');
            document.getElementById('editJsonBtn').style.display = 'inline-block';
            
            showSuccess(`Configuration loaded. Found ${data.slides.length} slide(s). Select slides to import or import all.`);
        } catch (error) {
            console.error('Error parsing imported JSON:', error);
            showError(`Failed to import configuration: ${error.message}`);
        }
    };
    
    reader.readAsText(file);
    // Reset file input
    event.target.value = '';
}

// Show Import Slide Selector
function showImportSlideSelector(importedSlides) {
    const selector = document.getElementById('importSlideSelector');
    const slideList = document.getElementById('importSlideList');
    
    if (!selector || !slideList) return;
    
    slideList.innerHTML = '';
    
    importedSlides.forEach((slide, index) => {
        const slideDiv = document.createElement('div');
        slideDiv.className = 'import-slide-item';
        slideDiv.style.cssText = 'padding: 8px; margin-bottom: 8px; border: 1px solid #ddd; border-radius: 4px; background: #f9f9f9;';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `import-slide-${index}`;
        checkbox.value = index;
        checkbox.checked = true;
        checkbox.style.marginRight = '8px';
        
        const label = document.createElement('label');
        label.htmlFor = `import-slide-${index}`;
        label.style.cssText = 'cursor: pointer; font-size: 13px;';
        label.innerHTML = `<strong>${slide.title || 'Untitled'}</strong> (Type: ${slide.type || 'unknown'}, ID: ${slide.id || 'N/A'})`;
        
        slideDiv.appendChild(checkbox);
        slideDiv.appendChild(label);
        slideList.appendChild(slideDiv);
    });
    
    // Add "Select All" / "Deselect All" buttons
    const selectAllDiv = document.createElement('div');
    selectAllDiv.style.cssText = 'margin-bottom: 12px;';
    const selectAllBtn = document.createElement('button');
    selectAllBtn.textContent = 'Select All';
    selectAllBtn.className = 'btn btn-small btn-secondary';
    selectAllBtn.onclick = () => {
        slideList.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = true);
    };
    const deselectAllBtn = document.createElement('button');
    deselectAllBtn.textContent = 'Deselect All';
    deselectAllBtn.className = 'btn btn-small btn-secondary';
    deselectAllBtn.onclick = () => {
        slideList.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
    };
    selectAllDiv.appendChild(selectAllBtn);
    selectAllDiv.appendChild(deselectAllBtn);
    slideList.insertBefore(selectAllDiv, slideList.firstChild);
    
    selector.style.display = 'block';
}

// Import Selected Slides
async function importSelectedSlides() {
    if (!importedConfigData) {
        showError('No imported configuration available');
        return;
    }
    
    const checkboxes = document.querySelectorAll('#importSlideList input[type="checkbox"]:checked');
    const selectedIndices = Array.from(checkboxes).map(cb => parseInt(cb.value));
    
    if (selectedIndices.length === 0) {
        showError('Please select at least one slide to import');
        return;
    }
    
    try {
        // Get current configuration
        const currentResponse = await fetch(`${API_BASE}/slides`);
        if (!currentResponse.ok) {
            throw new Error(`Failed to load current configuration: ${currentResponse.statusText}`);
        }
        const currentConfig = await currentResponse.json();
        const currentSlides = currentConfig.slides || [];
        
        // Get max ID from current slides
        const maxId = currentSlides.length > 0 
            ? Math.max(...currentSlides.map(s => s.id || 0))
            : 0;
        
        // Import selected slides with new IDs
        const slidesToImport = selectedIndices.map(index => {
            const slide = JSON.parse(JSON.stringify(importedConfigData.slides[index]));
            // Remove old ID, will be assigned new one
            delete slide.id;
            return slide;
        });
        
        // Assign new IDs and order values
        slidesToImport.forEach((slide, i) => {
            slide.id = maxId + i + 1;
            slide.order = currentSlides.length + i;
        });
        
        // Add to current slides
        const updatedSlides = [...currentSlides, ...slidesToImport];
        const updatedConfig = {
            ...currentConfig,
            slides: updatedSlides
        };
        
        // Save updated configuration
        const saveResponse = await fetch(`${API_BASE}/slides`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedConfig)
        });
        
        if (!saveResponse.ok) {
            const errorData = await saveResponse.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${saveResponse.status}: ${saveResponse.statusText}`);
        }
        
        showSuccess(`Successfully imported ${slidesToImport.length} slide(s)`);
        
        // Reload slides and refresh JSON viewer
        await loadSlides();
        await refreshJsonViewer();
        
        // Hide import selector
        document.getElementById('importSlideSelector').style.display = 'none';
        importedConfigData = null;
    } catch (error) {
        console.error('Error importing slides:', error);
        showError(`Failed to import slides: ${error.message}`);
    }
}

// Cancel Import
function cancelImport() {
    document.getElementById('importSlideSelector').style.display = 'none';
    importedConfigData = null;
    refreshJsonViewer();
}

// Save JSON Config
async function saveJsonConfig() {
    const jsonViewer = document.getElementById('jsonViewer');
    if (!jsonViewer) return;
    
    const saveBtn = document.getElementById('saveJsonBtn');
    setButtonLoading(saveBtn, true);
    
    try {
        const jsonText = jsonViewer.textContent;
        const data = JSON.parse(jsonText);
        
        // Validate structure
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid JSON: must be an object');
        }
        
        if (!data.slides || !Array.isArray(data.slides)) {
            throw new Error('Invalid configuration: missing or invalid "slides" array');
        }
        
        // Validate each slide
        for (const slide of data.slides) {
            if (!slide.id || !slide.type) {
                throw new Error('Invalid configuration: each slide must have "id" and "type"');
            }
        }
        
        // Save configuration
        const response = await fetch(`${API_BASE}/slides`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        jsonViewerOriginalData = data;
        saveBtn.style.display = 'none';
        document.getElementById('cancelJsonEditBtn').style.display = 'none';
        document.getElementById('editJsonBtn').style.display = 'inline-block';
        
        // Make read-only again
        jsonViewer.contentEditable = 'false';
        jsonViewer.style.backgroundColor = '#f9f9f9';
        
        showSuccess('Configuration saved successfully');
        
        // Reload slides to reflect changes
        await loadSlides();
    } catch (error) {
        console.error('Error saving JSON:', error);
        showError(`Failed to save configuration: ${error.message}`);
        jsonViewer.classList.add('json-error');
    } finally {
        setButtonLoading(saveBtn, false);
    }
}

// Cancel JSON Edit
function cancelJsonEdit() {
    const jsonViewer = document.getElementById('jsonViewer');
    if (!jsonViewer || !jsonViewerOriginalData) return;
    
    jsonViewer.textContent = JSON.stringify(jsonViewerOriginalData, null, 2);
    jsonViewer.classList.remove('json-error');
    jsonViewer.contentEditable = 'false';
    jsonViewer.style.backgroundColor = '#f9f9f9';
    document.getElementById('saveJsonBtn').style.display = 'none';
    document.getElementById('cancelJsonEditBtn').style.display = 'none';
    document.getElementById('editJsonBtn').style.display = 'inline-block';
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
        console.log('Loading Plex debug logs from:', `${API_BASE}/debug/plex`);
        const response = await fetch(`${API_BASE}/debug/plex`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Plex debug response:', data);
        
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
        if (!logsDiv) {
            console.error('debugLogs element not found');
            return;
        }
        
        if (!data.logs || data.logs.length === 0) {
            console.log('No Plex debug logs found');
            logsDiv.innerHTML = '<div class="debug-empty">No debug logs available yet. Try making a request or click "Test Connection".</div>';
            return;
        }
        
        console.log(`Displaying ${data.logs.length} Plex debug log entries`);
        
        let html = '<div class="debug-log-list">';
        // Logs are already sorted most recent first from backend, so no need to reverse
        data.logs.forEach((log, index) => {
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
        console.log('Loading ARM debug logs from:', `${API_BASE}/debug/arm`);
        const response = await fetch(`${API_BASE}/debug/arm`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('ARM debug response:', data);
        
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
        if (!logsDiv) {
            console.error('armDebugLogs element not found');
            return;
        }
        
        if (!data.logs || data.logs.length === 0) {
            console.log('No ARM debug logs found');
            logsDiv.innerHTML = '<div class="debug-empty">No debug logs available yet. Try making a request or click "Test Connection".</div>';
            return;
        }
        
        console.log(`Displaying ${data.logs.length} ARM debug log entries`);
        
        let html = '<div class="debug-log-list">';
        // Logs are already sorted most recent first from backend, so no need to reverse
        data.logs.forEach((log, index) => {
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

// System Debug Functions
async function loadSystemDebugLogs() {
    try {
        console.log('Loading system debug logs...');
        const response = await fetch(`${API_BASE}/debug/system`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('System debug data:', data);
        
        // Update debug info
        document.getElementById('systemDebugSlideCount').textContent = data.total_slides || 0;
        document.getElementById('systemDebugLogCount').textContent = data.log_count || 0;
        
        // Update last collection time
        if (data.logs && data.logs.length > 0) {
            const latestLog = data.logs[0]; // Most recent is first
            document.getElementById('systemDebugLastCollection').textContent = latestLog.timestamp_readable || '-';
        } else {
            document.getElementById('systemDebugLastCollection').textContent = '-';
        }
        
        // Display logs
        const logsDiv = document.getElementById('systemDebugLogs');
        if (!data.logs || data.logs.length === 0) {
            logsDiv.innerHTML = '<div class="debug-empty">No debug logs available yet. System stats will be collected automatically, or click "Test Collection" to force a collection.</div>';
            return;
        }
        
        let html = '<div class="debug-log-list">';
        // Show logs (most recent first - they're already sorted)
        data.logs.forEach((log, index) => {
            const hasError = log.errors && log.errors.length > 0;
            const statusClass = hasError ? 'error' : (log.success ? 'success' : 'warning');
            
            html += `<div class="debug-log-entry ${statusClass}">`;
            html += '<div class="debug-log-header">';
            html += `<span class="debug-log-time">${log.timestamp_readable || 'Unknown time'}</span>`;
            html += `<span class="debug-log-status">${log.success ? 'SUCCESS' : 'FAILED'}</span>`;
            if (log.slide_title) {
                html += `<span class="debug-log-endpoint">${log.slide_title} (ID: ${log.slide_id})</span>`;
            }
            html += `<span class="debug-log-method">${log.collection_time_ms}ms</span>`;
            html += '</div>';
            
            if (log.success) {
                html += '<div class="debug-log-details">';
                if (log.cpu_percent !== null && log.cpu_percent !== undefined) {
                    html += `<p><strong>CPU:</strong> ${log.cpu_percent}%</p>`;
                }
                if (log.memory_percent !== null && log.memory_percent !== undefined) {
                    html += `<p><strong>Memory:</strong> ${log.memory_percent}%</p>`;
                }
                if (log.disk_count !== null && log.disk_count !== undefined) {
                    html += `<p><strong>Disks Monitored:</strong> ${log.disk_count}</p>`;
                }
                if (log.nas_mounts_configured !== null && log.nas_mounts_configured !== undefined) {
                    html += `<p><strong>NAS Mounts Configured:</strong> ${log.nas_mounts_configured}</p>`;
                }
                html += '</div>';
                
                // Show mount checks
                if (log.mount_checks && log.mount_checks.length > 0) {
                    html += '<div class="debug-log-section">';
                    html += '<strong>Mount Point Checks:</strong>';
                    html += '<pre>';
                    log.mount_checks.forEach(mount => {
                        html += `Path: ${mount.path}\n`;
                        html += `  Exists: ${mount.exists ? 'Yes' : 'No'}\n`;
                        html += `  Accessible: ${mount.accessible ? 'Yes' : 'No'}\n`;
                        if (mount.percent !== undefined) {
                            html += `  Usage: ${mount.percent}%\n`;
                        }
                        if (mount.error) {
                            html += `  Error: ${mount.error}\n`;
                        }
                        if (mount.note) {
                            html += `  Note: ${mount.note}\n`;
                        }
                        html += '\n';
                    });
                    html += '</pre>';
                    html += '</div>';
                }
            }
            
            // Show errors if any
            if (log.errors && log.errors.length > 0) {
                html += '<div class="debug-log-section">';
                html += '<strong class="debug-log-error">Errors:</strong>';
                html += '<pre>';
                log.errors.forEach(error => {
                    html += `${error}\n`;
                });
                html += '</pre>';
                html += '</div>';
            }
            
            html += '</div>';
        });
        html += '</div>';
        
        logsDiv.innerHTML = html;
    } catch (error) {
        console.error('Error loading System debug logs:', error);
        const logsDiv = document.getElementById('systemDebugLogs');
        if (logsDiv) {
            logsDiv.innerHTML = `<div class="debug-error">Error loading debug logs: ${error.message}<br/><button class="btn btn-small btn-primary" onclick="loadSystemDebugLogs()">Retry</button></div>`;
        }
        showError(`Failed to load System debug logs: ${error.message}`);
    }
}

async function testSystemCollection() {
    const testBtn = document.getElementById('testSystemBtn');
    const originalText = testBtn.textContent;
    setButtonLoading(testBtn, true);
    
    try {
        const response = await fetch(`${API_BASE}/debug/system/test`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            showSuccess(`Collection test successful! Collected ${data.result_keys ? data.result_keys.length : 0} data keys.`);
        } else {
            showError(`Collection test failed: ${data.error || 'Unknown error'}`);
        }
        
        // Refresh logs after test
        await loadSystemDebugLogs();
    } catch (error) {
        console.error('Error testing System collection:', error);
        showError(`Error testing collection: ${error.message}`);
    } finally {
        setButtonLoading(testBtn, false, originalText);
    }
}

async function clearSystemDebugLogs() {
    const confirmed = await showConfirm('Clear System debug logs? This cannot be undone.', 'Clear Logs');
    if (!confirmed) {
        return;
    }
    
    // Note: This would require a backend endpoint to clear logs
    // For now, we'll just reload which will show current logs
    document.getElementById('systemDebugLogs').innerHTML = '<div class="debug-empty">Debug logs cleared. New collections will populate logs.</div>';
    showSuccess('System debug logs cleared');
}

// Keyboard Shortcuts
// About Dialog Functions
function openAboutDialog() {
    const aboutModal = document.getElementById('aboutModal');
    if (aboutModal) {
        aboutModal.style.display = 'block';
        // Focus the close button for accessibility
        setTimeout(() => {
            const closeBtn = document.getElementById('aboutCloseBtn');
            if (closeBtn) closeBtn.focus();
        }, 50);
    }
}

function closeAboutDialog() {
    const aboutModal = document.getElementById('aboutModal');
    if (aboutModal) {
        aboutModal.style.display = 'none';
    }
}

function setupKeyboardShortcuts() {
    // Escape key closes modals
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const slideModal = document.getElementById('slideModal');
            const confirmModal = document.getElementById('confirmModal');
            const aboutModal = document.getElementById('aboutModal');
            
            if (slideModal && slideModal.style.display === 'block') {
                closeSlideModal();
                e.preventDefault();
            } else if (confirmModal && confirmModal.style.display !== 'none') {
                confirmModal.style.display = 'none';
                e.preventDefault();
            } else if (aboutModal && aboutModal.style.display !== 'none') {
                closeAboutDialog();
                e.preventDefault();
            }
        }
        
        // Enter key submits form if modal is open, or closes About/Confirm dialogs
        if (e.key === 'Enter') {
            const slideModal = document.getElementById('slideModal');
            const aboutModal = document.getElementById('aboutModal');
            const confirmModal = document.getElementById('confirmModal');
            
            if (slideModal && slideModal.style.display === 'block' && e.ctrlKey) {
                const form = document.getElementById('slideForm');
                if (form && document.activeElement.tagName !== 'BUTTON') {
                    form.dispatchEvent(new Event('submit', { cancelable: true }));
                    e.preventDefault();
                }
            } else if (aboutModal && aboutModal.style.display !== 'none') {
                const aboutBtn = document.getElementById('aboutCloseBtn');
                if (document.activeElement === aboutBtn || e.target === aboutModal) {
                    closeAboutDialog();
                    e.preventDefault();
                }
            } else if (confirmModal && confirmModal.style.display !== 'none') {
                const confirmYes = document.getElementById('confirmYes');
                if (document.activeElement === confirmYes) {
                    confirmYes.click();
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



