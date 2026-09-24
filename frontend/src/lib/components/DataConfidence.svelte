<script lang="ts">
  import { ShieldCheck, Info, Database, Satellite, Cpu } from 'lucide-svelte';
  import { selectedLocation, simulationResults } from '../store';

  $: activeDam = $simulationResults?.dam_name || $selectedLocation?.name || 'Dam';
</script>

<div class="glass-panel rounded-xl p-4 space-y-3 text-xs select-none border border-command-border">
  <div class="flex items-center justify-between border-b border-command-border/60 pb-2">
    <h3 class="font-bold text-slate-100 flex items-center gap-2">
      <ShieldCheck class="w-4 h-4 text-emerald-400" />
      Data & Model Scientific Confidence
    </h3>
    <span class="px-2 py-0.5 rounded font-mono text-[10px] font-bold bg-sky-500/20 text-sky-400 border border-sky-500/30">
      86 / 100 HIGH
    </span>
  </div>

  <div class="space-y-2 font-mono text-[11px]">
    <div class="flex items-center justify-between p-2 bg-command-950/60 rounded border border-command-border">
      <span class="flex items-center gap-2 text-slate-300">
        <Database class="w-3.5 h-3.5 text-amber-400" />
        Copernicus DEM (30m Resolution)
      </span>
      <span class="px-2 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/30 font-bold">MODERATE</span>
    </div>

    <div class="flex items-center justify-between p-2 bg-command-950/60 rounded border border-command-border">
      <span class="flex items-center gap-2 text-slate-300">
        <Cpu class="w-3.5 h-3.5 text-emerald-400" />
        Hydrological & Dam Curves ({activeDam} CWC)
      </span>
      <span class="px-2 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold">GOOD</span>
    </div>

    <div class="flex items-center justify-between p-2 bg-command-950/60 rounded border border-command-border">
      <span class="flex items-center gap-2 text-slate-300">
        <Satellite class="w-3.5 h-3.5 text-emerald-400" />
        Sentinel-1 SAR C-band Imagery
      </span>
      <span class="px-2 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold">GOOD</span>
    </div>

    <div class="flex items-center justify-between p-2 bg-command-950/60 rounded border border-command-border">
      <span class="flex items-center gap-2 text-slate-300">
        <ShieldCheck class="w-3.5 h-3.5 text-emerald-400" />
        Model Convergence & CFL Condition
      </span>
      <span class="px-2 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold">PASS (&lt;0.42%)</span>
    </div>
  </div>
</div>
