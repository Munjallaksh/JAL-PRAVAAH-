<script lang="ts">
  import { selectedFeatureInfo } from '../store';
  import { MapPin, X, AlertTriangle, ShieldCheck, Activity } from 'lucide-svelte';

  function close() {
    selectedFeatureInfo.set(null);
  }

  $: info = $selectedFeatureInfo;
</script>

{#if info}
  <div class="glass-panel-dark rounded-xl p-3.5 border border-command-border shadow-2xl w-72 text-xs space-y-2 select-none">
    <div class="flex items-center justify-between border-b border-command-border/60 pb-2">
      <div class="font-bold text-slate-100 flex items-center gap-1.5 text-xs">
        <MapPin class="w-3.5 h-3.5 text-water-light" />
        {info.name || 'Map Location Feature'}
      </div>
      <button on:click={close} class="text-slate-400 hover:text-slate-200">
        <X class="w-4 h-4" />
      </button>
    </div>

    <div class="space-y-1.5 font-mono text-[11px]">
      <div class="flex justify-between text-slate-300">
        <span>Coordinates:</span>
        <span class="text-slate-100">{info.lat?.toFixed(4)}°N, {info.lng?.toFixed(4)}°E</span>
      </div>

      {#if info.flood_depth_m !== undefined}
        <div class="flex justify-between text-slate-300">
          <span>Flood Depth:</span>
          <span class="text-sky-400 font-bold">{info.flood_depth_m} m</span>
        </div>
        <div class="flex justify-between text-slate-300">
          <span>Flow Velocity:</span>
          <span class="text-slate-100">{info.velocity_mps} m/s</span>
        </div>
        <div class="flex justify-between text-slate-300">
          <span>Arrival Time:</span>
          <span class="text-amber-400 font-bold">{info.arrival_time_min} mins</span>
        </div>
        <div class="flex justify-between text-slate-300">
          <span>Hazard Class:</span>
          <span class="px-1.5 py-0.2 rounded text-[10px] font-bold text-white bg-rose-500">
            {info.hazard_class || 'HIGH'}
          </span>
        </div>
      {:else if info.population !== undefined}
        <div class="flex justify-between text-slate-300">
          <span>Population:</span>
          <span class="text-rose-400 font-bold">{info.population?.toLocaleString()}</span>
        </div>
        <div class="flex justify-between text-slate-300">
          <span>Elevation:</span>
          <span class="text-slate-100">{info.elevation_m} m</span>
        </div>
        <div class="flex justify-between text-slate-300">
          <span>Downstream Dist:</span>
          <span class="text-slate-100">{info.distance_downstream_km} km</span>
        </div>
      {/if}
    </div>
  </div>
{/if}
