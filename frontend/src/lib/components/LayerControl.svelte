<script lang="ts">
  import { layers, basemap } from '../store';
  import { Layers, Eye, EyeOff, Map, Droplets, ShieldAlert, Activity, ChevronDown, ChevronUp } from 'lucide-svelte';

  let isOpen = false; // Default collapsed so it doesn't block map or search bar

  function toggleLayer(key: keyof typeof $layers) {
    layers.update(l => ({ ...l, [key]: !l[key] }));
  }

  $: activeCount = Object.values($layers).filter(Boolean).length;
</script>

<div class="relative z-30 select-none">
  <!-- Sleek Compact Trigger Button -->
  <button
    on:click={() => isOpen = !isOpen}
    class="glass-panel px-3.5 py-2 rounded-xl flex items-center gap-2.5 font-semibold text-xs text-slate-100 shadow-2xl border border-command-border hover:bg-command-800/80 transition-all"
  >
    <div class="p-1 bg-water-deep/30 rounded-lg text-water-light">
      <Layers class="w-4 h-4" />
    </div>
    <span class="font-semibold tracking-wide">Map Layers & Basemap</span>
    <span class="px-1.5 py-0.5 rounded-full text-[10px] font-mono bg-sky-500/20 text-sky-400 border border-sky-500/30">
      {activeCount} Active
    </span>
    {#if isOpen}
      <ChevronUp class="w-3.5 h-3.5 text-slate-400" />
    {:else}
      <ChevronDown class="w-3.5 h-3.5 text-slate-400" />
    {/if}
  </button>

  <!-- Expanded Popover Panel (Positioned safely below button without overlapping SearchBar or Left Panel) -->
  {#if isOpen}
    <div class="absolute top-full left-0 mt-2 glass-panel-dark rounded-2xl p-3.5 shadow-2xl border border-command-border text-xs w-72 space-y-3.5 max-h-[70vh] overflow-y-auto animate-in fade-in zoom-in duration-200">
      <!-- Basemap Selector -->
      <div>
        <div class="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <Map class="w-3.5 h-3.5 text-sky-400" />
          Basemap Mode
        </div>
        <div class="grid grid-cols-2 gap-1.5">
          {#each ['Satellite', 'Terrain', 'Streets', 'Dark'] as mode}
            <button
              on:click={() => basemap.set(mode)}
              class="px-2.5 py-1.5 rounded-lg text-[11px] font-medium border text-center transition-all
                {$basemap === mode
                  ? 'bg-water-deep/40 border-water-light text-white font-bold shadow-lg shadow-sky-500/20'
                  : 'bg-command-950/40 border-command-border text-slate-400 hover:text-slate-200'}"
            >
              {mode}
            </button>
          {/each}
        </div>
      </div>

      <div class="h-px bg-command-border/40"></div>

      <!-- Simulation Layers -->
      <div>
        <div class="text-[10px] font-mono font-bold text-sky-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <Droplets class="w-3.5 h-3.5" />
          Simulation Output Layers
        </div>
        <div class="space-y-1">
          <button on:click={() => toggleLayer('floodInundation')} class="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-command-800/50 text-slate-200 text-[11px] font-medium">
            <span>Flood Inundation Zone</span>
            {#if $layers.floodInundation}<Eye class="w-3.5 h-3.5 text-sky-400" />{:else}<EyeOff class="w-3.5 h-3.5 text-slate-500" />{/if}
          </button>
          <button on:click={() => toggleLayer('floodDepth')} class="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-command-800/50 text-slate-200 text-[11px] font-medium">
            <span>Depth Classification</span>
            {#if $layers.floodDepth}<Eye class="w-3.5 h-3.5 text-sky-400" />{:else}<EyeOff class="w-3.5 h-3.5 text-slate-500" />{/if}
          </button>
          <button on:click={() => toggleLayer('arrivalTime')} class="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-command-800/50 text-slate-200 text-[11px] font-medium">
            <span>Arrival Time Map</span>
            {#if $layers.arrivalTime}<Eye class="w-3.5 h-3.5 text-amber-400" />{:else}<EyeOff class="w-3.5 h-3.5 text-slate-500" />{/if}
          </button>
        </div>
      </div>

      <div class="h-px bg-command-border/40"></div>

      <!-- Hydrology & Features -->
      <div>
        <div class="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider mb-2">Geospatial Base Features</div>
        <div class="space-y-1">
          <button on:click={() => toggleLayer('rivers')} class="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-command-800/50 text-slate-300 text-[11px]">
            <span>Rivers & River Reaches</span>
            {#if $layers.rivers}<Eye class="w-3.5 h-3.5 text-emerald-400" />{:else}<EyeOff class="w-3.5 h-3.5 text-slate-500" />{/if}
          </button>
          <button on:click={() => toggleLayer('dams')} class="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-command-800/50 text-slate-300 text-[11px]">
            <span>Dams & Reservoirs</span>
            {#if $layers.dams}<Eye class="w-3.5 h-3.5 text-emerald-400" />{:else}<EyeOff class="w-3.5 h-3.5 text-slate-500" />{/if}
          </button>
          <button on:click={() => toggleLayer('villages')} class="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-command-800/50 text-slate-300 text-[11px]">
            <span>Settlements & Population</span>
            {#if $layers.villages}<Eye class="w-3.5 h-3.5 text-amber-400" />{:else}<EyeOff class="w-3.5 h-3.5 text-slate-500" />{/if}
          </button>
          <button on:click={() => toggleLayer('infrastructure')} class="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-command-800/50 text-slate-300 text-[11px]">
            <span>Roads & Infrastructure</span>
            {#if $layers.infrastructure}<Eye class="w-3.5 h-3.5 text-purple-400" />{:else}<EyeOff class="w-3.5 h-3.5 text-slate-500" />{/if}
          </button>
        </div>
      </div>

      <!-- Depth Legend -->
      {#if $layers.floodInundation || $layers.floodDepth}
        <div class="h-px bg-command-border/40"></div>
        <div class="p-2.5 bg-command-950/80 rounded-xl border border-command-border/50 space-y-1 font-mono">
          <div class="text-[10px] text-slate-300 font-bold mb-1">Flood Depth Legend</div>
          <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-sm bg-[#7dd3fc]"></span><span class="text-[10px] text-slate-300">0.0 - 0.5 m (Low)</span></div>
          <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-sm bg-[#38bdf8]"></span><span class="text-[10px] text-slate-300">0.5 - 1.0 m (Moderate)</span></div>
          <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-sm bg-[#0284c7]"></span><span class="text-[10px] text-slate-300">1.0 - 2.0 m (High)</span></div>
          <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-sm bg-[#1e40af]"></span><span class="text-[10px] text-slate-300">2.0 - 5.0 m (Severe)</span></div>
          <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-sm bg-[#581c87]"></span><span class="text-[10px] text-slate-300">&gt; 5.0 m (Catastrophic)</span></div>
        </div>
      {/if}
    </div>
  {/if}
</div>
