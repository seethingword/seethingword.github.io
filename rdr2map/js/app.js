const DOM_ID = 'mapContainer';
const LS_KEY = 'rdr2';
const MODIFIER__LEGENDARY = 'is--legendary';
const TILES_ABS_PATH = './imgs/tiles';
const hiddenOverlays = {};
let completedMarkers = [];
let filteredSubTypes = [];
let lsData, mapBoundary, mapInst, mapLayers, markers, 
  subTypeFilterInput, subTypeFilterWrapper, typesLayerGroups;

// Load markers from static JSON file
function loadMarkers() { 
  return fetch('./markers.default.json')
    .then(resp => resp.json())
    .catch(err => {
      console.error('Error loading markers:', err);
      return [];
    });
}

function handlePopupOpen(ev) {
  const popup = ev.popup;
  const marker = popup._source;
  const completedToggle = popup._wrapper.querySelector('.marker-popup__completed input');
  let markerNdx;
  
  // Ensures popup stays centered to Marker
  popup.setLatLng(marker._latlng);
  
  for (let i=0; i<markers.length; i++) {
    if (markers[i].data.uid === marker.customData.uid) {
      markerNdx = i;
      break;
    }
  }
  
  const completedHandler = ({ currentTarget: { checked, value: uid } }) => {
    const { markerType } = marker.customData;
    const { data, lat, lng } = markers[markerNdx];
    
    (checked)
      ? completedMarkers.push(uid)
      : completedMarkers.splice(completedMarkers.indexOf(uid), 1);
    
    saveMapState();
    
    typesLayerGroups[markerType].removeLayer(marker);
    marker.remove();
    createMarker({ ...data, lat, lng });
  };
  
  // ensure events don't get bound multiple times
  completedToggle.removeEventListener('change', completedHandler);
  // add fresh handlers
  completedToggle.addEventListener('change', completedHandler);
  
  // User marker editing functionality removed for static GitHub Pages version
}

function createMarker({
  editable,
  lat,
  lng,
  markerCustomSubType,
  markerDescription,
  markerSubType,
  markerType,
  previewing,
  rating,
  uid
}) {
  const ICON_NAME = markerType.toLowerCase().replace(/\s/g, '-');
  const LEGENDARY = (/legendary/i.test(markerSubType)) ? '-legendary' : '';
  const ICON_RADIUS = 30;
  const ICON_OFFSET_VERTICAL = 0.01;
  const POPUP_OFFSET = [0, -ICON_RADIUS / 1.5];
  const _lat = lat + ICON_OFFSET_VERTICAL;
  const marker = L.canvasMarker([_lat, lng], {
    img: {
      offsetY: -ICON_RADIUS/2.5,
      opacity: (lsData.completedMarkers.includes(uid)) ? 0.3 : 1,
      size: [ICON_RADIUS, ICON_RADIUS],
      url: `./imgs/markers/${ICON_NAME}${LEGENDARY}.png`,
    },
    radius: ICON_RADIUS / 1.5,
  });
  let navMarkup = '';
  let ratingMarkup = '';
  
  // Navigation removed for static version
  
  if (rating) ratingMarkup = `
    <span class="marker-popup__rating">${Array(+rating).fill('&#9733;').join('')}</span>
  `;
  
  const popupContent = `
    <h4 class="marker-popup__title">
      <span
        class="marker-popup__icon"
        data-sub-type="${markerSubType}"
        data-type="${markerType}"
      ></span>
      ${ratingMarkup} ${markerCustomSubType || markerSubType}
    </h4>
    <label class="marker-popup__completed">
      <input type="checkbox" value="${uid}" ${lsData.completedMarkers.includes(uid) ? 'checked' : ''} /> Completed
    </label>
    <p>${markerDescription || ''}</p>
    ${navMarkup}
  `;
  
  marker.bindPopup(popupContent, {
    offset: POPUP_OFFSET,
  });
  
  marker.customData = {
    markerSubType,
    markerType,
    uid,
  };
  
  if (previewing) {
    marker.addTo(mapInst);
    marker.openPopup();
  }
  else typesLayerGroups[markerType].addLayer(marker);
  
  return marker;
}

function saveMapState() {
  const data = {
    completedMarkers,
    hiddenOverlays,
    latlng: mapInst.getCenter(),
    zoom: mapInst.getZoom(),
  };
  window.localStorage.setItem(LS_KEY, JSON.stringify(data));
  lsData = data;
};

function formDataToObj(form) {
  return [...(new FormData(form)).entries()].reduce((obj, arr) => {
    obj[arr[0]] = arr[1];
    return obj;
  }, {});
}

// Marker creator function removed for static version
function openMarkerCreator() {
  // Disabled for static GitHub Pages version
}


// Map click handler removed for static version

function handleOverlayToggle({ name, type }) {
  if (type === 'overlayadd') delete hiddenOverlays[name];
  else hiddenOverlays[name] = true;
  
  saveMapState();
}

function renderMarkers(filter) {
  const clearedGroups = [];
  
  if (filter) {
    markers.forEach(({ data, lat, lng }, i) => {
      const { markerCustomSubType, markerSubType, markerType } = data;
      const subType = markerCustomSubType || markerSubType;
      
      // clear out all layers based on marker types that have been added
      if (!clearedGroups.includes(markerType)) {
        typesLayerGroups[markerType].clearLayers();
        clearedGroups.push(markerType);
      }
      
      // add a reference to the filter
      if (
        subType === filter
        && !filteredSubTypes.includes(subType)
      ) filteredSubTypes.push(subType);
      
      // only add Markers that are filtered
      if (filteredSubTypes.includes(subType)) createMarker({ ...data, lat, lng });
    });
  }
  else {
    filteredSubTypes = [];
    markers.forEach(({ data, lat, lng }, i) => {
      createMarker({ ...data, lat, lng });
    });
  }
}

function renderFilterTag({
  label,
  markerItems,
  subType,
  type,
} = {}) {
  const iconDataAtts = (subType)
    ? `data-sub-type="${subType}" data-type="${type}"`
    : '';
  const filterTag = document.createElement('button');
        filterTag.className = 'filter-tag';
        filterTag.innerHTML = `
          <span class="filter-tag__icon" ${iconDataAtts}>${(markerItems) ? '&#10033;' : ''}</span>
          ${label || subType}
          <span class="filter-tag__close">&#10005;</span>
        `;
  
  if (markerItems) {
    filterTag.dataset.markerItems = JSON.stringify(markerItems);
  }
  else {
    filterTag.dataset.subType = subType;
    filterTag.dataset.type = type;
  }
  
  subTypeFilterWrapper.appendChild(filterTag);
}

function handleFilterSelect({ elements: filters, value }) {
  if (filters.length) {
    if (filters.length > 1) {
      const markerItems = [];
      
      filters.forEach((filter) => {
        const { subType, type } = filter.dataset;
        renderMarkers(subType);
        markerItems.push({ subType, type });
      });
      
      renderFilterTag({ label: value, markerItems });
    }
    else {
      const { subType, type } = filters[0].dataset;
      renderMarkers(subType);
      renderFilterTag({ subType, type });
    }
  }
}

function handleFilterRemoval(ev) {
  const el = ev.target;
  
  if (el.classList.contains('filter-tag')) {
    function removeFilter({ subType, type } = {}) {
      const filterNdx = filteredSubTypes.indexOf(subType);
      
      filteredSubTypes.splice(filterNdx, 1);
      typesLayerGroups[type].eachLayer((marker) => {
        if (marker.customData.markerSubType === subType) {
          typesLayerGroups[type].removeLayer(marker);
          marker.remove();
        }
      });
      
      // if no more filters are applied, show all Markers
      if (!filteredSubTypes.length) renderMarkers();
    };
    
    if (el.dataset.subType) {
      const { subType, type } = el.dataset;
      removeFilter({ subType, type });
    }
    else if (el.dataset.markerItems) {
      const markerItems = JSON.parse(el.dataset.markerItems);
      markerItems.forEach(({ subType, type }) => {
        removeFilter({ subType, type });
      });
    }
    
    el.remove();
  }
}

function setFilterItems() {
  const added = [];
  const itemGroups = {};
  
  markers.forEach(({ data: { markerCustomSubType, markerSubType, markerType } }) => {
    const subType = markerCustomSubType || markerSubType;
    
    if (!added.includes(`${markerType}_${subType}`)) {
      if (!itemGroups[markerType]) itemGroups[markerType] = [];
      itemGroups[markerType].push(subType);
      added.push(`${markerType}_${subType}`);
    }
  });
  
  subTypeFilterInput.items = Object.keys(itemGroups)
    .sort()
    .reduce((arr, markerType) => itemGroups[markerType]
      .sort()
      .reduce((combined, markerSubType) => {
        combined.push({
          attributes: {
            'data-sub-type': markerSubType,
            'data-type': markerType,
          },
          label: `<span class="filter-icon"></span><span class="filter-label">${markerSubType}</span>`,
          value: markerSubType,
        });
        return combined;
      }, arr)
    , []);
}

function init() {
  loadMarkers().then((loadedMarkers) => {
    const mapWrapper = document.createElement('div');
          mapWrapper.className = 'map-wrapper';
    const mapEl = document.createElement('div');
          mapEl.className = 'map-container';
          mapEl.id = DOM_ID;
    mapWrapper.appendChild(mapEl);
    document.body.prepend(mapWrapper);
    
    lsData = JSON.parse(window.localStorage.getItem(LS_KEY) || '{}');
    if (!lsData.completedMarkers) lsData.completedMarkers = [];
    if (!lsData.hiddenOverlays) lsData.hiddenOverlays = [];
    completedMarkers = lsData.completedMarkers;
    markers = loadedMarkers;
    mapBoundary = L.latLngBounds(L.latLng(-190, 0), L.latLng(0, 256));    
    mapLayers = {
      'default': L.tileLayer(
        `${TILES_ABS_PATH}/{z}/{x}_{y}.jpg`,
        {
          noWrap: true,
          bounds: mapBoundary,
        }
      ),
    };
    const viewArgs = (lsData.latlng)
      ? [lsData.latlng, lsData.zoom]
      : [{ lat: -70, lng: 111.75 }, 3];
    mapInst = L.map(DOM_ID, {
      attributionControl: false,
      crs: L.CRS.Simple,
      layers: [mapLayers['default']],
      maxZoom: 8,
      minZoom: 2,
      preferCanvas: true,
      zoomControl: false,
    }).setView(...viewArgs);
    
    typesLayerGroups = [...MARKER_TYPES].reduce((obj, [type]) => {
      obj[type] = L.layerGroup([]).addTo(mapInst);
      return obj;
    }, {});
    
    L.control.zoom({ position: 'bottomright' }).addTo(mapInst);
    L.control.layers({}, typesLayerGroups).addTo(mapInst);
    
    const layersControlList = document.querySelector('.leaflet-control-layers-list');
    const allLayersToggle = document.createElement('button');
          allLayersToggle.type = 'button';
          allLayersToggle.className = 'leaflet-control-layers-list__toggle-all-btn';
          allLayersToggle.innerText = 'Toggle All';
          allLayersToggle.title = 'Click to toggle all layers on or off';
    layersControlList.prepend(allLayersToggle);
    allLayersToggle.addEventListener('click', () => {
      allLayersToggle.disabled = true;
      
      const checkboxLabels = [...layersControlList.querySelectorAll('label')];
      const layerCheckboxes = [...layersControlList.querySelectorAll('input[type="checkbox"]')];
      const numberOfVisibleLayers = layerCheckboxes.reduce((count, checkbox) => {
        count += (checkbox.checked) ? 1 : 0;
        return count;
      }, 0);
      
      const toggleLayer = (label) => new Promise((resolve) => {
        const checkbox = label.querySelector('input[type="checkbox"]');
        const markerType = label.innerText.trim();
        
        if (numberOfVisibleLayers > 0 && checkbox.checked) {
          label.click();
          resolve();
        }
        else if (numberOfVisibleLayers === 0 && !checkbox.checked) {
          // NOTE - The interval and layer 'add' logic is hacky, but the only
          // solution that worked on lower-spec Mobile devices. Otherwise, when
          // I triggered a label click, only some layers would turn back on,
          // while the rest seemingly faded away, never to be heard from again.
          const layer = typesLayerGroups[markerType];
          const int = setInterval(() => {
            if (!checkbox.checked) label.click();
          }, 10);
          const handler = () => {
            clearInterval(int);
            layer.off('add', handler);
            resolve();
          }
          
          layer.on('add', handler);
          label.click();
        }
        else resolve();
      });
      
      Promise.all([
        ...checkboxLabels.map(label => toggleLayer(label))
      ]).then(() => {
        allLayersToggle.disabled = false;
      });
    });
    
    // Marker creator toggle removed for static version
    
    renderMarkers();
    
    subTypeFilterWrapper = document.createElement('div');
    subTypeFilterWrapper.className = 'filter-input-wrapper';
    subTypeFilterInput = document.createElement('custom-auto-complete-input');
    subTypeFilterInput.placeholder = 'Filter Markers';
    setFilterItems();
    subTypeFilterInput.onSelect = handleFilterSelect;
    subTypeFilterInput.styles = `
      .custom-autocomplete__list-item button {
        margin: 0;
        display: flex;
        align-items: center;
      }
      .custom-autocomplete__list-item button * {
        pointer-events: none;
      }
      
      .filter-icon {
        width: 2em;
        height: 1em;
        border: solid 3px;
        border-radius: 0.25em;
        margin-right: 1em;
        display: inline-block;
        box-shadow: 0 0 0px 1px #776245;
      }
      
      button[data-sub-type*="Legendary"] .filter-icon { border-color: var(--color__legendary); }
      button[data-type="Animal"] .filter-icon { background: var(--color__animal); }
      button[data-type="Bird"] .filter-icon { background: var(--color__bird); }
      button[data-type="Cigarette Card"] .filter-icon { background: var(--color__cig-card); }
      button[data-type="Dino Bones"] .filter-icon { background: var(--color__dino-bones); }
      button[data-type="Dreamcatcher"] .filter-icon { background: var(--color__dreamcatcher); }
      button[data-type="Fish"] .filter-icon { background: var(--color__fish); }
      button[data-type="Hat"] .filter-icon { background: var(--color__hat); }
      button[data-type="Mission Item"] .filter-icon { background: var(--color__mission-item); }
      button[data-type="Plant"] .filter-icon { background: var(--color__plant); }
      button[data-type="Point of Interest"] .filter-icon { background: var(--color__poi); }
      button[data-type="Rare Item"] .filter-icon { background: var(--color__rare-item); }
      button[data-type="Rock Carving"] .filter-icon { background: var(--color__rock-carving); }
      button[data-type="Treasure"] .filter-icon { background: var(--color__treasure); }
      button[data-type="Treasure Map"] .filter-icon { background: var(--color__treasure-map); }
      button[data-type="Weapon"] .filter-icon { background: var(--color__weapon); }
    `;
    subTypeFilterWrapper.appendChild(subTypeFilterInput);
    subTypeFilterWrapper.addEventListener('click', handleFilterRemoval);
    document.body.appendChild(subTypeFilterWrapper);

    // Map click handler removed for static version
    mapInst.on('move', saveMapState);
    mapInst.on('overlayadd', handleOverlayToggle);
    mapInst.on('overlayremove', handleOverlayToggle);
    mapInst.on('popupopen', handlePopupOpen);
    mapInst.on('zoomend', saveMapState);
    
    Object.keys(lsData.hiddenOverlays).forEach((hiddenOverlay) => {
      const layerGroup = typesLayerGroups[hiddenOverlay];
      if (layerGroup) mapInst.removeLayer(layerGroup);
    });
  });
}

init();
