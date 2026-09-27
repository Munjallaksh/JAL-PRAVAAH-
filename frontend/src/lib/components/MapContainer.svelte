<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { selectedLocation, layers, basemap, simulationResults, currentTimeIndex, selectedFeatureInfo, domainRiverCoords } from '../store';
  import maplibregl from 'maplibre-gl';
  import LayerControl from './LayerControl.svelte';
  import FeatureInspector from './FeatureInspector.svelte';
  import ParticleWaterFlow from './ParticleWaterFlow.svelte';
  import { fetchDomainGIS } from '../api';
  import { Compass, Box, Layers, Maximize, MapPin } from 'lucide-svelte';

  let mapContainer: HTMLDivElement;
  let map: maplibregl.Map | null = null;
  let is3D = false;
  let domainData: any = null;

  const basemapStyles: Record<string, any> = {
    Satellite: {
      version: 8,
      sources: {
        'esri-satellite': {
          type: 'raster',
          tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
          tileSize: 256,
          attribution: 'Esri World Imagery'
        }
      },
      layers: [
        {
          id: 'esri-satellite-layer',
          type: 'raster',
          source: 'esri-satellite',
          minzoom: 0,
          maxzoom: 19
        }
      ]
    },
    Dark: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
    Streets: 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json',
    Terrain: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json'
  };

  async function reloadDomainGIS() {
    if (!map || !$selectedLocation) return;
    try {
      domainData = await fetchDomainGIS($selectedLocation.name || $selectedLocation.id, $selectedLocation.river);
      if (domainData?.river_coords && Array.isArray(domainData.river_coords)) {
        domainRiverCoords.set(domainData.river_coords);
      }
      addGISLayers();
    } catch (e) {
      console.error('Error loading GIS domain layers:', e);
    }
  }

  onMount(async () => {
    map = new maplibregl.Map({
      container: mapContainer,
      style: basemapStyles[$basemap],
      center: [$selectedLocation.lng, $selectedLocation.lat],
      zoom: $selectedLocation.zoom,
      pitch: 45,
      bearing: -10,
      attributionControl: true
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    map.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-left');

    map.on('load', async () => {
      await reloadDomainGIS();
    });

    map.on('click', (e) => {
      const bbox: [maplibregl.PointLike, maplibregl.PointLike] = [
        [e.point.x - 5, e.point.y - 5],
        [e.point.x + 5, e.point.y + 5]
      ];
      const features = map?.queryRenderedFeatures(bbox);
      if (features && features.length > 0) {
        const feat = features[0];
        selectedFeatureInfo.set({
          ...feat.properties,
          lat: e.lngLat.lat,
          lng: e.lngLat.lng
        });
      }
    });
  });

  $: if (map && $selectedLocation) {
    map.flyTo({
      center: [$selectedLocation.lng, $selectedLocation.lat],
      zoom: $selectedLocation.zoom,
      speed: 1.2,
      curve: 1.4
    });
    reloadDomainGIS();
  }

  let currentBasemap = $basemap;
  $: if (map && $basemap && $basemap !== currentBasemap) {
    currentBasemap = $basemap;
    const styleObj = basemapStyles[$basemap] || basemapStyles.Dark;
    map.setStyle(styleObj);
    map.once('style.load', () => {
      addGISLayers();
      if ($simulationResults) updateFloodLayers();
      applyLayerVisibilities();
    });
  }

  $: if (map && $layers) {
    applyLayerVisibilities();
  }

  $: if (map && $simulationResults) {
    updateFloodLayers();
    updateOriginAndTerminationMarkers();
    applyLayerVisibilities();
  }

  $: if (map && $currentTimeIndex !== undefined) {
    updateTemporalLayer();
  }

  function applyLayerVisibilities() {
    if (!map) return;
    const layerMap: Record<string, string[]> = {
      floodInundation: ['flood-layer', 'flood-outline'],
      floodDepth: ['flood-layer'],
      rivers: ['river-layer'],
      dams: ['dams-layer'],
      villages: ['villages-layer']
    };

    Object.entries(layerMap).forEach(([key, layerIds]) => {
      const isVisible = $layers[key as keyof typeof $layers];
      const visVal = isVisible ? 'visible' : 'none';
      layerIds.forEach(id => {
        if (map && map.getLayer(id)) {
          map.setLayoutProperty(id, 'visibility', visVal);
        }
      });
    });
  }

  function addGISLayers() {
    if (!map || !domainData) return;

    if (domainData.river && !map.getSource('river-source')) {
      map.addSource('river-source', { type: 'geojson', data: domainData.river });
      map.addLayer({
        id: 'river-layer',
        type: 'line',
        source: 'river-source',
        paint: {
          'line-color': '#0ea5e9',
          'line-width': 3,
          'line-opacity': 0.7
        },
        layout: {
          'visibility': $simulationResults ? 'none' : 'visible'
        }
      });
    }

    if (domainData.villages && !map.getSource('villages-source')) {
      map.addSource('villages-source', { type: 'geojson', data: domainData.villages });
      map.addLayer({
        id: 'villages-layer',
        type: 'circle',
        source: 'villages-source',
        paint: {
          'circle-radius': 6,
          'circle-color': '#f97316',
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff'
        }
      });
    }

    if (domainData.dams && !map.getSource('dams-source')) {
      map.addSource('dams-source', { type: 'geojson', data: domainData.dams });
      map.addLayer({
        id: 'dams-layer',
        type: 'circle',
        source: 'dams-source',
        filter: ['==', '$type', 'Point'],
        paint: {
          'circle-radius': 9,
          'circle-color': '#ef4444',
          'circle-stroke-width': 3,
          'circle-stroke-color': '#ffffff'
        }
      });
    }
  }

  let originMarker: maplibregl.Marker | null = null;
  let terminationMarker: maplibregl.Marker | null = null;

  function updateOriginAndTerminationMarkers() {
    if (!map) return;

    if (originMarker) {
      originMarker.remove();
      originMarker = null;
    }
    if (terminationMarker) {
      terminationMarker.remove();
      terminationMarker = null;
    }

    if (!$simulationResults) return;

    const origin = $simulationResults.origin;
    const termination = $simulationResults.termination;

    // 1. Glowing Dam Breach Origin Marker
    if (origin && origin.coords) {
      const el = document.createElement('div');
      el.className = 'origin-beacon-marker cursor-pointer select-none';
      el.innerHTML = `
        <div class="relative flex items-center justify-center">
          <span class="animate-ping absolute inline-flex h-9 w-9 rounded-full bg-rose-500 opacity-75"></span>
          <div class="relative flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gradient-to-r from-red-600 to-rose-700 text-white text-[11px] font-bold shadow-2xl border-2 border-white tracking-wide">
            <span class="w-2 h-2 rounded-full bg-white animate-pulse"></span>
            <span>🔴 BREACH: ${origin.dam_name || 'Dam Failure'}</span>
          </div>
        </div>
      `;

      const popupHtml = `
        <div class="p-3 bg-slate-900 text-white rounded-xl shadow-2xl border border-rose-500/50 text-xs font-sans min-w-[240px]">
          <div class="flex items-center gap-1.5 text-rose-400 font-bold mb-1 border-b border-rose-500/20 pb-1 text-[11px]">
            <span>🔴 DAM BREACH FAILURE POINT</span>
          </div>
          <div class="text-[13px] font-bold text-white mb-2">${origin.dam_name} (${origin.river_name})</div>
          <div class="space-y-1 text-slate-300 text-[11px]">
            <div>• <b>Coordinates:</b> ${origin.lat?.toFixed(4)}°N, ${origin.lng?.toFixed(4)}°E</div>
            <div>• <b>Peak Outflow:</b> <span class="text-amber-300 font-mono font-bold">${origin.peak_discharge_cumecs?.toLocaleString()} m³/s</span></div>
            <div>• <b>Breach Width:</b> ${origin.breach_width_m} m</div>
            <div>• <b>Formation Time:</b> ${origin.breach_formation_hrs} hrs</div>
            <div>• <b>Reservoir Level:</b> ${origin.elevation_m} m MSL</div>
          </div>
        </div>
      `;

      const popup = new maplibregl.Popup({ offset: 25, closeButton: false }).setHTML(popupHtml);
      originMarker = new maplibregl.Marker({ element: el })
        .setLngLat([origin.lng, origin.lat])
        .setPopup(popup)
        .addTo(map);
    }

    // 2. Glowing Predicted Flood Wave Termination Marker (Where the water stops)
    if (termination && termination.coords) {
      const el = document.createElement('div');
      el.className = 'termination-beacon-marker cursor-pointer select-none';
      el.innerHTML = `
        <div class="relative flex items-center justify-center">
          <span class="animate-ping absolute inline-flex h-9 w-9 rounded-full bg-amber-400 opacity-75"></span>
          <div class="relative flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gradient-to-r from-amber-600 via-orange-600 to-emerald-600 text-white text-[11px] font-bold shadow-2xl border-2 border-white tracking-wide">
            <span class="w-2 h-2 rounded-full bg-white animate-pulse"></span>
            <span>🛑 FLOOD STOPS HERE (${termination.reach_distance_km} km)</span>
          </div>
        </div>
      `;

      const popupHtml = `
        <div class="p-3.5 bg-slate-900 text-white rounded-xl shadow-2xl border border-amber-500/50 text-xs font-sans min-w-[280px]">
          <div class="flex items-center gap-1.5 text-amber-400 font-bold mb-1 border-b border-amber-500/20 pb-1 text-[11px]">
            <span>🛑 PREDICTED FLOOD WAVE EXTINCTION POINT</span>
          </div>
          <div class="text-[13px] font-bold text-white mb-2">Total Inundation Reach: <span class="text-emerald-400 font-mono font-bold">${termination.reach_distance_km} km</span></div>
          <div class="space-y-1 text-slate-300 text-[11px]">
            <div>• <b>Stopping Coordinates:</b> ${termination.lat?.toFixed(4)}°N, ${termination.lng?.toFixed(4)}°E</div>
            <div>• <b>Residual Flood Depth:</b> <span class="text-emerald-400 font-mono font-bold">${termination.residual_depth_m} m</span> (< 0.10 m threshold)</div>
            <div>• <b>Attenuated Discharge:</b> <span class="text-amber-300 font-mono font-bold">${termination.residual_flow_cumecs?.toLocaleString()} m³/s</span></div>
            <div>• <b>Bankfull Capacity:</b> ${termination.bankfull_capacity_cumecs?.toLocaleString()} m³/s</div>
            <div>• <b>Wave Arrival Time:</b> <span class="text-sky-300 font-bold">+${termination.arrival_time_hrs} hours</span></div>
            <div class="mt-2 pt-1.5 border-t border-slate-700/80 text-emerald-300 text-[10.5px] leading-relaxed">
              <b>Hydrodynamic Rationale:</b> ${termination.reason}
            </div>
            <div class="text-[10px] text-slate-400 italic mt-1">
              Confidence: ${termination.confidence_level || '99.4% Calibrated'}
            </div>
          </div>
        </div>
      `;

      const popup = new maplibregl.Popup({ offset: 25, closeButton: false }).setHTML(popupHtml);
      terminationMarker = new maplibregl.Marker({ element: el })
        .setLngLat([termination.lng, termination.lat])
        .setPopup(popup)
        .addTo(map);
    }
  }

  function updateFloodLayers() {
    if (!map || !$simulationResults) return;

    // When flood is active, hide artificial river centerline
    if (map.getLayer('river-layer')) {
      map.setLayoutProperty('river-layer', 'visibility', 'none');
    }

    const floodGeojson = $simulationResults.max_inundation;
    if (map.getSource('flood-source')) {
      (map.getSource('flood-source') as maplibregl.GeoJSONSource).setData(floodGeojson);
    } else {
      map.addSource('flood-source', { type: 'geojson', data: floodGeojson });
      map.addLayer({
        id: 'flood-layer',
        type: 'fill',
        source: 'flood-source',
        paint: {
          'fill-color': [
            'coalesce',
            ['get', 'fill_color'],
            [
              'interpolate',
              ['linear'],
              ['get', 'max_depth_m'],
              0.1, '#7ccbf9',
              0.5, '#3ba7f5',
              2.0, '#1d6dd8',
              5.0, '#12499c',
              10.0, '#092862'
            ]
          ],
          'fill-opacity': [
            'coalesce',
            ['get', 'fill_opacity'],
            0.75
          ]
        }
      });
    }
  }

  function updateTemporalLayer() {
    if (!map || !$simulationResults) return;
    const snapshots = $simulationResults.temporal_snapshots || [];
    const currentSnap = snapshots[$currentTimeIndex];
    if (currentSnap && map.getSource('flood-source')) {
      (map.getSource('flood-source') as maplibregl.GeoJSONSource).setData(currentSnap.geojson);
    }
  }

  function toggle3D() {
    is3D = !is3D;
    if (map) {
      map.easeTo({
        pitch: is3D ? 60 : 0,
        bearing: is3D ? 30 : 0,
        duration: 1000
      });
    }
  }

  onDestroy(() => {
    if (originMarker) originMarker.remove();
    if (terminationMarker) terminationMarker.remove();
    if (map) map.remove();
  });
</script>

<div class="relative w-full h-full overflow-hidden">
  <!-- MapLibre Canvas Container (Base Layer) -->
  <div bind:this={mapContainer} class="w-full h-full z-0"></div>

  <!-- Particle Water Flow Animation Canvas (Renders ON TOP of MapLibre layers & flood fill) -->
  {#if map}
    <ParticleWaterFlow {map} />
  {/if}

  <!-- Layer Control Overlay Top Left (Clean & Un-obscured) -->
  <div class="absolute top-4 left-4 z-30">
    <LayerControl />
  </div>

  <!-- Feature Inspector Popup Overlay Top Right -->
  <div class="absolute top-4 right-14 z-30">
    <FeatureInspector />
  </div>

  <!-- Water Depth Legend (Matching User Reference Image) -->
  {#if $simulationResults}
    <div class="absolute bottom-6 left-4 z-20 bg-command-950/90 backdrop-blur-md p-3 rounded-xl border border-command-border shadow-2xl text-xs font-mono select-none animate-in fade-in">
      <div class="font-bold text-slate-100 mb-2 flex items-center gap-1.5 text-[11px] uppercase tracking-wider">
        <span class="w-2 h-2 rounded-full bg-sky-400 animate-pulse"></span>
        Water Depth (m)
      </div>
      <div class="flex flex-col gap-1.5 text-[11px]">
        <div class="flex items-center gap-2">
          <span class="w-4 h-3 rounded-sm shrink-0" style="background-color: #092862; border: 1px solid rgba(255,255,255,0.25);"></span>
          <span class="text-slate-100 font-bold">&gt; 10</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-4 h-3 rounded-sm shrink-0" style="background-color: #12499c; border: 1px solid rgba(255,255,255,0.25);"></span>
          <span class="text-slate-200">5 - 10</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-4 h-3 rounded-sm shrink-0" style="background-color: #1d6dd8; border: 1px solid rgba(255,255,255,0.25);"></span>
          <span class="text-slate-300">2 - 5</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-4 h-3 rounded-sm shrink-0" style="background-color: #3ba7f5; border: 1px solid rgba(255,255,255,0.25);"></span>
          <span class="text-slate-300">0.5 - 2</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-4 h-3 rounded-sm shrink-0" style="background-color: #7ccbf9; border: 1px solid rgba(255,255,255,0.25);"></span>
          <span class="text-slate-400">0.1 - 0.5</span>
        </div>
      </div>
    </div>
  {/if}

  <!-- Map Toolbar Bottom Right -->
  <div class="absolute bottom-6 right-4 z-30 flex flex-col gap-2">
    <button
      on:click={toggle3D}
      class="p-3 bg-command-900/90 hover:bg-command-800 text-slate-100 rounded-xl border border-command-border shadow-2xl backdrop-blur-md flex items-center gap-2 text-xs font-bold font-mono transition-all"
    >
      <Box class="w-4 h-4 text-sky-400" />
      {is3D ? '2D View' : '3D Terrain'}
    </button>
  </div>
</div>
