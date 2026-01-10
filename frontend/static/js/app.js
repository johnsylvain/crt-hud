// Homelab HUD Admin UI JavaScript

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
    startCurrentSlideRefresh();
    startSlidePreviewRefresh();
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
    
    // Conditional checkbox
    document.getElementById('slideConditional').addEventListener('change', (e) => {
        document.getElementById('conditionTypeGroup').style.display = e.target.checked ? 'block' : 'none';
    });
    
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
            
            // Load debug logs if switching to debug tab
            if (targetTab === 'debug') {
                loadDebugLogs();
                loadArmDebugLogs();
            }
        });
    });
}

// Load Slides
async function loadSlides() {
    try {
        const response = await fetch(`${API_BASE}/slides`);
        const data = await response.json();
        slides = data.slides || [];
        renderSlides();
    } catch (error) {
        console.error('Error loading slides:', error);
        showError('Failed to load slides');
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
    
    const typeLabels = {
        'pihole_summary': 'Pi-hole Stats',
        'plex_now_playing': 'Plex Now Playing',
        'arm_rip_progress': 'ARM Rip Progress',
        'system_stats': 'System Stats'
    };
    
    const badge = slide.conditional ? `<span class="slide-badge badge-conditional">Conditional</span>` : '';
    
    // Create preview image with cache-busting timestamp
    const previewImageUrl = `${API_BASE}/preview/${slide.id}?t=${Date.now()}`;
    
    div.innerHTML = `
        <div class="slide-preview" onclick="previewSlide(${slide.id})" title="Click to view full preview">
            <img src="${previewImageUrl}" alt="Slide preview" class="slide-preview-img" 
                 onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'160\' height=\'140\'%3E%3Crect fill=\'%23ccc\' width=\'160\' height=\'140\'/%3E%3Ctext fill=\'%23999\' font-family=\'monospace\' font-size=\'12\' x=\'50%25\' y=\'50%25\' text-anchor=\'middle\' dominant-baseline=\'middle\'%3ELoading...%3C/text%3E%3C/svg%3E';" />
        </div>
        <div class="slide-info">
            <div class="slide-title">${slide.title} ${badge}</div>
            <div class="slide-meta">
                ${typeLabels[slide.type] || slide.type} | 
                Duration: ${slide.duration}s | 
                Order: ${slide.order || 0}
            </div>
        </div>
        <div class="slide-actions">
            <button class="btn btn-small btn-secondary" onclick="previewSlide(${slide.id})">Preview</button>
            <button class="btn btn-small btn-secondary" onclick="editSlide(${slide.id})">Edit</button>
            <button class="btn btn-small btn-danger" onclick="deleteSlide(${slide.id})">Delete</button>
        </div>
    `;
    
    return div;
}

// Make Sortable (simple implementation)
function makeSortable(container) {
    let draggedElement = null;
    
    container.querySelectorAll('.slide-item').forEach(item => {
        item.draggable = true;
        
        item.addEventListener('dragstart', (e) => {
            draggedElement = item;
            item.classList.add('dragging');
        });
        
        item.addEventListener('dragend', () => {
            item.classList.remove('dragging');
            draggedElement = null;
        });
        
        item.addEventListener('dragover', (e) => {
            e.preventDefault();
            const afterElement = getDragAfterElement(container, e.clientY);
            if (afterElement == null) {
                container.appendChild(draggedElement);
            } else {
                container.insertBefore(draggedElement, afterElement);
            }
        });
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
function saveSlideOrder() {
    const container = document.getElementById('slidesList');
    const slideItems = container.querySelectorAll('.slide-item');
    const slideIds = Array.from(slideItems).map(item => parseInt(item.dataset.id));
    
    fetch(`${API_BASE}/slides/reorder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slide_ids: slideIds })
    })
    .then(() => loadSlides())
    .catch(error => {
        console.error('Error saving slide order:', error);
        showError('Failed to save slide order');
    });
}

// Slide Modal
function openSlideModal(slide = null) {
    const modal = document.getElementById('slideModal');
    const form = document.getElementById('slideForm');
    
    if (slide) {
        document.getElementById('modalTitle').textContent = 'Edit Slide';
        document.getElementById('slideId').value = slide.id;
        document.getElementById('slideType').value = slide.type;
        document.getElementById('slideTitle').value = slide.title;
        document.getElementById('slideDuration').value = slide.duration;
        document.getElementById('slideConditional').checked = slide.conditional || false;
        document.getElementById('slideConditionType').value = slide.condition_type || 'arm_active';
        document.getElementById('conditionTypeGroup').style.display = (slide.conditional || false) ? 'block' : 'none';
    } else {
        document.getElementById('modalTitle').textContent = 'Add Slide';
        form.reset();
        document.getElementById('conditionTypeGroup').style.display = 'none';
    }
    
    modal.style.display = 'block';
}

function closeSlideModal() {
    document.getElementById('slideModal').style.display = 'none';
    document.getElementById('slideForm').reset();
}

// Handle Slide Submit
async function handleSlideSubmit(e) {
    e.preventDefault();
    
    const formData = {
        type: document.getElementById('slideType').value,
        title: document.getElementById('slideTitle').value,
        duration: parseInt(document.getElementById('slideDuration').value),
        conditional: document.getElementById('slideConditional').checked,
    };
    
    if (formData.conditional) {
        formData.condition_type = document.getElementById('slideConditionType').value;
    }
    
    const slideId = document.getElementById('slideId').value;
    
    try {
        if (slideId) {
            // Update
            await fetch(`${API_BASE}/slides/${slideId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
        } else {
            // Create
            const maxOrder = slides.length > 0 ? Math.max(...slides.map(s => s.order || 0)) : -1;
            formData.order = maxOrder + 1;
            
            await fetch(`${API_BASE}/slides`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
        }
        
        closeSlideModal();
        await loadSlides();
        // Refresh current slide if it was updated
        if (slideId && currentSlideRefreshInterval) {
            updateCurrentSlide();
        }
    } catch (error) {
        console.error('Error saving slide:', error);
        showError('Failed to save slide');
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
    if (!confirm('Are you sure you want to delete this slide?')) {
        return;
    }
    
    try {
        await fetch(`${API_BASE}/slides/${id}`, {
            method: 'DELETE'
        });
        loadSlides();
    } catch (error) {
        console.error('Error deleting slide:', error);
        showError('Failed to delete slide');
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
        config = await response.json();
        renderConfig();
    } catch (error) {
        console.error('Error loading config:', error);
        showError('Failed to load configuration');
    }
}

// Render Config
function renderConfig() {
    const container = document.getElementById('configForm');
    container.innerHTML = '';
    
    // ARM Config
    container.appendChild(createConfigSection('ARM', 'arm', config.arm || {}));
    
    // Pi-hole Config
    container.appendChild(createConfigSection('Pi-hole', 'pihole', config.pihole || {}));
    
    // Plex Config
    container.appendChild(createConfigSection('Plex', 'plex', config.plex || {}));
    
    // System Config
    container.appendChild(createConfigSection('System', 'system', config.system || {}));
}

// Create Config Section
function createConfigSection(title, key, data) {
    const section = document.createElement('div');
    section.className = 'config-section';
    
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
        ${key === 'system' ? `
            <div class="config-row">
                <label>NAS Mounts (comma-separated):</label>
                <input type="text" id="config_${key}_nas_mounts" value="${(data.nas_mounts || []).join(', ')}" placeholder="/mnt/nas, /media/nas">
            </div>
        ` : ''}
        ${key === 'arm' ? `
            <div class="config-row">
                <label>Endpoint:</label>
                <input type="text" id="config_${key}_endpoint" value="${data.endpoint || '/json?mode=joblist'}" placeholder="/json?mode=joblist">
            </div>
        ` : ''}
    `;
    
    return section;
}

// Save Config
async function saveConfig() {
    const newConfig = {
        arm: {
            enabled: document.getElementById('config_arm_enabled').checked,
            api_url: document.getElementById('config_arm_api_url').value,
            api_key: document.getElementById('config_arm_api_key').value,
            poll_interval: parseInt(document.getElementById('config_arm_poll_interval').value),
            endpoint: document.getElementById('config_arm_endpoint').value,
            conditional: true
        },
        pihole: {
            enabled: document.getElementById('config_pihole_enabled').checked,
            api_url: document.getElementById('config_pihole_api_url').value,
            api_token: document.getElementById('config_pihole_api_key').value,
            poll_interval: parseInt(document.getElementById('config_pihole_poll_interval').value),
            conditional: false
        },
        plex: {
            enabled: document.getElementById('config_plex_enabled').checked,
            api_url: document.getElementById('config_plex_api_url').value,
            api_token: document.getElementById('config_plex_api_key').value,
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
    
    try {
        await fetch(`${API_BASE}/config`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newConfig)
        });
        config = newConfig;
        showSuccess('Configuration saved successfully');
    } catch (error) {
        console.error('Error saving config:', error);
        showError('Failed to save configuration');
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
                'system_stats': 'System Stats'
            };
            
            const typeLabel = typeLabels[infoData.type] || infoData.type;
            const conditionalBadge = infoData.conditional ? ' (Conditional)' : '';
            const timeAgo = infoData.timestamp ? formatTimeAgo(Date.now() / 1000 - infoData.timestamp) : '';
            
            metaEl.textContent = `${typeLabel}${conditionalBadge}${timeAgo ? ' • ' + timeAgo : ''}`;
        }
        
        infoDiv.style.display = 'block';
        
        // Update slide image with cache-busting
        const imageUrl = `${API_BASE}/preview/current?t=${Date.now()}`;
        imageDiv.innerHTML = `<img src="${imageUrl}" alt="Current Slide Preview" />`;
        
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
        imageDiv.innerHTML = '<div class="preview-loading">Error loading current slide</div>';
        statusDiv.textContent = 'Error: ' + error.message;
        statusDiv.style.color = '#e74c3c';
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

// Utility Functions
function showError(message) {
    alert(`Error: ${message}`);
}

function showSuccess(message) {
    alert(`Success: ${message}`);
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
        document.getElementById('debugLogs').innerHTML = `<div class="debug-error">Error loading debug logs: ${error.message}</div>`;
    }
}

async function testPlexConnection() {
    const testBtn = document.getElementById('testPlexBtn');
    const originalText = testBtn.textContent;
    testBtn.textContent = 'Testing...';
    testBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/debug/plex/test`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            alert(`Connection test successful!\n\nResult: ${JSON.stringify(data.result, null, 2)}`);
        } else {
            alert(`Connection test failed.\n\nLatest log: ${JSON.stringify(data.latest_log, null, 2)}`);
        }
        
        // Refresh logs after test
        await loadDebugLogs();
    } catch (error) {
        console.error('Error testing connection:', error);
        alert(`Error testing connection: ${error.message}`);
    } finally {
        testBtn.textContent = originalText;
        testBtn.disabled = false;
    }
}

async function fetchPlexData() {
    const fetchBtn = document.getElementById('fetchDataBtn');
    const originalText = fetchBtn.textContent;
    fetchBtn.textContent = 'Fetching...';
    fetchBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/debug/plex/data`);
        const data = await response.json();
        
        // Display the data
        const dataDiv = document.getElementById('debugData');
        const dataContent = document.getElementById('debugDataContent');
        
        dataContent.textContent = JSON.stringify(data, null, 2);
        dataDiv.style.display = 'block';
        
        // Scroll to data section
        dataDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // Also update has_active_streams in status
        if (data.has_active_streams !== undefined) {
            document.getElementById('debugHasStreams').textContent = data.has_active_streams ? 'Yes' : 'No';
        }
        
    } catch (error) {
        console.error('Error fetching Plex data:', error);
        alert(`Error fetching data: ${error.message}`);
    } finally {
        fetchBtn.textContent = originalText;
        fetchBtn.disabled = false;
    }
}

function clearDebugLogs() {
    if (confirm('Clear debug logs? This cannot be undone.')) {
        // Note: This would require a backend endpoint to clear logs
        // For now, we'll just reload which will show current logs
        document.getElementById('debugLogs').innerHTML = '<div class="debug-empty">Debug logs cleared. New requests will populate logs.</div>';
    }
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
        document.getElementById('armDebugLogs').innerHTML = `<div class="debug-error">Error loading debug logs: ${error.message}</div>`;
    }
}

async function testArmConnection() {
    const testBtn = document.getElementById('testArmBtn');
    const originalText = testBtn.textContent;
    testBtn.textContent = 'Testing...';
    testBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/debug/arm/test`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            alert(`Connection test successful!\n\nResult: ${JSON.stringify(data.result, null, 2)}`);
        } else {
            alert(`Connection test failed.\n\nLatest log: ${JSON.stringify(data.latest_log, null, 2)}`);
        }
        
        // Refresh logs after test
        await loadArmDebugLogs();
    } catch (error) {
        console.error('Error testing ARM connection:', error);
        alert(`Error testing connection: ${error.message}`);
    } finally {
        testBtn.textContent = originalText;
        testBtn.disabled = false;
    }
}

async function fetchArmData() {
    const fetchBtn = document.getElementById('fetchArmDataBtn');
    const originalText = fetchBtn.textContent;
    fetchBtn.textContent = 'Fetching...';
    fetchBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/debug/arm/data`);
        const data = await response.json();
        
        // Display the data
        const dataDiv = document.getElementById('armDebugData');
        const dataContent = document.getElementById('armDebugDataContent');
        
        dataContent.textContent = JSON.stringify(data, null, 2);
        dataDiv.style.display = 'block';
        
        // Scroll to data section
        dataDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // Also update has_active_rip in status
        if (data.has_active_rip !== undefined) {
            document.getElementById('armDebugHasRip').textContent = data.has_active_rip ? 'Yes' : 'No';
        }
        
    } catch (error) {
        console.error('Error fetching ARM data:', error);
        alert(`Error fetching data: ${error.message}`);
    } finally {
        fetchBtn.textContent = originalText;
        fetchBtn.disabled = false;
    }
}

function clearArmDebugLogs() {
    if (confirm('Clear ARM debug logs? This cannot be undone.')) {
        // Note: This would require a backend endpoint to clear logs
        // For now, we'll just reload which will show current logs
        document.getElementById('armDebugLogs').innerHTML = '<div class="debug-empty">Debug logs cleared. New requests will populate logs.</div>';
    }
}

// Make functions available globally
window.editSlide = editSlide;
window.deleteSlide = deleteSlide;
window.previewSlide = previewSlide;

