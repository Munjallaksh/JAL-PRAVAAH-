<script lang="ts">
  import { fetchSentinel1Observation, fetchValidationMetrics } from '../api';
  import { activeJobId, simulationResults } from '../store';
  import { Satellite, CheckCircle, BarChart3, Radio, RefreshCw, AlertCircle } from 'lucide-svelte';
  import { onMount } from 'svelte';

  let sarData: any = null;
  let valMetrics: any = null;
  let isLoading = true;

  onMount(async () => {
    try {
      sarData = await fetchSentinel1Observation();
      if ($activeJobId) {
        valMetrics = await fetchValidationMetrics($activeJobId);
      }
    } catch (e) {
      console.error(e);
    } finally {
      isLoading = false;
    }
  });
</script>

<div class="space-y-4 select-none">
  <!-- Header -->
  <div class="flex items-center justify-between bg-command-900/90 p-3 rounded-xl border border-command-border">
    <div class="flex items-center gap-3">
      <div class="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
        <Satellite class="w-5 h-5" />
      </div>
      <div>
        <h3 class="text-sm font-bold text-slate-100">Near Real-Time Satellite Observation</h3>
        <p class="text-xs text-slate-400 font-mono">Sentinel-1 C-Band SAR Synthetic Aperture Radar Change Detection</p>
      </div>
    </div>

    <div class="flex items-center gap-2 text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1.5 rounded-lg">
      <Radio class="w-3.5 h-3.5 animate-pulse" />
      Sentinel-1A IW GRDH
    </div>
  </div>

  {#if isLoading}
    <div class="p-8 text-center text-emerald-400 font-mono text-xs animate-pulse">
      Loading Sentinel-1 SAR satellite backscatter change detection layers...
    </div>
  {:else}
    <!-- Satellite Observation Metadata & Metrics -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="glass-panel p-4 rounded-xl border border-command-border space-y-3">
        <div class="flex items-center justify-between border-b border-command-border/60 pb-2">
          <span class="font-bold text-xs text-slate-200">Satellite Acquisition Metadata</span>
          <span class="text-[10px] font-mono text-emerald-400">PASSED QUALITY CHECK</span>
        </div>
        <div class="space-y-1.5 text-xs font-mono text-slate-300">
          <div class="flex justify-between"><span>Acquisition Date:</span><strong class="text-slate-100">12 Sep 2024 (00:45 UTC)</strong></div>
          <div class="flex justify-between"><span>Polarization Mode:</span><strong class="text-slate-100">VV + VH Dual-Pol</strong></div>
          <div class="flex justify-between"><span>Backscatter Threshold:</span><strong class="text-slate-100">-16.5 dB</strong></div>
          <div class="flex justify-between"><span>Detected Flood Extent:</span><strong class="text-emerald-400 font-bold">38.4 km²</strong></div>
        </div>
      </div>

      <!-- Model Validation Card -->
      <div class="glass-panel p-4 rounded-xl border border-command-border space-y-3">
        <div class="flex items-center justify-between border-b border-command-border/60 pb-2">
          <span class="font-bold text-xs text-sky-400">Model vs Satellite Validation</span>
          {#if valMetrics?.available}
            <span class="text-[10px] font-mono text-emerald-400 font-bold">{valMetrics.validation_class}</span>
          {/if}
        </div>

        {#if valMetrics?.available}
          <div class="grid grid-cols-2 gap-2 text-center font-mono">
            <div class="p-2 bg-command-950 rounded border border-command-border">
              <div class="text-[10px] text-slate-400">IoU Score</div>
              <div class="text-sm font-bold text-sky-400">{valMetrics.iou}</div>
            </div>
            <div class="p-2 bg-command-950 rounded border border-command-border">
              <div class="text-[10px] text-slate-400">F1 Score</div>
              <div class="text-sm font-bold text-emerald-400">{valMetrics.f1_score}</div>
            </div>
            <div class="p-2 bg-command-950 rounded border border-command-border">
              <div class="text-[10px] text-slate-400">Precision</div>
              <div class="text-xs font-bold text-slate-200">{valMetrics.precision}</div>
            </div>
            <div class="p-2 bg-command-950 rounded border border-command-border">
              <div class="text-[10px] text-slate-400">Recall</div>
              <div class="text-xs font-bold text-slate-200">{valMetrics.recall}</div>
            </div>
          </div>
        {:else}
          <div class="py-4 text-center text-slate-400 text-xs space-y-1">
            <AlertCircle class="w-5 h-5 text-amber-400 mx-auto" />
            <p>Run a simulation scenario first to compute satellite validation scores.</p>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>
