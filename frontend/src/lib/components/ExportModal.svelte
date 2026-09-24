<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { activeJobId, selectedLocation, simulationResults } from '../store';
  import { Download, FileText, Globe, FileSpreadsheet, FileArchive, X, MapPin } from 'lucide-svelte';

  const dispatch = createEventDispatcher();

  function close() {
    dispatch('close');
  }

  function getDownloadUrl(format: string) {
    return `/api/exports/${$activeJobId}/${format}`;
  }

  $: damName = $simulationResults?.dam_name || $selectedLocation?.name || 'Dam';
  $: riverName = $simulationResults?.river_name || $selectedLocation?.river || 'River Reach';
</script>

<div class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 select-none">
  <div class="glass-panel-dark rounded-2xl p-6 max-w-lg w-full border border-command-border space-y-5 shadow-2xl animate-in fade-in zoom-in duration-200">
    <div class="flex items-center justify-between border-b border-command-border pb-3">
      <div class="flex items-center gap-2 text-slate-100 font-bold text-sm">
        <Download class="w-5 h-5 text-sky-400" />
        Export GIS Datasets & PDF Report
      </div>
      <button on:click={close} class="p-1 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-command-800">
        <X class="w-5 h-5" />
      </button>
    </div>

    <div class="flex items-center justify-between text-xs text-slate-300 font-mono bg-command-950/60 p-2.5 rounded-lg border border-command-border">
      <div>
        Scenario ID: <strong class="text-sky-400">{$activeJobId}</strong>
      </div>
      <div class="flex items-center gap-1.5 text-emerald-400 font-semibold truncate max-w-[260px]">
        <MapPin class="w-3.5 h-3.5 shrink-0" />
        <span class="truncate">{damName} ({riverName})</span>
      </div>
    </div>

    <!-- Export Buttons Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
      <!-- Shapefile ZIP -->
      <a
        href={getDownloadUrl('shp')}
        download
        class="p-3 bg-command-900 hover:bg-command-800 border border-command-border rounded-xl flex items-center gap-3 text-left transition-all hover:border-sky-500/50 group"
      >
        <div class="p-2 bg-sky-500/10 text-sky-400 rounded-lg group-hover:scale-110 transition-transform">
          <FileArchive class="w-5 h-5" />
        </div>
        <div>
          <div class="text-xs font-bold text-slate-100">Shapefile Bundle (.ZIP)</div>
          <div class="text-[10px] text-slate-400 font-mono">.SHP, .SHX, .DBF, .PRJ</div>
        </div>
      </a>

      <!-- GeoJSON -->
      <a
        href={getDownloadUrl('geojson')}
        download
        class="p-3 bg-command-900 hover:bg-command-800 border border-command-border rounded-xl flex items-center gap-3 text-left transition-all hover:border-sky-500/50 group"
      >
        <div class="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg group-hover:scale-110 transition-transform">
          <Globe class="w-5 h-5" />
        </div>
        <div>
          <div class="text-xs font-bold text-slate-100">GeoJSON Vector</div>
          <div class="text-[10px] text-slate-400 font-mono">WGS84 EPSG:4326</div>
        </div>
      </a>

      <!-- KML -->
      <a
        href={getDownloadUrl('kml')}
        download
        class="p-3 bg-command-900 hover:bg-command-800 border border-command-border rounded-xl flex items-center gap-3 text-left transition-all hover:border-sky-500/50 group"
      >
        <div class="p-2 bg-purple-500/10 text-purple-400 rounded-lg group-hover:scale-110 transition-transform">
          <Globe class="w-5 h-5" />
        </div>
        <div>
          <div class="text-xs font-bold text-slate-100">Google Earth KML</div>
          <div class="text-[10px] text-slate-400 font-mono">3D Terrain Polygon</div>
        </div>
      </a>

      <!-- CSV -->
      <a
        href={getDownloadUrl('csv')}
        download
        class="p-3 bg-command-900 hover:bg-command-800 border border-command-border rounded-xl flex items-center gap-3 text-left transition-all hover:border-sky-500/50 group"
      >
        <div class="p-2 bg-amber-500/10 text-amber-400 rounded-lg group-hover:scale-110 transition-transform">
          <FileSpreadsheet class="w-5 h-5" />
        </div>
        <div>
          <div class="text-xs font-bold text-slate-100">CSV Priority Matrix</div>
          <div class="text-[10px] text-slate-400 font-mono">Settlement Breakdown</div>
        </div>
      </a>
    </div>

    <!-- PDF Report Full Banner -->
    <a
      href={getDownloadUrl('pdf')}
      download
      class="w-full p-4 bg-gradient-to-r from-sky-600 to-blue-700 hover:from-sky-500 hover:to-blue-600 rounded-xl text-white flex items-center justify-between shadow-xl transition-all group"
    >
      <div class="flex items-center gap-3">
        <FileText class="w-6 h-6 group-hover:scale-110 transition-transform" />
        <div class="text-left">
          <div class="text-xs font-bold">Download {damName} Executive Report (PDF)</div>
          <div class="text-[10px] text-sky-200 font-mono">Decision-support summary for {damName} on {riverName}</div>
        </div>
      </div>
      <Download class="w-5 h-5" />
    </a>
  </div>
</div>
