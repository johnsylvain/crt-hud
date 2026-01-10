# Widget Designer UX Improvements Plan

## Overview

Improve the widget designer user experience by making API configuration optional and implementing a drag-and-drop interface for easier widget placement and management.

## Current Issues

1. API configuration is required/always visible - makes it cumbersome for simple widgets
2. No drag-and-drop - widgets are added via click, positioning requires manual input
3. Canvas is just a preview - no interactive positioning
4. Workflow is form-heavy - too many manual configuration steps

## Improvements

### 1. Optional API Configuration

- Make API section collapsible/hidden by default
- Allow widgets to work with static/test data without API
- Show API configuration only when user explicitly wants to add external data
- Widgets should work standalone (with static data bindings)

### 2. Drag-and-Drop Interface

- **Palette to Canvas**: Drag widgets from palette onto canvas to add them
- **Canvas Repositioning**: Drag widgets on canvas to reposition them visually
- **Visual Feedback**: Show drop zones, drag previews, and position indicators
- **Snap to Grid**: Optional grid snapping for alignment
- **Resize Handles**: Visual resize handles on selected widgets

### 3. Simplified Workflow

- Start with canvas visible and empty state message
- Drag widget from palette → appears on canvas at drop location
- Click widget on canvas → properties panel updates
- Edit properties → live preview updates
- Save when done

## Implementation Tasks

### Backend Changes

1. **Make API Config Optional in Validation**

- Update widget validation to allow widgets without API config
- Allow slides without api_config (default to empty data dict)
- Handle empty/missing data gracefully in renderer

### Frontend Changes

1. **Collapsible API Section**

- Add collapse/expand button to API configuration section
- Hide by default, show "Configure API (Optional)" toggle
- Only require API config when widgets actually need external data

2. **Drag-and-Drop from Palette**

- Make palette items draggable (draggable="true")
- Add dragstart handler to palette items
- Add dragover/drop handlers to canvas
- Create widget at drop position on canvas

3. **Drag Widgets on Canvas**

- Make canvas widgets draggable
- Track widget positions visually on canvas overlay
- Update widget position property when dragged
- Show visual preview during drag

4. **Canvas Overlay for Widget Positioning**

- Create overlay div on top of canvas for interactive widgets
- Render widget placeholders as draggable divs
- Show widget boundaries and handles when selected
- Sync overlay positions with actual widget positions

5. **Visual Feedback**

- Highlight drop zones when dragging from palette
- Show drag preview/ghost during drag
- Show grid/snap indicators (optional)
- Highlight selected widget with border/background
- Show resize handles for selected widgets

6. **Simplified Workflow**

- Remove complex layout area configuration (use simple absolute positioning by default)
- Auto-generate widget IDs and positions
- Quick-add widgets at center of canvas
- Inline property editing on canvas (optional)

## Files to Modify

1. `frontend/static/js/widget-designer.js`

- Add drag-and-drop event handlers
- Implement canvas overlay system
- Make API section optional/collapsible
- Simplify widget creation workflow

2. `frontend/templates/index.html`

- Make API section collapsible
- Add drag-and-drop attributes to palette items
- Add canvas overlay div for interactive widgets
- Improve canvas container structure

3. `frontend/static/css/widget-designer.css`

- Add drag-and-drop styles (dragging, drop-zone, etc.)
- Style canvas overlay and widget placeholders
- Add selected widget styles (border, handles)
- Improve visual feedback styles

4. `backend/display/renderer.py`

- Ensure widgets can render with empty/missing data
- Handle optional API config gracefully

5. `backend/api/routes.py`

- Update validation to make API config optional
- Allow saving slides without api_config

## User Flow Improvements

**Before:**

1. Click "New Custom Slide"
2. Configure API (required)
3. Click widget type in palette
4. Widget appears at default position
5. Manually edit X/Y position in properties
6. Configure widget properties
7. Preview
8. Save

**After:**

1. Click "New Custom Slide"
2. Drag widget from palette to canvas
3. Widget appears at drop location
4. Drag widget to reposition (optional)
5. Click widget to edit properties
6. API config is optional - only add if needed
7. Live preview updates as you edit
8. Save when done

## Technical Details

### Drag-and-Drop Implementation

- Use HTML5 drag-and-drop API (draggable, dragstart, dragover, drop)
- Canvas overlay uses absolute positioning to match canvas coordinates
- Widget positions stored as x/y pixels relative to canvas
- Convert canvas coordinates to actual display coordinates (320x280)

### Canvas Overlay System

- Transparent overlay div positioned exactly over canvas
- Widget placeholders rendered as divs with absolute positioning
- Canvas shows rendered preview, overlay shows interactive widgets
- On save, overlay positions are converted to widget config

### Optional API

- API section collapsed by default with "Optional: Add API Configuration" header
- Widgets can bind to static data paths (like "test.value", "demo.data")
- If no API config, renderer uses empty dict {} as data
- Widgets show placeholder/empty state if data path doesn't resolve

## Files to Modify

1. `frontend/static/js/widget-designer.js` - Add drag-drop, overlay system, optional API
2. `frontend/templates/index.html` - Collapsible API, drag attributes, canvas overlay
3. `frontend/static/css/widget-designer.css` - Drag-drop styles, overlay styles
4. `backend/display/renderer.py` - Handle optional data gracefully
5. `backend/api/routes.py` - Optional API validation