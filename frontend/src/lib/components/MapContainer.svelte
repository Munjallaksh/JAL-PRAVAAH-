<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { selectedLocation, layers, basemap, simulationResults, currentTimeIndex, selectedFeatureInfo } from '../store';
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
      domainData = await fetchDomainGIS($selectedLocation.name || $selectedLocation.id);
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
          'line-width': 4,
          'line-opacity': 0.85
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

  function updateFloodLayers() {
    if (!map || !$simulationResults) return;

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
            'interpolate',
            ['linear'],
            ['get', 'max_depth_m'],
            0, '#c084fc',
            1, '#7dd3fc',
            3, '#0284c7',
            7, '#1e40af',
            15, '#312e81'
          ],
          'fill-opacity': 0.65
        }
      });

      map.addLayer({
        id: 'flood-outline',
        type: 'line',
        source: 'flood-source',
        paint: {
          'line-color': '#a855f7',
          'line-width': 1.5,
          'line-opacity': 0.6
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
