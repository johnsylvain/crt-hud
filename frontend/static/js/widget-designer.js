// Widget Designer JavaScript
'use strict';

console.log('Widget designer: Script file loaded and executing - line 3');

// API_BASE is already defined in app.js (loaded before this script)
// Check if it exists, otherwise define it (shouldn't happen, but safe fallback)
if (typeof API_BASE === 'undefined') {
    window.API_BASE = '/api';
}

// State
let currentSlide = null;
let widgets = [];
let selectedWidget = null;
let layoutAreas = [{ id: 'default', grid_area: '1 / 1 / 2 / 2' }];
let widgetTypes = {};
let testData = null;

// Initialize widget designer when DOM is ready
// Use both DOMContentLoaded and window.onload as fallbacks
function initWidgetDesignerOnReady() {
    console.log('Widget designer: initWidgetDesignerOnReady called, readyState:', document.readyState);
    
    function doInit() {
        console.log('Widget designer: Executing doInit');
        try {
            initWidgetDesigner();
            // Set up event listeners with delay to ensure elements are ready
            setTimeout(() => {
                console.log('Widget designer: Setting up delayed event listeners');
                setupDesignerEventListeners();
            }, 500);
        } catch (error) {
            console.error('Widget designer: Error during initialization:', error);
            console.error(error.stack);
        }
    }
    
    if (document.readyState === 'loading') {
        console.log('Widget designer: DOM still loading, waiting for DOMContentLoaded');
        document.addEventListener('DOMContentLoaded', doInit);
    } else {
        console.log('Widget designer: DOM ready, initializing with delay');
        // DOM is ready, but wait a bit to ensure all scripts have loaded
        setTimeout(doInit, 200);
    }
    
    // Also listen for window load as backup
    window.addEventListener('load', () => {
        console.log('Widget designer: Window load event fired');
        // Double-check if initialization happened
        const btn = document.getElementById('newCustomSlideBtn');
        if (btn && !btn.hasAttribute('data-listener-attached')) {
            console.log('Widget designer: Button found on load, setting up listeners');
            setupDesignerEventListeners();
        }
    });
}

// Execute immediately - this should log even if DOM isn't ready
console.log('Widget designer: Script file loaded and executing');

// Use event delegation from document to handle clicks - works even if script loads late
// This MUST be set up immediately when script loads, before DOMContentLoaded
(function() {
    console.log('Widget designer: Setting up global event delegation');
    
    function handleNewCustomSlideClick(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('Widget designer: newCustomSlideBtn clicked (delegation handler)');
        
        // Check if function is available (it should be hoisted, but double-check)
        if (typeof window.startNewCustomSlide === 'function') {
            console.log('Widget designer: Calling window.startNewCustomSlide');
            try {
                window.startNewCustomSlide();
            } catch (error) {
                console.error('Widget designer: Error in startNewCustomSlide:', error);
                alert('Error starting custom slide: ' + error.message);
            }
        } else if (typeof startNewCustomSlide === 'function') {
            console.log('Widget designer: Calling startNewCustomSlide (not on window yet)');
            try {
                startNewCustomSlide();
            } catch (error) {
                console.error('Widget designer: Error in startNewCustomSlide:', error);
                alert('Error starting custom slide: ' + error.message);
            }
        } else {
            console.error('Widget designer: startNewCustomSlide function not found');
            alert('Widget designer is still loading. Please refresh the page and try again.');
        }
        return false;
    }
    
    function handleLoadCustomSlideClick(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('Widget designer: loadCustomSlideBtn clicked (delegation handler)');
        
        if (typeof window.loadExistingCustomSlide === 'function') {
            try {
                window.loadExistingCustomSlide();
            } catch (error) {
                console.error('Widget designer: Error in loadExistingCustomSlide:', error);
                alert('Error loading custom slide: ' + error.message);
            }
        } else if (typeof loadExistingCustomSlide === 'function') {
            try {
                loadExistingCustomSlide();
            } catch (error) {
                console.error('Widget designer: Error in loadExistingCustomSlide:', error);
                alert('Error loading custom slide: ' + error.message);
            }
        } else {
            console.error('Widget designer: loadExistingCustomSlide function not found');
            alert('Widget designer is still loading. Please refresh the page and try again.');
        }
        return false;
    }
    
    // Set up event delegation immediately
    document.addEventListener('click', function(e) {
        const target = e.target;
        if (!target) return;
        
        // Check for newCustomSlideBtn
        if (target.id === 'newCustomSlideBtn' || (target.closest && target.closest('#newCustomSlideBtn'))) {
            handleNewCustomSlideClick(e);
            return;
        }
        
        // Check for loadCustomSlideBtn
        if (target.id === 'loadCustomSlideBtn' || (target.closest && target.closest('#loadCustomSlideBtn'))) {
            handleLoadCustomSlideClick(e);
            return;
        }
    }, true); // Use capture phase
    
    console.log('Widget designer: Global event delegation set up');
})();

// Functions will be defined below - function declarations are hoisted, so they're available immediately
// We'll assign them to window right after they're defined to ensure they're globally accessible

// Call initialization
try {
    initWidgetDesignerOnReady();
} catch (error) {
    console.error('Widget designer: Error during initialization:', error);
    console.error(error.stack);
}

// Initialize Widget Designer
function initWidgetDesigner() {
    console.log('Widget designer: Initializing');
    
    // Load widget types
    loadWidgetTypes();
    
    // Setup event listeners
    setupDesignerEventListeners();
    
    // Setup canvas
    setupCanvas();
}

// Setup event listeners
function setupDesignerEventListeners() {
    console.log('Widget designer: setupDesignerEventListeners called');
    
    // New custom slide button
    const newCustomSlideBtn = document.getElementById('newCustomSlideBtn');
    if (newCustomSlideBtn) {
        console.log('Widget designer: Found newCustomSlideBtn, attaching listener');
        
        // Mark button as having listener attached
        newCustomSlideBtn.setAttribute('data-listener-attached', 'true');
        
        // Remove any existing listeners by cloning and replacing
        const newBtn = newCustomSlideBtn.cloneNode(true);
        newCustomSlideBtn.parentNode.replaceChild(newBtn, newCustomSlideBtn);
        
        // Add click handler
        newBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Widget designer: newCustomSlideBtn clicked!');
            try {
                startNewCustomSlide();
            } catch (error) {
                console.error('Widget designer: Error in startNewCustomSlide:', error);
                alert('Error starting custom slide: ' + error.message);
            }
            return false;
        });
        
        // Also add onclick as absolute fallback
        newBtn.onclick = function(e) {
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }
            console.log('Widget designer: newCustomSlideBtn onclick handler fired');
            try {
                startNewCustomSlide();
            } catch (error) {
                console.error('Widget designer: Error in startNewCustomSlide (onclick):', error);
                alert('Error starting custom slide: ' + error.message);
            }
            return false;
        };
        
        console.log('Widget designer: Event listeners attached to newCustomSlideBtn');
    } else {
        console.warn('Widget designer: newCustomSlideBtn not found in DOM');
        console.warn('Widget designer: Available buttons:', document.querySelectorAll('button').length);
        // Try again after a longer delay
        setTimeout(() => {
            const retryBtn = document.getElementById('newCustomSlideBtn');
            if (retryBtn) {
                console.log('Widget designer: Found newCustomSlideBtn on retry');
                retryBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('Widget designer: newCustomSlideBtn clicked (retry handler)');
                    startNewCustomSlide();
                    return false;
                });
                retryBtn.setAttribute('data-listener-attached', 'true');
            } else {
                console.error('Widget designer: newCustomSlideBtn still not found after retry');
            }
        }, 1000);
    }
    
    // Load existing slide button
    const loadCustomSlideBtn = document.getElementById('loadCustomSlideBtn');
    if (loadCustomSlideBtn) {
        loadCustomSlideBtn.addEventListener('click', () => {
            loadExistingCustomSlide();
        });
    }
    
    // Designer action buttons
    const designerPreviewBtn = document.getElementById('designerPreviewBtn');
    if (designerPreviewBtn) {
        designerPreviewBtn.addEventListener('click', () => {
            generatePreview();
        });
    }
    
    const designerSaveBtn = document.getElementById('designerSaveBtn');
    if (designerSaveBtn) {
        designerSaveBtn.addEventListener('click', () => {
            saveCustomSlide();
        });
    }
    
    const designerCancelBtn = document.getElementById('designerCancelBtn');
    if (designerCancelBtn) {
        designerCancelBtn.addEventListener('click', () => {
            cancelDesigner();
        });
    }
    
    // Setup drag-and-drop for palette items
    setupPaletteDragAndDrop();
    
    // Setup canvas drop zone
    setupCanvasDropZone();
    
    // Setup collapsible API section
    setupCollapsibleAPISection();
    
    // Palette items (widget types) - also allow click as fallback
    const paletteItems = document.querySelectorAll('.palette-item');
    paletteItems.forEach(item => {
        item.addEventListener('click', (e) => {
            // Only handle click if not dragging
            if (!e.target.classList.contains('dragging')) {
                const widgetType = item.getAttribute('data-widget-type');
                addWidgetToCanvas(widgetType);
            }
        });
    });
    
    // API test button
    const testApiBtn = document.getElementById('testApiBtn');
    if (testApiBtn) {
        testApiBtn.addEventListener('click', () => {
            testAPI();
        });
    }
    
    // Load test data button
    const loadTestDataBtn = document.getElementById('loadTestDataBtn');
    if (loadTestDataBtn) {
        loadTestDataBtn.addEventListener('click', () => {
            useTestDataInPreview();
        });
    }
    
    // Toggle grid button
    const toggleGridBtn = document.getElementById('toggleGridBtn');
    if (toggleGridBtn) {
        toggleGridBtn.addEventListener('click', () => {
            toggleCanvasGrid();
        });
    }
    
    // Preview canvas button
    const previewCanvasBtn = document.getElementById('previewCanvasBtn');
    if (previewCanvasBtn) {
        previewCanvasBtn.addEventListener('click', () => {
            generatePreview();
        });
    }
    
    // Clear canvas button
    const clearCanvasBtn = document.getElementById('clearCanvasBtn');
    if (clearCanvasBtn) {
        clearCanvasBtn.addEventListener('click', () => {
            if (confirm('Clear all widgets from canvas?')) {
                clearCanvas();
            }
        });
    }
}

// Load widget types from API
async function loadWidgetTypes() {
    try {
        const response = await fetch(`${API_BASE}/widgets/types`);
        const data = await response.json();
        widgetTypes = data.widget_types || {};
    } catch (error) {
        console.error('Error loading widget types:', error);
        showError('Failed to load widget types');
    }
}

// Setup canvas
function setupCanvas() {
    const canvas = document.getElementById('previewCanvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    // Set canvas size (240p for better readability)
    canvas.width = 320;
    canvas.height = 240;
    
    // Fill with black background
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
}

// Start new custom slide  
function startNewCustomSlide() {
    console.log('startNewCustomSlide called (actual function)');
    
    // Replace the window placeholder with this actual function
    window.startNewCustomSlide = startNewCustomSlide;
    
    try {
        currentSlide = {
            type: 'custom',
            title: 'Custom Dashboard',
            duration: 10,
            layout: {
                type: 'mixed',
                grid_areas: layoutAreas
            },
            widgets: [],
            api_config: null
        };
        
        widgets = [];
        selectedWidget = null;
        testData = null;
        
        // Show designer UI
        const container = document.getElementById('widgetDesignerContainer');
        const emptyState = document.getElementById('designerEmptyState');
        
        if (!container) {
            console.error('widgetDesignerContainer not found');
            alert('Widget designer container not found. Please refresh the page.');
            return;
        }
        
        if (!emptyState) {
            console.error('designerEmptyState not found');
            alert('Designer empty state not found. Please refresh the page.');
            return;
        }
        
        container.style.display = 'block';
        emptyState.style.display = 'none';
        
        // Reset form
        resetDesignerForm();
        updateCanvas();
        updatePropertyPanel();
        
        console.log('startNewCustomSlide completed successfully');
    } catch (error) {
        console.error('Error in startNewCustomSlide:', error);
        alert('Error starting custom slide: ' + error.message);
    }
}

// Expose startNewCustomSlide to window immediately after definition
window.startNewCustomSlide = startNewCustomSlide;

// Load existing custom slide
async function loadExistingCustomSlide() {
    
    try {
        const response = await fetch(`${API_BASE}/slides`);
        const data = await response.json();
        const customSlides = (data.slides || []).filter(s => s.type === 'custom');
        
        if (customSlides.length === 0) {
            alert('No custom slides found');
            return;
        }
        
        // Show selection dialog (simplified - just pick first one)
        // TODO: Add proper selection dialog
        if (customSlides.length > 0) {
            const slide = customSlides[0];
            loadCustomSlide(slide);
        }
    } catch (error) {
        console.error('Error loading custom slides:', error);
        showError('Failed to load custom slides');
    }
}

// Expose loadExistingCustomSlide to window immediately after definition
window.loadExistingCustomSlide = loadExistingCustomSlide;

// Load custom slide configuration
function loadCustomSlide(slide) {
    currentSlide = { ...slide };
    widgets = slide.widgets || [];
    layoutAreas = slide.layout?.grid_areas || [{ id: 'default', grid_area: '1 / 1 / 2 / 2' }];
    
    // Update form
    const titleInput = document.getElementById('designerSlideTitle');
    const durationInput = document.getElementById('designerSlideDuration');
    if (titleInput) titleInput.value = slide.title || '';
    if (durationInput) durationInput.value = slide.duration || 10;
    
    // Update API config
    if (slide.api_config) {
        updateAPIConfigForm(slide.api_config);
    }
    
    // Show designer UI
    const container = document.getElementById('widgetDesignerContainer');
    const emptyState = document.getElementById('designerEmptyState');
    if (container && emptyState) {
        container.style.display = 'block';
        emptyState.style.display = 'none';
    }
    
    updateCanvas();
    updatePropertyPanel();
}

// Reset designer form
function resetDesignerForm() {
    const titleInput = document.getElementById('designerSlideTitle');
    const durationInput = document.getElementById('designerSlideDuration');
    if (titleInput) titleInput.value = 'Custom Dashboard';
    if (durationInput) durationInput.value = 10;
    
    // Reset API config
    const endpointInput = document.getElementById('apiEndpoint');
    const methodSelect = document.getElementById('apiMethod');
    const headersTextarea = document.getElementById('apiHeaders');
    const bodyTextarea = document.getElementById('apiBody');
    const dataPathInput = document.getElementById('apiDataPath');
    const refreshInput = document.getElementById('apiRefreshInterval');
    
    if (endpointInput) endpointInput.value = '';
    if (methodSelect) methodSelect.value = 'GET';
    if (headersTextarea) headersTextarea.value = '';
    if (bodyTextarea) bodyTextarea.value = '';
    if (dataPathInput) dataPathInput.value = '$';
    if (refreshInput) refreshInput.value = 30;
    
    // Clear test result
    const testResult = document.getElementById('apiTestResult');
    if (testResult) {
        testResult.style.display = 'none';
        testResult.innerHTML = '';
    }
}

// Setup drag-and-drop from palette
function setupPaletteDragAndDrop() {
    const paletteItems = document.querySelectorAll('.palette-item[draggable="true"]');
    paletteItems.forEach(item => {
        item.addEventListener('dragstart', (e) => {
            const widgetType = item.getAttribute('data-widget-type');
            e.dataTransfer.effectAllowed = 'copy';
            e.dataTransfer.setData('text/plain', widgetType);
            item.classList.add('dragging');
        });
        
        item.addEventListener('dragend', (e) => {
            item.classList.remove('dragging');
        });
    });
}

// Setup canvas drop zone
function setupCanvasDropZone() {
    const canvasDropZone = document.getElementById('canvasDropZone');
    const canvasContainer = document.getElementById('canvasContainer');
    
    if (!canvasDropZone || !canvasContainer) return;
    
    // Allow drop
    canvasDropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
        canvasDropZone.classList.add('drag-over');
    });
    
    canvasDropZone.addEventListener('dragleave', (e) => {
        // Only remove if actually leaving the drop zone
        if (!canvasContainer.contains(e.relatedTarget)) {
            canvasDropZone.classList.remove('drag-over');
        }
    });
    
    // Handle drop
    canvasDropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        canvasDropZone.classList.remove('drag-over');
        
        const widgetType = e.dataTransfer.getData('text/plain');
        if (widgetType) {
            // Get drop position relative to canvas
            const rect = canvasContainer.getBoundingClientRect();
            const canvas = document.getElementById('previewCanvas');
            if (!canvas) return;
            
            const canvasRect = canvas.getBoundingClientRect();
            const x = Math.max(0, Math.min(canvas.width - 50, e.clientX - canvasRect.left));
            const y = Math.max(0, Math.min(canvas.height - 20, e.clientY - canvasRect.top));
            
            addWidgetToCanvasAtPosition(widgetType, x, y);
        }
    });
}

// Setup collapsible API section
function setupCollapsibleAPISection() {
    const apiHeader = document.querySelector('.designer-api-section h3.collapsible-header');
    const apiContent = document.getElementById('apiConfigContent');
    
    if (!apiHeader || !apiContent) return;
    
    // Initialize as expanded by default
    if (apiHeader.classList.contains('expanded')) {
        apiContent.style.display = 'block';
        const icon = apiHeader.querySelector('.collapse-icon');
        if (icon) {
            icon.textContent = '▼';
        }
    }
    
    apiHeader.addEventListener('click', () => {
        const isExpanded = apiHeader.classList.contains('expanded');
        apiContent.style.display = isExpanded ? 'none' : 'block';
        apiHeader.classList.toggle('expanded', !isExpanded);
        
        const icon = apiHeader.querySelector('.collapse-icon');
        if (icon) {
            icon.textContent = isExpanded ? '▶' : '▼';
        }
    });
}

// Add widget to canvas at specific position
function addWidgetToCanvasAtPosition(widgetType, x, y) {
    if (!currentSlide) {
        startNewCustomSlide();
    }
    
    // Generate widget ID
    const widgetId = `widget_${Date.now()}`;
    
    // Create widget based on type
    const widget = {
        id: widgetId,
        type: widgetType,
        container: 'default',
        position: { x: Math.round(x), y: Math.round(y) },
        ...getDefaultWidgetConfig(widgetType)
    };
    
    widgets.push(widget);
    selectedWidget = widget;
    
    updateCanvas();
    updateCanvasOverlay();
    updatePropertyPanel();
}

// Add widget to canvas (center by default)
function addWidgetToCanvas(widgetType) {
    const canvas = document.getElementById('previewCanvas');
    if (!canvas) {
        // Fallback to center
        addWidgetToCanvasAtPosition(widgetType, 160, 140);
        return;
    }
    
    // Add at center of canvas
    addWidgetToCanvasAtPosition(widgetType, canvas.width / 2 - 25, canvas.height / 2 - 10);
}

// Get default widget configuration
function getDefaultWidgetConfig(widgetType) {
    switch (widgetType) {
        case 'text':
            return {
                data_binding: { path: '', template: '', format: null },
                style: { font_size: 'medium', color: 'text', align: 'left' }
            };
        case 'progress':
            return {
                data_binding: { path: '', min: 0, max: 100 },
                style: { width: 30, show_label: true, label_template: '{value:.1f}%', color: 'text' }
            };
        case 'chart':
            return {
                chart_config: { type: 'line', data_path: '' },
                width: 200,
                height: 150
            };
        case 'conditional':
            return {
                condition: { operator: 'exists', path: '' },
                widget: { type: 'text', data_binding: { path: '' } }
            };
        case 'list':
            return {
                list_config: {
                    array_path: '',  // Path to array (e.g., "items", "data.results")
                    iteration_mode: 'all',  // 'all', 'first', 'last', 'index'
                    max_items: 10,  // Maximum items to show when mode is 'all'
                    start_index: 0,  // Start index for custom range
                    item_index: 0  // Specific index for 'index' mode
                },
                item_template: {  // Widget template to repeat for each item
                    type: 'text',
                    data_binding: { path: '', template: '{name}' },
                    position: { x: 0, y: 0 }
                },
                spacing: 25  // Vertical spacing between items
            };
        default:
            return {};
    }
}

// Update canvas - renders preview and overlay
function updateCanvas() {
    // Update the visual overlay first
    updateCanvasOverlay();
    
    // Then trigger preview render
    generatePreview();
}

// Update canvas overlay - shows interactive widget placeholders
function updateCanvasOverlay() {
    const canvasWidgets = document.getElementById('canvasWidgets');
    const dropZone = document.getElementById('canvasDropZone');
    
    if (!canvasWidgets || !dropZone) return;
    
    // Hide drop zone message if widgets exist
    const dropMessage = dropZone.querySelector('.drop-zone-message');
    if (dropMessage) {
        dropMessage.style.display = widgets.length > 0 ? 'none' : 'block';
    }
    
    // Clear existing overlay widgets
    canvasWidgets.innerHTML = '';
    
    // Create overlay items for each widget
    widgets.forEach(widget => {
        const widgetEl = createCanvasWidgetElement(widget);
        canvasWidgets.appendChild(widgetEl);
    });
    
    // Setup drag for canvas widgets
    setupCanvasWidgetDrag();
}

// Create canvas widget overlay element
function createCanvasWidgetElement(widget) {
    const canvas = document.getElementById('previewCanvas');
    if (!canvas) return document.createElement('div');
    
    const div = document.createElement('div');
    div.className = 'canvas-widget-item';
    div.dataset.widgetId = widget.id;
    
    if (selectedWidget && selectedWidget.id === widget.id) {
        div.classList.add('selected');
    }
    
    // Position relative to canvas (320x240)
    const x = widget.position?.x || 10;
    const y = widget.position?.y || 10;
    const width = widget.width || 100;
    const height = widget.height || 30;
    
    // Convert canvas coordinates to percentage
    const percentX = (x / canvas.width) * 100;
    const percentY = (y / canvas.height) * 100;
    const percentWidth = (width / canvas.width) * 100;
    const percentHeight = (height / canvas.height) * 100;
    
    div.style.left = `${percentX}%`;
    div.style.top = `${percentY}%`;
    div.style.width = `${percentWidth}%`;
    div.style.height = `${percentHeight}%`;
    
    // Widget label
    const label = document.createElement('div');
    label.className = 'widget-label';
    label.textContent = `${widget.type} (${widget.id})`;
    div.appendChild(label);
    
    // Resize handle
    const resizeHandle = document.createElement('div');
    resizeHandle.className = 'widget-resize-handle';
    div.appendChild(resizeHandle);
    
    // Click to select
    div.addEventListener('click', (e) => {
        e.stopPropagation();
        selectWidget(widget);
    });
    
    return div;
}

// Setup drag for canvas widgets (repositioning)
function setupCanvasWidgetDrag() {
    const widgetItems = document.querySelectorAll('.canvas-widget-item');
    widgetItems.forEach(item => {
        let isDragging = false;
        let startX, startY, startLeft, startTop;
        
        item.addEventListener('mousedown', (e) => {
            // Don't start drag if clicking resize handle
            if (e.target.classList.contains('widget-resize-handle')) {
                return;
            }
            
            isDragging = true;
            item.classList.add('dragging');
            
            const widgetId = item.dataset.widgetId;
            const widget = widgets.find(w => w.id === widgetId);
            if (!widget) return;
            
            const canvas = document.getElementById('previewCanvas');
            if (!canvas) return;
            
            const rect = canvas.getBoundingClientRect();
            startX = e.clientX - rect.left;
            startY = e.clientY - rect.top;
            startLeft = widget.position?.x || 0;
            startTop = widget.position?.y || 0;
            
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            
            const widgetId = item.dataset.widgetId;
            const widget = widgets.find(w => w.id === widgetId);
            if (!widget) return;
            
            const canvas = document.getElementById('previewCanvas');
            if (!canvas) return;
            
            const rect = canvas.getBoundingClientRect();
            const newX = e.clientX - rect.left;
            const newY = e.clientY - rect.top;
            
            // Calculate new position
            const deltaX = newX - startX;
            const deltaY = newY - startY;
            
            const newLeft = Math.max(0, Math.min(canvas.width - 50, startLeft + deltaX));
            const newTop = Math.max(0, Math.min(canvas.height - 20, startTop + deltaY));
            
            // Update widget position
            if (!widget.position) widget.position = {};
            widget.position.x = Math.round(newLeft);
            widget.position.y = Math.round(newTop);
            
            // Update overlay visual position
            const percentX = (widget.position.x / canvas.width) * 100;
            const percentY = (widget.position.y / canvas.height) * 100;
            item.style.left = `${percentX}%`;
            item.style.top = `${percentY}%`;
        });
        
        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                item.classList.remove('dragging');
                
                // Update preview after drag
                generatePreview();
                updatePropertyPanel();
            }
        });
    });
}

// Select widget
function selectWidget(widget) {
    selectedWidget = widget;
    
    // Update overlay to show selection
    document.querySelectorAll('.canvas-widget-item').forEach(item => {
        item.classList.toggle('selected', item.dataset.widgetId === widget.id);
    });
    
    updatePropertyPanel();
}

// Update property panel
function updatePropertyPanel() {
    const panelContent = document.getElementById('propertyPanelContent');
    if (!panelContent) return;
    
    if (!selectedWidget) {
        panelContent.innerHTML = '<div class="property-placeholder">Select a widget or create a new one to edit properties</div>';
        return;
    }
    
    // Generate property editor based on widget type
    panelContent.innerHTML = generatePropertyEditor(selectedWidget);
    
    // Setup property editor event listeners
    setupPropertyEditorListeners();
}

// Generate property editor HTML
function generatePropertyEditor(widget) {
    const type = widget.type || 'text';
    let html = `<div class="property-group">
        <label>Widget ID:</label>
        <input type="text" value="${widget.id}" readonly>
    </div>
    <div class="property-group">
        <label>Widget Type:</label>
        <input type="text" value="${type}" readonly>
    </div>`;
    
    switch (type) {
        case 'text':
            html += generateTextWidgetEditor(widget);
            break;
        case 'progress':
            html += generateProgressWidgetEditor(widget);
            break;
        case 'chart':
            html += generateChartWidgetEditor(widget);
            break;
        case 'conditional':
            html += generateConditionalWidgetEditor(widget);
            break;
        case 'list':
            html += generateListWidgetEditor(widget);
            break;
    }
    
    // Position editor
    html += `<div class="property-group">
        <label>Position X:</label>
        <input type="number" id="propPosX" value="${widget.position?.x || 0}" min="0">
        <label>Position Y:</label>
        <input type="number" id="propPosY" value="${widget.position?.y || 0}" min="0">
    </div>`;
    
    // Container selector
    html += `<div class="property-group">
        <label>Container:</label>
        <select id="propContainer">
            ${layoutAreas.map(area => 
                `<option value="${area.id}" ${widget.container === area.id ? 'selected' : ''}>${area.id}</option>`
            ).join('')}
        </select>
    </div>`;
    
    // Actions
    html += `<div class="property-group">
        <div class="property-actions">
            <button type="button" class="btn btn-primary" id="propSaveBtn">Save Changes</button>
            <button type="button" class="btn btn-secondary" id="propDeleteBtn">Delete Widget</button>
        </div>
    </div>`;
    
    return html;
}

// Generate text widget editor
function generateTextWidgetEditor(widget) {
    const dataBinding = widget.data_binding || {};
    const style = widget.style || {};
    
    return `
    <div class="property-group">
        <label>Data Field:</label>
        ${createDataPathSelector('propTextPath', dataBinding.path || '', 'e.g., cpu.percent, temperature, status')}
        <small>📍 Path to data value. Click 📂 to browse available fields from test data.</small>
        <button type="button" class="btn btn-small btn-secondary" id="browseTextDataBtn" style="margin-top: 4px;">Browse Available Data</button>
    </div>
    <div class="property-group">
        <label>Template:</label>
        <textarea id="propTextTemplate" rows="2" placeholder="e.g., CPU: {value}%">${dataBinding.template || ''}</textarea>
        <small>Template string with {value} placeholder</small>
    </div>
    <div class="property-group">
        <label>Format:</label>
        <select id="propTextFormat">
            <option value="">None</option>
            <option value="bytes" ${dataBinding.format === 'bytes' ? 'selected' : ''}>Bytes</option>
            <option value="duration" ${dataBinding.format === 'duration' ? 'selected' : ''}>Duration</option>
            <option value="percentage" ${dataBinding.format === 'percentage' ? 'selected' : ''}>Percentage</option>
            <option value="integer" ${dataBinding.format === 'integer' ? 'selected' : ''}>Integer</option>
            <option value="float" ${dataBinding.format === 'float' ? 'selected' : ''}>Float</option>
        </select>
    </div>
    <div class="property-group">
        <label>Font Size:</label>
        <select id="propTextFontSize">
            <option value="large" ${style.font_size === 'large' ? 'selected' : ''}>Large</option>
            <option value="medium" ${style.font_size === 'medium' ? 'selected' : ''}>Medium</option>
            <option value="small" ${style.font_size === 'small' ? 'selected' : ''}>Small</option>
            <option value="tiny" ${style.font_size === 'tiny' ? 'selected' : ''}>Tiny</option>
        </select>
    </div>
    <div class="property-group">
        <label>Color:</label>
        <select id="propTextColor">
            <option value="text" ${style.color === 'text' ? 'selected' : ''}>Text (White)</option>
            <option value="text_secondary" ${style.color === 'text_secondary' ? 'selected' : ''}>Secondary (Gray)</option>
            <option value="text_muted" ${style.color === 'text_muted' ? 'selected' : ''}>Muted (Dark Gray)</option>
            <option value="accent" ${style.color === 'accent' ? 'selected' : ''}>Accent</option>
        </select>
    </div>
    <div class="property-group">
        <label>Align:</label>
        <select id="propTextAlign">
            <option value="left" ${style.align === 'left' ? 'selected' : ''}>Left</option>
            <option value="center" ${style.align === 'center' ? 'selected' : ''}>Center</option>
            <option value="right" ${style.align === 'right' ? 'selected' : ''}>Right</option>
        </select>
    </div>
    `;
}

// Generate progress widget editor
function generateProgressWidgetEditor(widget) {
    const dataBinding = widget.data_binding || {};
    const style = widget.style || {};
    
    return `
    <div class="property-group">
        <label>Data Path:</label>
        <input type="text" id="propProgressPath" value="${dataBinding.path || ''}" placeholder="e.g., cpu.percent">
    </div>
    <div class="property-group">
        <label>Min Value:</label>
        <input type="number" id="propProgressMin" value="${dataBinding.min || 0}">
    </div>
    <div class="property-group">
        <label>Max Value:</label>
        <input type="number" id="propProgressMax" value="${dataBinding.max || 100}">
    </div>
    <div class="property-group">
        <label>Bar Width:</label>
        <input type="number" id="propProgressWidth" value="${style.width || 30}" min="10" max="50">
    </div>
    <div class="property-group">
        <label>Show Label:</label>
        <input type="checkbox" id="propProgressShowLabel" ${style.show_label !== false ? 'checked' : ''}>
    </div>
    <div class="property-group">
        <label>Label Template:</label>
        <input type="text" id="propProgressLabelTemplate" value="${style.label_template || '{value:.1f}%'}" placeholder="{value:.1f}%">
    </div>
    `;
}

// Generate chart widget editor
function generateChartWidgetEditor(widget) {
    const chartConfig = widget.chart_config || {};
    
    return `
    <div class="property-group">
        <label>Chart Type:</label>
        <select id="propChartType">
            <option value="line" ${chartConfig.type === 'line' ? 'selected' : ''}>Line</option>
            <option value="bar" ${chartConfig.type === 'bar' ? 'selected' : ''}>Bar</option>
        </select>
    </div>
    <div class="property-group">
        <label>Data Path:</label>
        <input type="text" id="propChartDataPath" value="${chartConfig.data_path || ''}" placeholder="e.g., history.temperature">
    </div>
    <div class="property-group">
        <label>Width:</label>
        <input type="number" id="propChartWidth" value="${widget.width || 200}" min="50" max="300">
    </div>
    <div class="property-group">
        <label>Height:</label>
        <input type="number" id="propChartHeight" value="${widget.height || 150}" min="50" max="250">
    </div>
    `;
}

// Generate conditional widget editor
function generateConditionalWidgetEditor(widget) {
    const condition = widget.condition || {};
    const childWidget = widget.widget || {};
    
    return `
    <div class="property-group">
        <label>Condition Operator:</label>
        <select id="propConditionOp">
            <option value="==" ${condition.operator === '==' ? 'selected' : ''}>Equals (==)</option>
            <option value="!=" ${condition.operator === '!=' ? 'selected' : ''}>Not Equals (!=)</option>
            <option value=">" ${condition.operator === '>' ? 'selected' : ''}>Greater Than (>)</option>
            <option value="<" ${condition.operator === '<' ? 'selected' : ''}>Less Than (<)</option>
            <option value=">=" ${condition.operator === '>=' ? 'selected' : ''}>Greater or Equal (>=)</option>
            <option value="<=" ${condition.operator === '<=' ? 'selected' : ''}>Less or Equal (<=)</option>
            <option value="exists" ${condition.operator === 'exists' ? 'selected' : ''}>Exists</option>
            <option value="contains" ${condition.operator === 'contains' ? 'selected' : ''}>Contains</option>
        </select>
    </div>
    <div class="property-group">
        <label>Data Path:</label>
        ${createDataPathSelector('propConditionPath', condition.path || '', 'e.g., status')}
    </div>
    <div class="property-group">
        <label>Compare Value:</label>
        <input type="text" id="propConditionValue" value="${condition.value || ''}" placeholder="e.g., active">
    </div>
    <div class="property-group">
        <label>Child Widget Type:</label>
        <select id="propConditionChildType">
            <option value="text" ${childWidget.type === 'text' ? 'selected' : ''}>Text</option>
            <option value="progress" ${childWidget.type === 'progress' ? 'selected' : ''}>Progress</option>
            <option value="chart" ${childWidget.type === 'chart' ? 'selected' : ''}>Chart</option>
        </select>
    </div>
    `;
}

// Generate List widget editor - simple iteration over arrays
function generateListWidgetEditor(widget) {
    const listConfig = widget.list_config || {};
    const itemTemplate = widget.item_template || { type: 'text', data_binding: { path: '', template: '{name}' } };
    const spacing = widget.spacing || 25;
    
    return `
    <div class="property-group">
        <label><strong>📋 List Configuration</strong></label>
        <p style="font-size: 12px; color: #666; margin: 4px 0;">This widget repeats a template for each item in a list/array.</p>
    </div>
    
    <div class="property-group">
        <label>Array/List Path:</label>
        ${createDataPathSelector('propListArrayPath', listConfig.array_path || '', 'e.g., items, data.results, users')}
        <small>📍 Path to the array/list in your data (e.g., "items", "data.results")</small>
        <button type="button" class="btn btn-small btn-secondary" id="browseListDataBtn" style="margin-top: 4px;">Browse Available Data</button>
    </div>
    
    <div class="property-group">
        <label>Show Items:</label>
        <select id="propListIterationMode">
            <option value="all" ${listConfig.iteration_mode === 'all' ? 'selected' : ''}>All Items</option>
            <option value="first" ${listConfig.iteration_mode === 'first' ? 'selected' : ''}>First Item Only</option>
            <option value="last" ${listConfig.iteration_mode === 'last' ? 'selected' : ''}>Last Item Only</option>
            <option value="index" ${listConfig.iteration_mode === 'index' ? 'selected' : ''}>Specific Item (by number)</option>
            <option value="range" ${listConfig.iteration_mode === 'range' ? 'selected' : ''}>Range of Items</option>
        </select>
        <small>💡 Choose how many items to display</small>
    </div>
    
    <div class="property-group" id="propListMaxItemsGroup" style="${listConfig.iteration_mode === 'all' || listConfig.iteration_mode === 'range' ? '' : 'display: none;'}">
        <label>Maximum Items to Show:</label>
        <input type="number" id="propListMaxItems" value="${listConfig.max_items || 10}" min="1" max="50">
        <small>Limits how many items are displayed (for "All" or "Range")</small>
    </div>
    
    <div class="property-group" id="propListItemIndexGroup" style="${listConfig.iteration_mode === 'index' ? '' : 'display: none;'}">
        <label>Item Number (0 = first, 1 = second, etc.):</label>
        <input type="number" id="propListItemIndex" value="${listConfig.item_index || 0}" min="0">
        <small>Which item to show (0 is the first item, 1 is the second, etc.)</small>
    </div>
    
    <div class="property-group" id="propListStartIndexGroup" style="${listConfig.iteration_mode === 'range' ? '' : 'display: none;'}">
        <label>Start at Item Number:</label>
        <input type="number" id="propListStartIndex" value="${listConfig.start_index || 0}" min="0">
        <small>First item to show (0 = first item)</small>
    </div>
    
    <div class="property-group">
        <label>Spacing Between Items (pixels):</label>
        <input type="number" id="propListSpacing" value="${spacing}" min="0" max="100">
        <small>Vertical space between each item</small>
    </div>
    
    <div class="property-group" style="border-top: 1px solid #ddd; padding-top: 12px; margin-top: 12px;">
        <label><strong>Item Template</strong></label>
        <p style="font-size: 12px; color: #666; margin: 4px 0;">This is what each item in the list will look like.</p>
    </div>
    
    <div class="property-group">
        <label>Template Widget Type:</label>
        <select id="propListItemWidgetType">
            <option value="text" ${itemTemplate.type === 'text' ? 'selected' : ''}>Text</option>
            <option value="progress" ${itemTemplate.type === 'progress' ? 'selected' : ''}>Progress Bar</option>
        </select>
    </div>
    
    <div class="property-group">
        <label>Display Field (from each item):</label>
        ${createDataPathSelector('propListItemPath', itemTemplate.data_binding?.path || '', 'e.g., name, title, value')}
        <small>📍 Field from each item to display (e.g., "name" for items[].name)</small>
        <button type="button" class="btn btn-small btn-secondary" id="browseItemFieldsBtn" style="margin-top: 4px;">Browse Item Fields</button>
    </div>
    
    <div class="property-group">
        <label>Display Template (optional):</label>
        <input type="text" id="propListItemTemplate" value="${itemTemplate.data_binding?.template || ''}" placeholder="e.g., {name} - {value}, Item: {title}">
        <small>💡 Use {field} to show values. Leave empty to show just the field value. Examples: "{name}: {value}", "Item {index}: {title}"</small>
    </div>
    
    <div class="property-group" style="background: #f9f9f9; padding: 8px; border-radius: 4px; font-size: 11px; color: #666;">
        <strong>💡 Quick Examples:</strong><br>
        • Array path: "items" → Shows all items in the "items" array<br>
        • Array path: "data.results" → Shows all items in "data.results"<br>
        • Show: "First Item Only" → Display only the first item<br>
        • Display field: "name" → Each item shows item.name<br>
        • Template: "{name}: {value}" → Shows "Item Name: Item Value"
    </div>
    `;
}

// Create data path selector with helper button
function createDataPathSelector(id, value, placeholder) {
    const escapedValue = (value || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    const escapedPlaceholder = (placeholder || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    return `
    <div style="display: flex; gap: 4px;">
        <input type="text" id="${id}" value="${escapedValue}" placeholder="${escapedPlaceholder}" style="flex: 1;">
        <button type="button" class="btn btn-small btn-secondary" data-browse-path="${id}" title="Browse available data fields">📂</button>
    </div>
    `;
}

// Browse and display available data fields
function browseDataFields(targetInputId, dataSource = null) {
    // Use test data if available, otherwise use empty object
    const dataToBrowse = dataSource || testData || {};
    
    // Build tree structure of available fields
    const fieldTree = buildFieldTree(dataToBrowse);
    
    // Show modal with data browser
    showDataBrowser(targetInputId, fieldTree, dataToBrowse);
}

// Build a tree structure from data object
function buildFieldTree(data, prefix = '', depth = 0) {
    if (depth > 5) return []; // Limit recursion depth
    
    const fields = [];
    
    if (Array.isArray(data)) {
        // For arrays, show the array itself and first item as example
        fields.push({
            name: prefix || 'Array',
            path: prefix || '$',
            type: 'array',
            example: `${data.length} items`,
            note: 'This is an array. Use this path to iterate over all items.'
        });
        
        // Show first item structure if available
        if (data.length > 0 && typeof data[0] === 'object') {
            fields.push({
                name: 'First item structure',
                path: prefix ? `${prefix}[0]` : '[0]',
                type: 'array_item',
                example: 'Click to see fields in each item',
                children: buildFieldTree(data[0], prefix ? `${prefix}[0]` : '[0]', depth + 1)
            });
        }
    } else if (typeof data === 'object' && data !== null) {
        for (const [key, value] of Object.entries(data)) {
            const currentPath = prefix ? `${prefix}.${key}` : key;
            let fieldType = typeof value;
            let example = '';
            
            if (Array.isArray(value)) {
                fieldType = 'array';
                example = `${value.length} items`;
            } else if (typeof value === 'object' && value !== null) {
                fieldType = 'object';
                example = 'object with fields';
            } else {
                example = String(value).substring(0, 50);
            }
            
            const fieldInfo = {
                name: key,
                path: currentPath,
                type: fieldType,
                example: example,
                children: (typeof value === 'object' && value !== null) ? buildFieldTree(value, currentPath, depth + 1) : []
            };
            fields.push(fieldInfo);
        }
    }
    
    return fields;
}

// Show data browser modal
function showDataBrowser(targetInputId, fieldTree, rawData) {
    // Create modal HTML
    const modalHTML = `
    <div id="dataBrowserModal" class="modal" style="display: block;">
        <div class="modal-content" style="max-width: 600px;">
            <div class="modal-header">
                <h3>Browse Available Data Fields</h3>
                <button type="button" class="modal-close" onclick="closeDataBrowser()">&times;</button>
            </div>
            <div class="modal-body">
                <p style="font-size: 12px; color: #666; margin-bottom: 12px;">
                    Click on a field to use it. Expand items with arrows (▶) to see nested fields.
                </p>
                <div id="dataBrowserTree" style="max-height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 8px; background: #f9f9f9; font-family: monospace; font-size: 12px;">
                    ${renderFieldTree(fieldTree)}
                </div>
                <div style="margin-top: 12px;">
                    <button type="button" class="btn btn-primary" onclick="insertDataPath('${targetInputId}', '$')">Use Root ($)</button>
                    <button type="button" class="btn btn-secondary" onclick="closeDataBrowser()">Cancel</button>
                </div>
            </div>
        </div>
    </div>
    `;
    
    // Add modal to body
    const modalContainer = document.createElement('div');
    modalContainer.id = 'dataBrowserModalContainer';
    modalContainer.innerHTML = modalHTML;
    document.body.appendChild(modalContainer);
    
    // Setup click handlers for field items
    modalContainer.querySelectorAll('.data-field-item').forEach(item => {
        item.addEventListener('click', (e) => {
            const path = item.dataset.path;
            if (path) {
                insertDataPath(targetInputId, path);
                closeDataBrowser();
            }
        });
    });
}

// Render field tree as HTML
function renderFieldTree(fields, indent = 0) {
    if (!fields || fields.length === 0) {
        return '<div style="color: #999; padding-left: ' + (indent * 20) + 'px;">No fields available. Try testing your API first to see available data.</div>';
    }
    
    let html = '';
    for (const field of fields) {
        const hasChildren = field.children && field.children.length > 0;
        const indentPx = indent * 20;
        const expandIcon = hasChildren ? '▶' : ' ';
        const typeIcon = field.type === 'array' ? '📋' : field.type === 'object' ? '📁' : '📄';
        const escapedPath = (field.path || '').replace(/"/g, '&quot;');
        const escapedExample = (field.example || '').replace(/"/g, '&quot;').substring(0, 60);
        const escapedName = (field.name || '').replace(/"/g, '&quot;');
        
        html += `
        <div class="data-field-item" data-path="${escapedPath}" style="padding: 6px ${indentPx}px; cursor: pointer; border-radius: 3px; margin: 2px 0; border-left: 2px solid transparent;" 
             onmouseover="this.style.background='#e8f4f8'; this.style.borderLeftColor='#0066cc';" 
             onmouseout="this.style.background='transparent'; this.style.borderLeftColor='transparent';">
            <span style="display: inline-block; width: 16px;">${expandIcon}</span>
            ${typeIcon} <strong>${escapedName}</strong> <span style="color: #666;">(${field.type})</span>
            <div style="color: #999; font-size: 11px; padding-left: 24px; margin-top: 2px;">
                Path: <code style="background: #f0f0f0; padding: 2px 4px; border-radius: 2px;">${escapedPath}</code>
                ${escapedExample ? ` | Example: ${escapedExample}` : ''}
            </div>
        </div>
        `;
        
        // Recursively render children (expanded by default for simplicity)
        if (hasChildren) {
            html += renderFieldTree(field.children, indent + 1);
        }
    }
    
    return html;
}

// Insert data path into target input
function insertDataPath(targetInputId, path) {
    const input = document.getElementById(targetInputId);
    if (input) {
        input.value = path;
        input.dispatchEvent(new Event('input', { bubbles: true }));
    }
}

// Close data browser modal
function closeDataBrowser() {
    const modalContainer = document.getElementById('dataBrowserModalContainer');
    if (modalContainer) {
        modalContainer.remove();
    }
}

// Make functions globally available for onclick handlers
window.insertDataPath = insertDataPath;
window.closeDataBrowser = closeDataBrowser;

// Setup property editor listeners
function setupPropertyEditorListeners() {
    // Save button
    const saveBtn = document.getElementById('propSaveBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            saveWidgetProperties();
        });
    }
    
    // Delete button
    const deleteBtn = document.getElementById('propDeleteBtn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => {
            deleteSelectedWidget();
        });
    }
    
    // Browse data buttons
    document.querySelectorAll('[id^="browse"]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const btnId = btn.id;
            let targetInputId = null;
            
            if (btnId === 'browseTextDataBtn') {
                targetInputId = 'propTextPath';
            } else if (btnId === 'browseListDataBtn') {
                targetInputId = 'propListArrayPath';
            } else if (btnId === 'browseItemFieldsBtn') {
                targetInputId = 'propListItemPath';
            }
            
            if (targetInputId) {
                browseDataFields(targetInputId);
            }
        });
    });
    
    // Data path selector buttons (📂 buttons)
    document.querySelectorAll('[data-browse-path]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const targetInputId = btn.dataset.browsePath;
            if (targetInputId) {
                browseDataFields(targetInputId);
            }
        });
    });
    
    // List iteration mode change handler
    const listModeSelect = document.getElementById('propListIterationMode');
    if (listModeSelect) {
        listModeSelect.addEventListener('change', (e) => {
            const mode = e.target.value;
            const maxItemsGroup = document.getElementById('propListMaxItemsGroup');
            const itemIndexGroup = document.getElementById('propListItemIndexGroup');
            const startIndexGroup = document.getElementById('propListStartIndexGroup');
            
            // Show/hide groups based on mode
            if (maxItemsGroup) {
                maxItemsGroup.style.display = (mode === 'all' || mode === 'range') ? 'block' : 'none';
            }
            if (itemIndexGroup) {
                itemIndexGroup.style.display = (mode === 'index') ? 'block' : 'none';
            }
            if (startIndexGroup) {
                startIndexGroup.style.display = (mode === 'range') ? 'block' : 'none';
            }
        });
    }
}

// Save widget properties
function saveWidgetProperties() {
    if (!selectedWidget) return;
    
    const widgetIndex = widgets.findIndex(w => w.id === selectedWidget.id);
    if (widgetIndex === -1) return;
    
    // Update widget based on type
    const type = selectedWidget.type;
    
    switch (type) {
        case 'text':
            selectedWidget.data_binding = {
                path: document.getElementById('propTextPath')?.value || '',
                template: document.getElementById('propTextTemplate')?.value || '',
                format: document.getElementById('propTextFormat')?.value || null
            };
            selectedWidget.style = {
                font_size: document.getElementById('propTextFontSize')?.value || 'medium',
                color: document.getElementById('propTextColor')?.value || 'text',
                align: document.getElementById('propTextAlign')?.value || 'left'
            };
            break;
        case 'progress':
            selectedWidget.data_binding = {
                path: document.getElementById('propProgressPath')?.value || '',
                min: parseInt(document.getElementById('propProgressMin')?.value || 0),
                max: parseInt(document.getElementById('propProgressMax')?.value || 100)
            };
            selectedWidget.style = {
                width: parseInt(document.getElementById('propProgressWidth')?.value || 30),
                show_label: document.getElementById('propProgressShowLabel')?.checked !== false,
                label_template: document.getElementById('propProgressLabelTemplate')?.value || '{value:.1f}%',
                color: 'text'
            };
            break;
        case 'chart':
            selectedWidget.chart_config = {
                type: document.getElementById('propChartType')?.value || 'line',
                data_path: document.getElementById('propChartDataPath')?.value || ''
            };
            selectedWidget.width = parseInt(document.getElementById('propChartWidth')?.value || 200);
            selectedWidget.height = parseInt(document.getElementById('propChartHeight')?.value || 150);
            break;
        case 'conditional':
            selectedWidget.condition = {
                operator: document.getElementById('propConditionOp')?.value || 'exists',
                path: document.getElementById('propConditionPath')?.value || '',
                value: document.getElementById('propConditionValue')?.value || ''
            };
            selectedWidget.widget = {
                type: document.getElementById('propConditionChildType')?.value || 'text',
                ...selectedWidget.widget
            };
            break;
    }
    
    // Update position
    const posX = document.getElementById('propPosX');
    const posY = document.getElementById('propPosY');
    if (posX && posY) {
        selectedWidget.position = {
            x: parseInt(posX.value || 0),
            y: parseInt(posY.value || 0)
        };
    }
    
    // Update container
    const container = document.getElementById('propContainer');
    if (container) {
        selectedWidget.container = container.value;
    }
    
    // Update widgets array
    widgets[widgetIndex] = { ...selectedWidget };
    
    updateCanvas();
    showSuccess('Widget properties saved');
}

// Delete selected widget
function deleteSelectedWidget() {
    if (!selectedWidget) return;
    
    if (!confirm('Delete this widget?')) return;
    
    widgets = widgets.filter(w => w.id !== selectedWidget.id);
    selectedWidget = null;
    
    updateCanvas();
    updatePropertyPanel();
    showSuccess('Widget deleted');
}

// Add layout area
// Toggle canvas grid
function toggleCanvasGrid() {
    let canvasGrid = document.querySelector('.canvas-grid');
    const toggleBtn = document.getElementById('toggleGridBtn');
    const canvasContainer = document.getElementById('canvasContainer');
    
    if (!canvasGrid && canvasContainer) {
        // Create grid if it doesn't exist
        canvasGrid = document.createElement('div');
        canvasGrid.className = 'canvas-grid';
        canvasContainer.appendChild(canvasGrid);
    }
    
    if (!canvasGrid) return;
    
    const isVisible = canvasGrid.classList.contains('visible');
    canvasGrid.classList.toggle('visible');
    
    if (toggleBtn) {
        toggleBtn.classList.toggle('active', !isVisible);
        toggleBtn.textContent = !isVisible ? 'Hide Grid' : 'Grid';
    }
}

function addLayoutArea() {
    const areaId = `area_${Date.now()}`;
    const newArea = {
        id: areaId,
        grid_area: `${layoutAreas.length + 1} / 1 / ${layoutAreas.length + 2} / 2`
    };
    layoutAreas.push(newArea);
    
    // Update layout in current slide
    if (currentSlide) {
        currentSlide.layout = {
            type: 'mixed',
            grid_areas: layoutAreas
        };
    }
    
    showSuccess('Layout area added');
}

// Clear canvas
function clearCanvas() {
    widgets = [];
    selectedWidget = null;
    updateCanvas();
    updatePropertyPanel();
    
    // Show drop zone message
    const dropZone = document.getElementById('canvasDropZone');
    if (dropZone) {
        const dropMessage = dropZone.querySelector('.drop-zone-message');
        if (dropMessage) {
            dropMessage.style.display = 'block';
        }
    }
}

// Legacy function - keeping for compatibility but simplifying workflow
function addLayoutArea() {
    if (!confirm('Clear all widgets from canvas?')) return;
    
    widgets = [];
    selectedWidget = null;
    
    updateCanvas();
    updatePropertyPanel();
}

// Generate preview
async function generatePreview() {
    if (!currentSlide) return;
    
    // Update current slide from form
    const titleInput = document.getElementById('designerSlideTitle');
    const durationInput = document.getElementById('designerSlideDuration');
    
    if (titleInput) currentSlide.title = titleInput.value || 'Custom Dashboard';
    if (durationInput) currentSlide.duration = parseInt(durationInput.value || 10);
    
    currentSlide.widgets = widgets;
    currentSlide.layout = {
        type: 'mixed',
        grid_areas: layoutAreas
    };
    
    // Get API config (optional - only if configured)
    const apiConfig = getAPIConfigFromForm();
    currentSlide.api_config = (apiConfig && apiConfig.endpoint) ? apiConfig : null;
    
    // Render preview using canvas
    try {
        const canvas = document.getElementById('previewCanvas');
        if (!canvas) return;
        
        // Update canvas overlay to show current widgets
        updateCanvasOverlay();
        
        // Render preview using backend API (if available) or show placeholder
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#000000';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 12px monospace';
        ctx.fillText('Preview (click Preview button to render)', 10, 20);
        
        // Call backend preview endpoint with test data if available
        if (testData || currentSlide.api_config) {
            await renderPreviewFromBackend(testData);
        }
    } catch (error) {
        console.error('Error generating preview:', error);
        showError('Failed to generate preview');
    }
}

// Render preview from backend
async function renderPreviewFromBackend(testDataOverride = null) {
    if (!currentSlide) return;
    
    // Create a temporary slide ID for preview (or use existing)
    const slideId = currentSlide.id || 0;
    
    try {
        const response = await fetch(`${API_BASE}/slides/${slideId}/preview`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                slide: currentSlide,
                test_data: testDataOverride || testData
            })
        });
        
        if (!response.ok) {
            throw new Error(`Preview failed: ${response.statusText}`);
        }
        
        // Get image blob
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        
        // Draw on canvas
        const canvas = document.getElementById('previewCanvas');
        if (canvas) {
            const ctx = canvas.getContext('2d');
            const img = new Image();
            img.onload = () => {
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                URL.revokeObjectURL(imageUrl);
            };
            img.src = imageUrl;
        }
    } catch (error) {
        console.error('Error rendering preview from backend:', error);
        // Fallback: show error on canvas
        const canvas = document.getElementById('previewCanvas');
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#000000';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#ff0000';
            ctx.font = 'bold 10px monospace';
            ctx.fillText('Preview Error', 10, 20);
        }
    }
}

// Get API config from form
function getAPIConfigFromForm() {
    const endpoint = document.getElementById('apiEndpoint')?.value;
    if (!endpoint) return null;
    
    const method = document.getElementById('apiMethod')?.value || 'GET';
    const headersText = document.getElementById('apiHeaders')?.value || '{}';
    const bodyText = document.getElementById('apiBody')?.value || null;
    const dataPath = document.getElementById('apiDataPath')?.value || '$';
    const refreshInterval = parseInt(document.getElementById('apiRefreshInterval')?.value || 30);
    
    let headers = {};
    try {
        headers = JSON.parse(headersText);
    } catch (e) {
        console.error('Invalid headers JSON:', e);
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

// Update API config form
function updateAPIConfigForm(apiConfig) {
    const endpointInput = document.getElementById('apiEndpoint');
    const methodSelect = document.getElementById('apiMethod');
    const headersTextarea = document.getElementById('apiHeaders');
    const bodyTextarea = document.getElementById('apiBody');
    const dataPathInput = document.getElementById('apiDataPath');
    const refreshInput = document.getElementById('apiRefreshInterval');
    
    if (endpointInput) endpointInput.value = apiConfig.endpoint || '';
    if (methodSelect) methodSelect.value = apiConfig.method || 'GET';
    if (headersTextarea) headersTextarea.value = JSON.stringify(apiConfig.headers || {}, null, 2);
    if (bodyTextarea) bodyTextarea.value = apiConfig.body ? (typeof apiConfig.body === 'string' ? apiConfig.body : JSON.stringify(apiConfig.body, null, 2)) : '';
    if (dataPathInput) dataPathInput.value = apiConfig.data_path || '$';
    if (refreshInput) refreshInput.value = apiConfig.refresh_interval || 30;
}

// Test API
async function testAPI() {
    const apiConfig = getAPIConfigFromForm();
    if (!apiConfig || !apiConfig.endpoint) {
        showError('Please enter an API endpoint');
        return;
    }
    
    const testResult = document.getElementById('apiTestResult');
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
                
                // Store result as test data
                testData = data.result;
            } else {
                testResult.className = 'api-test-result error';
                testResult.innerHTML = `✗ API Test Failed\n\nError: ${data.error || 'Unknown error'}`;
                testData = null;
            }
        }
    } catch (error) {
        if (testResult) {
            testResult.className = 'api-test-result error';
            testResult.innerHTML = `✗ API Test Failed\n\nError: ${error.message}`;
        }
        testData = null;
    }
}

// Use test data in preview
function useTestDataInPreview() {
    if (!testData) {
        showError('No test data available. Please test the API first.');
        return;
    }
    
    renderPreviewFromBackend(testData);
    showSuccess('Using test data in preview');
}

// Save custom slide
async function saveCustomSlide() {
    if (!currentSlide) return;
    
    // Update current slide from form
    const titleInput = document.getElementById('designerSlideTitle');
    const durationInput = document.getElementById('designerSlideDuration');
    
    if (titleInput) currentSlide.title = titleInput.value || 'Custom Dashboard';
    if (durationInput) currentSlide.duration = parseInt(durationInput.value || 10);
    
    currentSlide.widgets = widgets;
    currentSlide.layout = {
        type: 'mixed',
        grid_areas: layoutAreas
    };
    
    // API config is optional - only include if endpoint is configured
    const apiConfig = getAPIConfigFromForm();
    currentSlide.api_config = (apiConfig && apiConfig.endpoint) ? apiConfig : null;
    
    // Validate
    if (!currentSlide.title) {
        showError('Please enter a slide title');
        return;
    }
    
    if (!widgets || widgets.length === 0) {
        showError('Please add at least one widget');
        return;
    }
    
    try {
        let response;
        if (currentSlide.id) {
            // Update existing slide
            response = await fetch(`${API_BASE}/slides/${currentSlide.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(currentSlide)
            });
        } else {
            // Create new slide
            // Get current slides to determine order
            const slidesResponse = await fetch(`${API_BASE}/slides`);
            const slidesData = await slidesResponse.json();
            const slides = slidesData.slides || [];
            
            currentSlide.order = slides.length;
            
            response = await fetch(`${API_BASE}/slides`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(currentSlide)
            });
        }
        
        if (!response.ok) {
            throw new Error(`Save failed: ${response.statusText}`);
        }
        
        const savedSlide = await response.json();
        currentSlide.id = savedSlide.id;
        
        showSuccess('Custom slide saved successfully');
        
        // Reload slides list in main tab
        if (typeof loadSlides === 'function') {
            loadSlides();
        }
        
    } catch (error) {
        console.error('Error saving custom slide:', error);
        showError(`Failed to save custom slide: ${error.message}`);
    }
}

// Cancel designer
function cancelDesigner() {
    if (confirm('Cancel editing? All unsaved changes will be lost.')) {
        currentSlide = null;
        widgets = [];
        selectedWidget = null;
        testData = null;
        
        const container = document.getElementById('widgetDesignerContainer');
        const emptyState = document.getElementById('designerEmptyState');
        if (container && emptyState) {
            container.style.display = 'none';
            emptyState.style.display = 'block';
        }
        
        resetDesignerForm();
    }
}

// Utility functions
function showError(message) {
    if (typeof showToast === 'function') {
        showToast(message, 'error');
    } else {
        alert('Error: ' + message);
    }
}

function showSuccess(message) {
    if (typeof showToast === 'function') {
        showToast(message, 'success');
    } else {
        alert('Success: ' + message);
    }
}

