// modules.js
// Modular approach for the station verifier application

// =============================================================================
// 1. APPLICATION STATE MANAGEMENT
// =============================================================================
class AppState {
    constructor() {
        this.datasets = {
            1: { yearSide: null, lineFilter: 'all', color: '#3498db', markers: L.layerGroup(), data: null },
            2: { yearSide: null, lineFilter: 'all', color: '#e74c3c', markers: L.layerGroup(), data: null }
        };
        this.selectedStation = null;
        this.selectedMarker = null;
        this.markerDraggedPosition = null;
        this.corrections = {};
        this.newStationMode = false;
        this.newStationPosition = null;
        this.newStationMarker = null;
        this.historicalLayer = null;
        this.availableTileSets = [];
    }

    reset() {
        this.selectedStation = null;
        this.selectedMarker = null;
        this.markerDraggedPosition = null;
        this.newStationMode = false;
        this.newStationPosition = null;
        if (this.newStationMarker) {
            window.mapManager.map.removeLayer(this.newStationMarker);
            this.newStationMarker = null;
        }
    }
}

// =============================================================================
// 2. UI UTILITIES AND HELPERS
// =============================================================================
class UIUtils {
    static showToast(message, type = 'info') {
        // Remove existing toasts
        document.querySelectorAll('.toast').forEach(toast => {
            document.body.removeChild(toast);
        });
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => {
                    if (document.body.contains(toast)) {
                        document.body.removeChild(toast);
                    }
                }, 300);
            }, 3000);
        }, 100);
    }

    static createMarkerIcon(color, isSelected, isCorrected) {
        const hexToRgb = (hex) => {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result ? {
                r: parseInt(result[1], 16),
                g: parseInt(result[2], 16),
                b: parseInt(result[3], 16)
            } : null;
        };
        
        const rgb = hexToRgb(color);
        const colorStyle = rgb ? `background-color: rgb(${rgb.r}, ${rgb.g}, ${rgb.b})` : `background-color: ${color}`;
        
        const className = `${isSelected ? 'selected' : ''} ${isCorrected ? 'corrected' : ''}`.trim();
        const sizeClass = isSelected ? 'size-large' : 'size-normal';
        
        return L.divIcon({
            html: `<div class="station-marker ${className} ${sizeClass}" style="${colorStyle}"></div>`,
            className: '',
            iconSize: isSelected ? [16, 16] : [12, 12]
        });
    }

    static updateTabContent(tabName) {
        // Deactivate all tabs
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
        
        // Activate selected tab
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }
}

// =============================================================================
// 3. MAP MANAGEMENT
// =============================================================================
class MapManager {
    constructor(appState) {
        this.appState = appState;
        this.map = null;
        this.osmLayer = null;
        this.initializeMap();
    }

    initializeMap() {
        this.map = L.map('map').setView([52.5200, 13.4050], 12);
        
        this.osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(this.map);

        // Add dataset layers to map
        this.appState.datasets[1].markers.addTo(this.map);
        this.appState.datasets[2].markers.addTo(this.map);

        // Note: Removed map click handler for station adding since we're using text input now
    }

    updateHistoricalLayer() {
        if (!document.getElementById('historic-layer').checked) {
            return;
        }
        
        // Remove existing layer
        if (this.appState.historicalLayer && this.map.hasLayer(this.appState.historicalLayer)) {
            this.map.removeLayer(this.appState.historicalLayer);
        }
        
        const selectedOption = document.getElementById('historic-map-select').selectedOptions[0];
        if (!selectedOption || !selectedOption.value) {
            return;
        }
        
        const tileSet = this.appState.availableTileSets.find(ts => ts.name === selectedOption.value);
        if (!tileSet) {
            console.error('Selected tile set not found:', selectedOption.value);
            return;
        }
        
        const opacity = parseFloat(document.getElementById('opacity-slider').value);
        
        this.appState.historicalLayer = L.tileLayer(tileSet.url, {
            attribution: 'Historical Map - ' + tileSet.name,
            minZoom: Math.min(...tileSet.zoom_levels),
            maxZoom: Math.max(...tileSet.zoom_levels),
            opacity: opacity
        }).addTo(this.map);
    }
}

// =============================================================================
// 4. DATA MANAGEMENT
// =============================================================================
class DataManager {
    constructor(appState) {
        this.appState = appState;
    }

    async loadCorrections() {
        try {
            const response = await fetch('/get_corrections');
            this.appState.corrections = await response.json();
        } catch (error) {
            console.error('Error loading corrections:', error);
        }
    }

    async loadAvailableTileSets() {
        try {
            const response = await fetch('/available_tile_sets');
            this.appState.availableTileSets = await response.json();
            this.updateHistoricMapOptions();
        } catch (error) {
            console.error('Error loading tile sets:', error);
        }
    }

    updateHistoricMapOptions() {
        const select = document.getElementById('historic-map-select');
        select.innerHTML = '';
        
        if (this.appState.availableTileSets.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No tile sets available - process TIF files first';
            select.appendChild(option);
        } else {
            this.appState.availableTileSets.forEach(tileSet => {
                const option = document.createElement('option');
                option.value = tileSet.name;
                option.textContent = tileSet.name;
                option.dataset.url = tileSet.url;
                option.dataset.minZoom = Math.min(...tileSet.zoom_levels);
                option.dataset.maxZoom = Math.max(...tileSet.zoom_levels);
                select.appendChild(option);
            });
        }
    }

    async loadDatasets() {
        const yearSides = [];
        const lineFilters = {};
        
        // Gather dataset configurations
        const yearSide1 = document.getElementById('year-select-1').value;
        if (yearSide1) {
            yearSides.push(yearSide1);
            this.appState.datasets[1].yearSide = yearSide1;
            this.appState.datasets[1].lineFilter = document.getElementById('line-select-1').value;
            lineFilters[yearSide1] = this.appState.datasets[1].lineFilter;
        } else {
            UIUtils.showToast('Please select a primary dataset', 'error');
            return;
        }
        
        const yearSide2 = document.getElementById('year-select-2').value;
        if (yearSide2) {
            yearSides.push(yearSide2);
            this.appState.datasets[2].yearSide = yearSide2;
            this.appState.datasets[2].lineFilter = document.getElementById('line-select-2').value;
            lineFilters[yearSide2] = this.appState.datasets[2].lineFilter;
        } else {
            this.appState.datasets[2].yearSide = null;
            this.appState.datasets[2].markers.clearLayers();
        }

        try {
            const response = await fetch('/multi_data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ year_sides: yearSides, line_filters: lineFilters })
            });
            
            const data = await response.json();
            
            // Process each dataset
            for (const datasetId in this.appState.datasets) {
                const yearSide = this.appState.datasets[datasetId].yearSide;
                if (yearSide && data[yearSide]) {
                    this.appState.datasets[datasetId].data = data[yearSide];
                    this.appState.datasets[datasetId].markers.clearLayers();
                    
                    if (data[yearSide].error) {
                        UIUtils.showToast(`Error in dataset ${datasetId}: ${data[yearSide].error}`, 'error');
                    } else {
                        this.displayDataset(datasetId);
                    }
                }
            }
            
            // Update station list
            window.stationList.updateList(1);
            
            // Update add station modal options
            window.stationAdder.updateDatasetOptions();
            
            if (yearSides.length > 0) {
                UIUtils.showToast('Datasets loaded successfully', 'success');
            }
        } catch (error) {
            console.error('Error loading datasets:', error);
            UIUtils.showToast('Error loading datasets', 'error');
        }
    }

    displayDataset(datasetId) {
        const dataset = this.appState.datasets[datasetId];
        dataset.markers.clearLayers();
        
        if (!dataset.data || !dataset.data.geojson || !dataset.data.geojson.features) {
            return;
        }
        
        dataset.data.geojson.features.forEach(feature => {
            const marker = L.marker([
                feature.geometry.coordinates[1],  // latitude
                feature.geometry.coordinates[0]   // longitude
            ], {
                draggable: true,
                title: feature.properties.name,
                icon: UIUtils.createMarkerIcon(dataset.color, false, feature.properties.corrected)
            });
            
            marker.feature = feature;
            marker.datasetId = datasetId;
            
            marker.on('click', (e) => {
                window.stationSelector.selectStation(feature, marker);
            });
            
            marker.on('dragend', (e) => {
                this.appState.markerDraggedPosition = e.target.getLatLng();
                document.getElementById('save-correction').style.display = 'block';
                window.stationDetails.updateDisplay();
            });
            
            dataset.markers.addLayer(marker);
        });
    }
}

// =============================================================================
// 5. STATION ADDITION MODULE
// =============================================================================
class StationAdder {
    constructor(appState) {
        this.appState = appState;
        this.isFormValid = false;
        this.parsedCoordinates = null;
        this.setupEventHandlers();
    }

    setupEventHandlers() {
        // Add station button
        document.getElementById('add-station-btn').addEventListener('click', () => {
            this.showModal();
        });

        // Form field listeners
        document.getElementById('new-station-name').addEventListener('input', () => this.validateForm());
        document.getElementById('new-station-year-side').addEventListener('change', () => {
            this.updateLineOptions();
            this.validateForm();
        });
        document.getElementById('new-station-line').addEventListener('change', () => {
            this.updateStopOrderOptions();
            this.validateForm();
        });
        document.getElementById('new-station-stop-order').addEventListener('change', () => this.validateForm());

        // Coordinates input listener
        document.getElementById('new-station-coords-input').addEventListener('input', (e) => {
            this.parseCoordinates(e.target.value);
            this.validateForm();
        });

        // Create button
        document.getElementById('create-station-btn').addEventListener('click', () => this.createStation());

        // Close modal
        document.querySelectorAll('.close-modal').forEach(close => {
            close.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                if (modal.id === 'add-station-modal') {
                    this.hideModal();
                }
            });
        });
    }

    parseCoordinates(coordString) {
        const display = document.getElementById('new-station-coords-display');
        const parsedSpan = document.getElementById('parsed-coords');
        
        // Reset state
        this.parsedCoordinates = null;
        display.style.display = 'none';
        
        if (!coordString.trim()) {
            return;
        }

        // Try to parse coordinates from various formats
        // Support formats like: "52.42146115349324, 13.178055311099948"
        // Also support: "52.42146115349324,13.178055311099948" (no space)
        // Also support: "52.42146115349324 13.178055311099948" (space separated)
        
        const cleanString = coordString.trim();
        let matches;
        
        // Try comma-separated format first
        matches = cleanString.match(/^(-?\d+\.?\d*),\s*(-?\d+\.?\d*)$/);
        
        // Try space-separated format
        if (!matches) {
            matches = cleanString.match(/^(-?\d+\.?\d*)\s+(-?\d+\.?\d*)$/);
        }
        
        if (matches) {
            const lat = parseFloat(matches[1]);
            const lng = parseFloat(matches[2]);
            
            // Validate coordinate ranges
            if (lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
                // Additional validation for Berlin area (rough bounds)
                if (lat >= 52.3 && lat <= 52.7 && lng >= 13.0 && lng <= 13.8) {
                    this.parsedCoordinates = { lat, lng };
                    display.style.display = 'block';
                    parsedSpan.textContent = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
                    parsedSpan.style.color = '#27ae60'; // Green for valid
                    
                    // Update or create map marker to show location
                    this.updateMapMarker(lat, lng);
                } else {
                    // Coordinates are valid but outside Berlin area
                    display.style.display = 'block';
                    parsedSpan.textContent = 'Warning: Coordinates outside Berlin area';
                    parsedSpan.style.color = '#f39c12'; // Orange for warning
                }
            } else {
                // Invalid coordinate ranges
                display.style.display = 'block';
                parsedSpan.textContent = 'Invalid coordinate ranges';
                parsedSpan.style.color = '#e74c3c'; // Red for error
            }
        } else if (cleanString.length > 5) {
            // Show error for malformed input (but only if they've typed something substantial)
            display.style.display = 'block';
            parsedSpan.textContent = 'Invalid format. Use: latitude, longitude';
            parsedSpan.style.color = '#e74c3c'; // Red for error
        }
    }

    updateMapMarker(lat, lng) {
        // Remove existing marker if any
        if (this.appState.newStationMarker) {
            window.mapManager.map.removeLayer(this.appState.newStationMarker);
        }

        // Add new marker
        this.appState.newStationMarker = L.marker([lat, lng], {
            icon: L.divIcon({
                html: '<div class="station-marker new-station"></div>',
                className: '',
                iconSize: [16, 16]
            })
        }).addTo(window.mapManager.map);

        // Pan map to show the marker
        window.mapManager.map.setView([lat, lng], Math.max(window.mapManager.map.getZoom(), 15));
    }

    showModal() {
        this.resetForm();
        this.updateDatasetOptions();
        // Remove the newStationMode since we're not using map clicks anymore
        this.appState.newStationMode = false;
        document.getElementById('add-station-modal').style.display = 'block';
    }

    hideModal() {
        document.getElementById('add-station-modal').style.display = 'none';
        this.appState.reset();
        this.parsedCoordinates = null;
    }

    resetForm() {
        document.getElementById('new-station-name').value = '';
        document.getElementById('new-station-type').value = 'ubahn';
        document.getElementById('new-station-year-side').value = '';
        document.getElementById('new-station-line').value = '';
        document.getElementById('new-station-coords-input').value = '';
        document.getElementById('new-station-coords-display').style.display = 'none';
        document.getElementById('stop-order-container').style.display = 'none';
        this.parsedCoordinates = null;
        this.validateForm();
    }

    updateDatasetOptions() {
        const select = document.getElementById('new-station-year-side');
        select.innerHTML = '<option value="">-- Select Dataset --</option>';
        
        for (const datasetId in this.appState.datasets) {
            if (this.appState.datasets[datasetId].yearSide) {
                const option = document.createElement('option');
                option.value = this.appState.datasets[datasetId].yearSide;
                option.textContent = this.appState.datasets[datasetId].yearSide;
                select.appendChild(option);
            }
        }
    }

    async updateLineOptions() {
        const yearSide = document.getElementById('new-station-year-side').value;
        const lineSelect = document.getElementById('new-station-line');
        
        lineSelect.innerHTML = '<option value="">-- No Line Connection --</option>';
        
        if (!yearSide) return;

        // Find the dataset with line data
        for (const datasetId in this.appState.datasets) {
            if (this.appState.datasets[datasetId].yearSide === yearSide && 
                this.appState.datasets[datasetId].data?.lines) {
                
                this.appState.datasets[datasetId].data.lines.forEach(line => {
                    const option = document.createElement('option');
                    option.value = line.line_id;
                    option.textContent = `${line.line_name} (${line.type})`;
                    lineSelect.appendChild(option);
                });
                break;
            }
        }
    }

    async updateStopOrderOptions() {
        const lineId = document.getElementById('new-station-line').value;
        const yearSide = document.getElementById('new-station-year-side').value;
        const stopOrderContainer = document.getElementById('stop-order-container');
        const stopOrderSelect = document.getElementById('new-station-stop-order');
        
        if (!lineId || !yearSide) {
            stopOrderContainer.style.display = 'none';
            return;
        }

        try {
            const response = await fetch(`/get_line_details/${yearSide}/${lineId}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                stopOrderSelect.innerHTML = '';
                
                data.insertion_points.forEach(point => {
                    const option = document.createElement('option');
                    option.value = point.stop_order;
                    option.textContent = `${point.stop_order}. ${point.description}`;
                    stopOrderSelect.appendChild(option);
                });
                
                stopOrderContainer.style.display = 'block';
            } else {
                UIUtils.showToast(`Error loading line details: ${data.message}`, 'error');
            }
        } catch (error) {
            console.error('Error fetching line details:', error);
            UIUtils.showToast('Error loading line details', 'error');
        }
    }

    validateForm() {
        const name = document.getElementById('new-station-name').value.trim();
        const yearSide = document.getElementById('new-station-year-side').value;
        const lineId = document.getElementById('new-station-line').value;
        const stopOrder = document.getElementById('new-station-stop-order').value;
        
        // Check required fields
        const hasRequiredFields = name && yearSide && this.parsedCoordinates;
        
        // If line is selected, stop order is required
        const hasValidLineConnection = !lineId || (lineId && stopOrder);
        
        this.isFormValid = hasRequiredFields && hasValidLineConnection;
        
        this.updateCreateButton();
    }

    updateCreateButton() {
        const createBtn = document.getElementById('create-station-btn');
        const name = document.getElementById('new-station-name').value.trim();
        const yearSide = document.getElementById('new-station-year-side').value;
        const lineId = document.getElementById('new-station-line').value;
        const stopOrder = document.getElementById('new-station-stop-order').value;
        
        createBtn.disabled = !this.isFormValid;
        
        // Update button text based on state
        if (!name) {
            createBtn.textContent = 'Enter station name';
        } else if (!yearSide) {
            createBtn.textContent = 'Select dataset';
        } else if (!this.parsedCoordinates) {
            createBtn.textContent = 'Enter valid coordinates';
        } else if (lineId && !stopOrder) {
            createBtn.textContent = 'Select position on line';
        } else {
            createBtn.textContent = 'Create Station';
        }
    }

    async createStation() {
        if (!this.isFormValid) {
            UIUtils.showToast('Please complete all required fields', 'error');
            return;
        }

        const stationData = {
            year_side: document.getElementById('new-station-year-side').value,
            name: document.getElementById('new-station-name').value.trim(),
            type: document.getElementById('new-station-type').value,
            latitude: this.parsedCoordinates.lat,
            longitude: this.parsedCoordinates.lng,
            source: 'User added'
        };

        const lineId = document.getElementById('new-station-line').value;
        const stopOrder = document.getElementById('new-station-stop-order').value;
        
        if (lineId && stopOrder) {
            stationData.line_connections = [{
                line_id: lineId,
                stop_order: parseInt(stopOrder)
            }];
        }

        const createBtn = document.getElementById('create-station-btn');
        createBtn.disabled = true;
        createBtn.textContent = 'Creating station...';

        try {
            const response = await fetch('/add_station', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(stationData)
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                UIUtils.showToast('Station added successfully', 'success');
                this.hideModal();
                
                // Reload datasets to show new station
                await window.dataManager.loadDatasets();
            } else {
                UIUtils.showToast(`Error adding station: ${data.message}`, 'error');
            }
        } catch (error) {
            console.error('Error adding station:', error);
            UIUtils.showToast('Error adding station', 'error');
        } finally {
            createBtn.disabled = false;
            this.updateCreateButton();
        }
    }
}

// =============================================================================
// 6. STATION SELECTION AND DETAILS
// =============================================================================
class StationSelector {
    constructor(appState) {
        this.appState = appState;
    }

    selectStation(feature, marker) {
        // Reset previous selection
        if (this.appState.selectedMarker) {
            const prevDatasetId = this.appState.selectedMarker.datasetId;
            const prevDataset = this.appState.datasets[prevDatasetId];
            const prevIsCorrected = this.appState.selectedMarker.feature.properties.corrected;
            this.appState.selectedMarker.setIcon(
                UIUtils.createMarkerIcon(prevDataset.color, false, prevIsCorrected)
            );
        }
        
        // Set new selection
        this.appState.selectedStation = feature;
        this.appState.selectedMarker = marker;
        
        // Update marker icon
        const datasetId = marker.datasetId;
        const dataset = this.appState.datasets[datasetId];
        const isCorrected = feature.properties.corrected;
        marker.setIcon(UIUtils.createMarkerIcon(dataset.color, true, isCorrected));
        
        // Reset state
        this.appState.markerDraggedPosition = null;
        
        // Show UI elements
        document.getElementById('save-correction').style.display = 'none';
        document.getElementById('delete-station').style.display = 'block';
        document.getElementById('current-station').style.display = 'block';
        
        // Update station list highlighting
        this.updateStationListSelection();
        
        // Update details display
        window.stationDetails.updateDisplay();
    }

    updateStationListSelection() {
        const stationItems = document.querySelectorAll('.station-item');
        stationItems.forEach(item => {
            item.classList.remove('selected');
            if (item.getAttribute('data-id') == this.appState.selectedStation.properties.stop_id) {
                item.classList.add('selected');
                item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        });
    }
}

// =============================================================================
// 7. STATION DETAILS AND EDITING
// =============================================================================
class StationDetails {
    constructor(appState) {
        this.appState = appState;
        this.originalName = null;
        this.nameChanged = false;
        this.setupEventHandlers();
    }

    setupEventHandlers() {
        // Name editing
        document.getElementById('edit-name-btn').addEventListener('click', () => this.toggleNameEdit());
        document.getElementById('save-name-btn').addEventListener('click', () => this.saveName());
        document.getElementById('station-name-input').addEventListener('input', () => this.trackNameChanges());

        // Save correction button
        document.getElementById('save-correction').addEventListener('click', () => this.saveCorrection());
        
        // Delete station button
        document.getElementById('delete-station').addEventListener('click', () => this.deleteStation());
    }

    updateDisplay() {
        if (!this.appState.selectedStation) return;
        
        const station = this.appState.selectedStation;
        const yearSide = station.properties.year_side;
        
        // Update compact view
        document.getElementById('selected-station-name').textContent = station.properties.name;
        document.getElementById('selected-station-year-side').textContent = yearSide;
        
        // Calculate current position
        const originalLat = station.geometry.coordinates[1];
        const originalLng = station.geometry.coordinates[0];
        
        let correctedPosition = null;
        if (this.appState.corrections[yearSide]?.[station.properties.stop_id]) {
            const correction = this.appState.corrections[yearSide][station.properties.stop_id];
            correctedPosition = { lat: correction.lat, lng: correction.lng };
        }
        
        const currentPosition = this.appState.markerDraggedPosition || 
                               correctedPosition || 
                               { lat: originalLat, lng: originalLng };
        
        // Update coordinates display
        document.getElementById('selected-station-coords').textContent = 
            `${currentPosition.lat.toFixed(6)}, ${currentPosition.lng.toFixed(6)}`;
        
        // Update status
        const statusElement = document.getElementById('selected-station-status');
        if (this.appState.markerDraggedPosition) {
            statusElement.className = 'status-tag status-modified';
            statusElement.textContent = 'Modified (Unsaved)';
        } else if (correctedPosition) {
            statusElement.className = 'status-tag status-corrected';
            statusElement.textContent = 'Corrected';
        } else {
            statusElement.className = 'status-tag status-original';
            statusElement.textContent = 'Original';
        }

        // Update name input
        const nameInput = document.getElementById('station-name-input');
        nameInput.value = station.properties.name;
        nameInput.disabled = true;
        
        // Reset editing state
        document.getElementById('edit-name-btn').textContent = 'Edit';
        document.getElementById('save-name-btn').style.display = 'none';
    }

    toggleNameEdit() {
        const nameInput = document.getElementById('station-name-input');
        const editButton = document.getElementById('edit-name-btn');
        const saveButton = document.getElementById('save-name-btn');
        
        if (nameInput.disabled) {
            // Enable editing
            nameInput.disabled = false;
            nameInput.focus();
            editButton.textContent = 'Cancel';
            saveButton.style.display = 'inline';
            this.originalName = nameInput.value;
        } else {
            // Cancel editing
            nameInput.disabled = true;
            nameInput.value = this.originalName;
            editButton.textContent = 'Edit';
            saveButton.style.display = 'none';
            this.nameChanged = false;
            nameInput.classList.remove('changed');
        }
    }

    trackNameChanges() {
        const nameInput = document.getElementById('station-name-input');
        this.nameChanged = nameInput.value !== this.originalName;
        
        if (this.nameChanged) {
            nameInput.classList.add('changed');
        } else {
            nameInput.classList.remove('changed');
        }
    }

    async saveName() {
        if (!this.appState.selectedStation || !this.nameChanged) return;
        
        const yearSide = this.appState.selectedStation.properties.year_side;
        const nameInput = document.getElementById('station-name-input');
        
        try {
            const response = await fetch('/save_name_correction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    year_side: yearSide,
                    stop_id: this.appState.selectedStation.properties.stop_id,
                    name: nameInput.value
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                UIUtils.showToast('Station name saved successfully!', 'success');
                
                // Update local state
                this.appState.selectedStation.properties.name = nameInput.value;
                
                // Reset editing state
                this.nameChanged = false;
                nameInput.disabled = true;
                document.getElementById('edit-name-btn').textContent = 'Edit';
                document.getElementById('save-name-btn').style.display = 'none';
                
                // Refresh displays
                this.updateDisplay();
                window.dataManager.loadDatasets();
            } else {
                UIUtils.showToast('Error saving station name', 'error');
            }
        } catch (error) {
            console.error('Error saving name:', error);
            UIUtils.showToast('Error saving station name', 'error');
        }
    }

    async saveCorrection() {
        if (!this.appState.selectedStation || !this.appState.markerDraggedPosition) return;
        
        const yearSide = this.appState.selectedStation.properties.year_side;
        
        try {
            const response = await fetch('/save_correction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    year_side: yearSide,
                    stop_id: this.appState.selectedStation.properties.stop_id,
                    lat: this.appState.markerDraggedPosition.lat,
                    lng: this.appState.markerDraggedPosition.lng,
                    name: null
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                UIUtils.showToast('Station location saved successfully!', 'success');
                
                // Update local corrections
                if (!this.appState.corrections[yearSide]) {
                    this.appState.corrections[yearSide] = {};
                }
                
                this.appState.corrections[yearSide][this.appState.selectedStation.properties.stop_id] = {
                    lat: this.appState.markerDraggedPosition.lat,
                    lng: this.appState.markerDraggedPosition.lng
                };
                
                // Reset state
                this.appState.markerDraggedPosition = null;
                document.getElementById('save-correction').style.display = 'none';
                
                // Refresh datasets
                window.dataManager.loadDatasets();
                this.updateDisplay();
            } else {
                UIUtils.showToast('Error saving station location', 'error');
            }
        } catch (error) {
            console.error('Error saving correction:', error);
            UIUtils.showToast('Error saving station location', 'error');
        }
    }

    async deleteStation() {
        if (!this.appState.selectedStation) return;
        
        const station = this.appState.selectedStation;
        
        if (confirm(`Are you sure you want to delete station "${station.properties.name}"? This action cannot be undone.`)) {
            try {
                const response = await fetch('/delete_station', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        year_side: station.properties.year_side,
                        stop_id: station.properties.stop_id
                    })
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    UIUtils.showToast('Station deleted successfully', 'success');
                    
                    // Reset UI
                    document.getElementById('current-station').style.display = 'none';
                    document.getElementById('full-station-details').style.display = 'none';
                    
                    this.appState.reset();
                    
                    // Reload datasets
                    window.dataManager.loadDatasets();
                } else {
                    UIUtils.showToast(`Error deleting station: ${data.message}`, 'error');
                }
            } catch (error) {
                console.error('Error deleting station:', error);
                UIUtils.showToast('Error deleting station', 'error');
            }
        }
    }
}

// =============================================================================
// 8. STATION LIST MANAGEMENT
// =============================================================================
class StationList {
    constructor(appState) {
        this.appState = appState;
        this.setupEventHandlers();
    }

    setupEventHandlers() {
        // Dataset switcher
        document.querySelectorAll('#station-list-datasets .btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('#station-list-datasets .btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.updateList(e.target.getAttribute('data-dataset'));
            });
        });

        // Search functionality
        document.getElementById('station-search').addEventListener('input', (e) => {
            this.filterStations(e.target.value);
        });
    }

    updateList(datasetId) {
        const stationList = document.getElementById('station-list');
        stationList.innerHTML = '';
        
        const dataset = this.appState.datasets[datasetId];
        
        if (!dataset.yearSide || !dataset.data || !dataset.data.geojson || !dataset.data.geojson.features) {
            stationList.innerHTML = '<div class="no-data-message">No stations to display</div>';
            return;
        }
        
        dataset.data.geojson.features.forEach(feature => {
            const listItem = this.createStationListItem(feature, dataset);
            stationList.appendChild(listItem);
        });
        
        // Update button labels
        document.querySelectorAll('#station-list-datasets .btn').forEach(btn => {
            const btnDatasetId = btn.getAttribute('data-dataset');
            const yearSide = this.appState.datasets[btnDatasetId].yearSide;
            btn.textContent = yearSide || `Dataset ${btnDatasetId}`;
        });
    }

    createStationListItem(feature, dataset) {
        const listItem = document.createElement('div');
        listItem.className = `station-item${feature.properties.corrected ? ' corrected' : ''}`;
        listItem.setAttribute('data-id', feature.properties.stop_id);
        listItem.setAttribute('data-name', feature.properties.name);
        
        // Color indicator
        const colorIndicator = document.createElement('div');
        colorIndicator.className = 'color-indicator';
        colorIndicator.style.backgroundColor = dataset.color;
        
        // Transport type indicator
        const typeSpan = document.createElement('span');
        typeSpan.className = `transport-type type-${feature.properties.type.replace(/\s+/g, '')}`;
        typeSpan.textContent = feature.properties.type.charAt(0).toUpperCase();
        
        // Station details
        const detailsDiv = document.createElement('div');
        detailsDiv.className = 'station-details';
        
        const nameDiv = document.createElement('div');
        nameDiv.className = 'station-name';
        nameDiv.textContent = feature.properties.name;
        
        const lineDiv = document.createElement('div');
        lineDiv.className = 'station-line';
        lineDiv.textContent = feature.properties.line || 'No line';
        
        detailsDiv.appendChild(nameDiv);
        detailsDiv.appendChild(lineDiv);
        
        listItem.appendChild(colorIndicator);
        listItem.appendChild(typeSpan);
        listItem.appendChild(detailsDiv);
        
        // Click handler
        listItem.addEventListener('click', () => {
            // Find the corresponding marker
            let marker = null;
            dataset.markers.eachLayer(m => {
                if (m.feature.properties.stop_id === feature.properties.stop_id) {
                    marker = m;
                }
            });
            
            if (marker) {
                window.stationSelector.selectStation(feature, marker);
                window.mapManager.map.setView([
                    feature.geometry.coordinates[1],
                    feature.geometry.coordinates[0]
                ], 17);
            }
        });
        
        return listItem;
    }

    filterStations(searchText) {
        const searchLower = searchText.toLowerCase();
        const stationItems = document.querySelectorAll('.station-item');
        
        stationItems.forEach(item => {
            const name = item.getAttribute('data-name').toLowerCase();
            const id = item.getAttribute('data-id').toLowerCase();
            
            if (name.includes(searchLower) || id.includes(searchLower)) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    }
}

// =============================================================================
// 9. APPLICATION INITIALIZATION
// =============================================================================
class StationVerifierApp {
    constructor() {
        this.state = new AppState();
        this.mapManager = new MapManager(this.state);
        this.dataManager = new DataManager(this.state);
        this.stationAdder = new StationAdder(this.state);
        this.stationSelector = new StationSelector(this.state);
        this.stationDetails = new StationDetails(this.state);
        this.stationList = new StationList(this.state);
        
        // Make instances globally available
        window.appState = this.state;
        window.mapManager = this.mapManager;
        window.dataManager = this.dataManager;
        window.stationAdder = this.stationAdder;
        window.stationSelector = this.stationSelector;
        window.stationDetails = this.stationDetails;
        window.stationList = this.stationList;
        
        this.initialize();
    }

    async initialize() {
        // Setup tab functionality
        this.setupTabs();
        
        // Setup remaining event handlers
        this.setupEventHandlers();
        
        // Load initial data
        await this.dataManager.loadCorrections();
        await this.dataManager.loadAvailableTileSets();
        
        console.log('Station Verifier App initialized');
    }

    setupTabs() {
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.getAttribute('data-tab');
                UIUtils.updateTabContent(tabName);
            });
        });
        
        // Details toggle
        document.getElementById('details-toggle').addEventListener('click', () => {
            const fullDetails = document.getElementById('full-station-details');
            const isVisible = fullDetails.style.display === 'block';
            
            fullDetails.style.display = isVisible ? 'none' : 'block';
            document.getElementById('details-toggle').textContent = 
                isVisible ? 'Show Full Details' : 'Hide Full Details';
            
            if (!isVisible) {
                UIUtils.updateTabContent('tools');
            }
        });
    }

    setupEventHandlers() {
        // Load datasets button
        document.getElementById('load-datasets-btn').addEventListener('click', () => {
            this.dataManager.loadDatasets();
        });

        // Export button
        document.getElementById('export-btn').addEventListener('click', async () => {
            try {
                const response = await fetch('/export_corrections');
                const data = await response.json();
                
                if (data.status === 'success') {
                    UIUtils.showToast(`Exported ${data.updated_stations} station corrections to database!`, 'success');
                } else {
                    UIUtils.showToast(`Export error: ${data.message}`, 'error');
                }
            } catch (error) {
                console.error('Error exporting data:', error);
                UIUtils.showToast('Error exporting data', 'error');
            }
        });

        // Layer controls
        document.getElementById('osm-layer').addEventListener('change', (e) => {
            if (e.target.checked) {
                this.mapManager.map.addLayer(this.mapManager.osmLayer);
            } else {
                this.mapManager.map.removeLayer(this.mapManager.osmLayer);
            }
        });

        document.getElementById('historic-layer').addEventListener('change', (e) => {
            const historicLayerSelector = document.getElementById('historic-layer-selector');
            
            if (e.target.checked) {
                historicLayerSelector.style.display = 'block';
                this.mapManager.updateHistoricalLayer();
            } else {
                historicLayerSelector.style.display = 'none';
                
                if (this.state.historicalLayer && this.mapManager.map.hasLayer(this.state.historicalLayer)) {
                    this.mapManager.map.removeLayer(this.state.historicalLayer);
                    this.state.historicalLayer = null;
                }
            }
        });

        document.getElementById('historic-map-select').addEventListener('change', () => {
            this.mapManager.updateHistoricalLayer();
        });

        // Opacity slider
        document.getElementById('opacity-slider').addEventListener('input', (e) => {
            document.getElementById('opacity-value').textContent = `${Math.round(e.target.value * 100)}%`;
            if (this.state.historicalLayer) {
                this.state.historicalLayer.setOpacity(parseFloat(e.target.value));
            }
        });

        // Year selection handlers
        document.querySelectorAll('.year-select').forEach(select => {
            select.addEventListener('change', (e) => {
                const datasetId = e.target.id.split('-')[2];
                this.handleYearSideSelection(datasetId, e.target.value);
            });
        });

        // Color selection handlers
        document.querySelectorAll('.color-select').forEach(select => {
            select.addEventListener('change', (e) => {
                const datasetId = e.target.id.split('-')[2];
                this.state.datasets[datasetId].color = e.target.value;
                
                if (this.state.datasets[datasetId].yearSide) {
                    this.dataManager.displayDataset(datasetId);
                }
            });
        });
    }

    async handleYearSideSelection(datasetId, yearSide) {
        const lineFilterContainer = document.getElementById(`line-filter-container-${datasetId}`);
        const lineSelect = document.getElementById(`line-select-${datasetId}`);
        
        lineSelect.innerHTML = '<option value="all">All Lines</option>';
        lineFilterContainer.style.display = 'none';
        
        if (yearSide) {
            try {
                const response = await fetch(`/data/${yearSide}`);
                const data = await response.json();
                
                this.state.datasets[datasetId].linesData = data.lines;
                
                const uniqueLines = {};
                data.lines.forEach(line => {
                    uniqueLines[line.line_id] = {
                        name: line.line_name,
                        type: line.type
                    };
                });
                
                const sortedLines = Object.entries(uniqueLines).sort((a, b) => {
                    return a[1].name.localeCompare(b[1].name);
                });

                sortedLines.forEach(([id, line]) => {
                    const option = document.createElement('option');
                    option.value = id;
                    option.textContent = `${line.name} (${line.type})`;
                    lineSelect.appendChild(option);
                });
                
                lineFilterContainer.style.display = 'block';
            } catch (error) {
                console.error(`Error fetching lines for ${yearSide}:`, error);
                UIUtils.showToast(`Error loading lines for dataset ${datasetId}`, 'error');
            }
        }
    }
}

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new StationVerifierApp();
});