<script lang="ts">
  import { fetchModelComparison } from '../api';
  import { GitCompare, CheckCircle2, AlertTriangle, Layers, Info } from 'lucide-svelte';
  import { onMount } from 'svelte';

  let mode: 'SIDE_BY_SIDE' | 'DIFFERENCE' = 'SIDE_BY_SIDE';
  let comparisonData: any = null;
  let isLoading = true;

  onMount(async () => {
    try {
      comparisonData = await fetchModelComparison({
        scenario_type: 'DAM_BREAK',
        breach_width_m: 100,
        breach_formation_time_min: 30,
        simulation_duration_hours: 6,
        engine_type: 'SPH'
      });
    } catch (e) {
      console.error(e);
    } finally {
      isLoading = false;
    }
  });
</script>

<div class="space-y-4 select-none">
  <!-- Mode Selector Header -->
  <div class="flex items-center justify-between bg-command-900/90 p-3 rounded-xl border border-command-border">
    <div class="flex items-center gap-3">
      <div class="p-2 bg-purple-500/10 text-purple-400 rounded-lg">
        <GitCompare class="w-5 h-5" />
      </div>
      <div>
        <h3 class="text-sm font-bold text-slate-100">SPH vs Delft3D Model Comparison</h3>
        <p class="text-xs text-slate-400 font-mono">Evaluate meshless particle dynamics vs Delft3D-FM curvilinear shallow-water solver.</p>
      </div>
    </div>

    <div class="flex items-center gap-1 bg-command-950 p-1 rounded-lg border border-command-border text-xs font-semibold">
      <button
        on:click={() => mode = 'SIDE_BY_SIDE'}
        class="px-3 py-1 rounded transition-all {mode === 'SIDE_BY_SIDE' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-slate-200'}"
      >
        Side-by-Side View
      </button>
      <button
        on:click={() => mode = 'DIFFERENCE'}
        class="px-3 py-1 rounded transition-all {mode === 'DIFFERENCE' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-slate-200'}"
      >
        Difference Map
      </button>
    </div>
  </div>

  {#if isLoading}
    <div class="p-8 text-center text-purple-400 font-mono text-xs animate-pulse">
      Computing SPH particle mesh vs Delft3D-FM spatial delta metrics...
    </div>
  {:else if comparisonData}
    <!-- Numerical Comparison Table -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div class="glass-panel p-3 rounded-xl border border-command-border text-center">
        <div class="text-[10px] font-mono text-slate-400 uppercase">Intersection over Union (IoU)</div>
        <div class="text-lg font-bold text-purple-400 font-mono">{comparisonData.comparison_metrics.iou_similarity}</div>
        <div class="text-[9px] text-slate-400">High Mesh Agreement</div>
      </div>
      <div class="glass-panel p-3 rounded-xl border border-command-border text-center">
        <div class="text-[10px] font-mono text-slate-400 uppercase">Area Delta</div>
        <div class="text-lg font-bold text-slate-100 font-mono">{comparisonData.comparison_metrics.area_difference_sqkm} km²</div>
        <div class="text-[9px] text-slate-400">Spatial Extent Variation</div>
      </div>
      <div class="glass-panel p-3 rounded-xl border border-command-border text-center">
        <div class="text-[10px] font-mono text-slate-400 uppercase">Depth RMSE</div>
        <div class="text-lg font-bold text-sky-400 font-mono">{comparisonData.comparison_metrics.depth_rmse_m} m</div>
        <div class="text-[9px] text-slate-400">Root Mean Square Error</div>
      </div>
      <div class="glass-panel p-3 rounded-xl border border-command-border text-center">
        <div class="text-[10px] font-mono text-slate-400 uppercase">Arrival Time Delta</div>
        <div class="text-lg font-bold text-amber-400 font-mono">{comparisonData.comparison_metrics.arrival_time_delta_min} min</div>
        <div class="text-[9px] text-slate-400">Wave Front Discrepancy</div>
      </div>
    </div>

    <!-- Models Comparison Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- SPH Card -->
      <div class="glass-panel p-4 rounded-xl border border-command-border space-y-2">
        <div class="flex items-center justify-between border-b border-command-border/60 pb-2">
          <span class="font-bold text-xs text-sky-400">Smooth Particle Hydrodynamics (SPH)</span>
          <span class="text-[10px] font-mono text-slate-400">2D Meshless</span>
        </div>
        <div class="space-y-1 font-mono text-xs text-slate-300">
          <div>Peak Flow: <strong class="text-slate-100">{comparisonData.sph_model.peak_flow_cumecs?.toLocaleString()} m³/s</strong></div>
          <div>Max Depth: <strong class="text-slate-100">{comparisonData.sph_model.max_depth_m} m</strong></div>
          <div>Kernel: <strong class="text-slate-100">Cubic Spline W(r,h)</strong></div>
        </div>
      </div>

      <!-- Delft3D Card -->
      <div class="glass-panel p-4 rounded-xl border border-command-border space-y-2">
        <div class="flex items-center justify-between border-b border-command-border/60 pb-2">
          <span class="font-bold text-xs text-purple-400">Delft3D / Delft3D-FM</span>
          <span class="text-[10px] font-mono text-amber-400">Flexible Mesh</span>
        </div>
        <div class="space-y-1 font-mono text-xs text-slate-300">
          <div>Peak Flow: <strong class="text-slate-100">{comparisonData.delft3d_model.peak_flow_cumecs?.toLocaleString()} m³/s</strong></div>
          <div>Max Depth: <strong class="text-slate-100">{comparisonData.delft3d_model.max_depth_m} m</strong></div>
          <div>Status: <strong class="text-slate-100">{comparisonData.delft3d_model.configured ? 'Executable Active' : 'Adapter (Reference Grid)'}</strong></div>
        </div>
      </div>
    </div>

    <!-- Difference Map Explanation Legend -->
    {#if mode === 'DIFFERENCE'}
      <div class="p-3 bg-command-900 rounded-xl border border-command-border flex items-center justify-around text-xs font-mono">
        <div class="flex items-center gap-2"><span class="w-3 h-3 bg-sky-500 rounded"></span><span>SPH Only Extent</span></div>
        <div class="flex items-center gap-2"><span class="w-3 h-3 bg-purple-500 rounded"></span><span>Delft3D Only Extent</span></div>
        <div class="flex items-center gap-2"><span class="w-3 h-3 bg-emerald-500 rounded"></span><span>Model Agreement (Intersection)</span></div>
      </div>
    {/if}
  {/if}
</div>
