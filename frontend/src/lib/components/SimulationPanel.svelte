<script lang="ts">
  import { selectedLocation, activeJobId, jobStatus, simulationResults } from '../store';
  import { startSimulation, pollSimulationStatus, fetchSimulationResults } from '../api';
  import { Play, AlertCircle, RefreshCw, Cpu, Layers, Info, CheckCircle2 } from 'lucide-svelte';

  let scenarioType = 'DAM_BREAK';
  let engineType = 'SPH';
  let breachWidth = 100;
  let breachDepth = 150;
  let formationTime = 30;
  let releaseDischarge = 8000;
  let duration = 6;
  let manningN = 0.035;

  let isRunning = false;
  let progressPercent = 0;
  let progressStep = '';
  let warnings: string[] = [];
  let errorMsg = '';

  async function handleRunSimulation() {
    isRunning = true;
    errorMsg = '';
    warnings = [];
    progressPercent = 5;
    progressStep = 'Initializing scenario configuration...';

    try {
      const params = {
        scenario_type: scenarioType,
        dam_name: $selectedLocation.name,
        river_name: $selectedLocation.river,
        reservoir_level_m: $selectedLocation.reservoir_level_m || 820.0,
        reservoir_volume_mcm: $selectedLocation.reservoir_volume_mcm || 3540.0,
        dam_height_m: $selectedLocation.dam_height_m || 260.5,
        breach_width_m: breachWidth,
        breach_depth_m: breachDepth,
        breach_formation_time_min: formationTime,
        release_discharge_cumecs: releaseDischarge,
        mannings_n: manningN,
        simulation_duration_hours: duration,
        engine_type: engineType
      };

      const launchRes = await startSimulation(params);
      activeJobId.set(launchRes.job_id);
      warnings = launchRes.warnings || [];

      const timer = setInterval(async () => {
        try {
          const statusRes = await pollSimulationStatus(launchRes.job_id);
          jobStatus.set(statusRes);
          progressPercent = statusRes.progress_percent;
          progressStep = statusRes.current_step;

          if (statusRes.status === 'COMPLETE') {
            clearInterval(timer);
            const results = await fetchSimulationResults(launchRes.job_id);
            simulationResults.set(results);
            isRunning = false;
          } else if (statusRes.status === 'FAILED') {
            clearInterval(timer);
            errorMsg = statusRes.error || 'Simulation execution failed.';
            isRunning = false;
          }
        } catch (err) {
          clearInterval(timer);
          isRunning = false;
        }
      }, 500);

    } catch (e: any) {
      errorMsg = e.message || 'Error launching simulation.';
      isRunning = false;
    }
  }
</script>

<div class="glass-panel rounded-xl p-4 space-y-4 text-xs select-none border border-command-border">
  <div class="flex items-center justify-between border-b border-command-border/60 pb-3">
    <h2 class="font-bold text-slate-100 flex items-center gap-2 text-sm">
      <Cpu class="w-4 h-4 text-water-light" />
      Simulation Parameters
    </h2>
    <span class="px-2 py-0.5 rounded font-mono text-[10px] bg-command-800 text-slate-300">
      {$selectedLocation.name}
    </span>
  </div>

  <!-- Scenario Type Tabs -->
  <div>
    <span class="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Scenario Type</span>
    <div class="grid grid-cols-3 gap-1 bg-command-950/60 p-1 rounded-lg border border-command-border">
      <button
        on:click={() => scenarioType = 'DAM_BREAK'}
        class="py-1.5 px-2 rounded font-medium text-center transition-all {scenarioType === 'DAM_BREAK' ? 'bg-water-deep text-white shadow' : 'text-slate-400 hover:text-slate-200'}"
      >
        Dam Break
      </button>
      <button
        on:click={() => scenarioType = 'SUDDEN_WATER_RELEASE'}
        class="py-1.5 px-2 rounded font-medium text-center transition-all {scenarioType === 'SUDDEN_WATER_RELEASE' ? 'bg-water-deep text-white shadow' : 'text-slate-400 hover:text-slate-200'}"
      >
        Water Release
      </button>
      <button
        on:click={() => scenarioType = 'NATURAL_RIVER_BLOCKAGE'}
        class="py-1.5 px-2 rounded font-medium text-center transition-all {scenarioType === 'NATURAL_RIVER_BLOCKAGE' ? 'bg-water-deep text-white shadow' : 'text-slate-400 hover:text-slate-200'}"
      >
        River Blockage
      </button>
    </div>
  </div>

  <!-- Model Engine Selector -->
  <div>
    <span class="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Hydrodynamic Engine</span>
    <div class="space-y-1.5">
      <label class="flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all {engineType === 'SPH' ? 'bg-sky-500/10 border-sky-400 text-slate-100' : 'bg-command-950/30 border-command-border text-slate-400'}">
        <div class="flex items-center gap-2">
          <input type="radio" name="engine" value="SPH" bind:group={engineType} class="accent-sky-400" />
          <span class="font-semibold text-xs">Smooth Particle Hydrodynamics (SPH)</span>
        </div>
        <span class="text-[10px] font-mono text-sky-400">2D Meshless</span>
      </label>

      <label class="flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all {engineType === 'DELFT3D' ? 'bg-sky-500/10 border-sky-400 text-slate-100' : 'bg-command-950/30 border-command-border text-slate-400'}">
        <div class="flex items-center gap-2">
          <input type="radio" name="engine" value="DELFT3D" bind:group={engineType} class="accent-sky-400" />
          <span class="font-semibold text-xs">Delft3D / Delft3D-FM</span>
        </div>
        <span class="text-[10px] font-mono text-amber-400">Flexible Mesh</span>
      </label>

      <label class="flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all {engineType === 'DEMO_HYDRAULIC' ? 'bg-sky-500/10 border-sky-400 text-slate-100' : 'bg-command-950/30 border-command-border text-slate-400'}">
        <div class="flex items-center gap-2">
          <input type="radio" name="engine" value="DEMO_HYDRAULIC" bind:group={engineType} class="accent-sky-400" />
          <span class="font-semibold text-xs">Simplified 2D Hydraulic Wave Model</span>
        </div>
        <span class="text-[10px] font-mono text-slate-400">Deterministic</span>
      </label>
    </div>
  </div>

  <!-- Dynamic Inputs based on Scenario -->
  {#if scenarioType === 'DAM_BREAK'}
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label for="bw" class="block text-[10px] font-mono text-slate-400 mb-1">Breach Width (m)</label>
        <input id="bw" type="number" bind:value={breachWidth} min="10" max="600" class="w-full bg-command-950 text-slate-100 px-3 py-1.5 rounded border border-command-border font-mono text-xs focus:border-water-light outline-none" />
      </div>
      <div>
        <label for="ft" class="block text-[10px] font-mono text-slate-400 mb-1">Breach Formation (min)</label>
        <input id="ft" type="number" bind:value={formationTime} min="5" max="300" class="w-full bg-command-950 text-slate-100 px-3 py-1.5 rounded border border-command-border font-mono text-xs focus:border-water-light outline-none" />
      </div>
    </div>
  {:else if scenarioType === 'SUDDEN_WATER_RELEASE'}
    <div>
      <label for="sd" class="block text-[10px] font-mono text-slate-400 mb-1">Spillway Discharge (m³/s)</label>
      <input id="sd" type="number" bind:value={releaseDischarge} step="500" min="1000" max="40000" class="w-full bg-command-950 text-slate-100 px-3 py-1.5 rounded border border-command-border font-mono text-xs focus:border-water-light outline-none" />
    </div>
  {/if}

  <div class="grid grid-cols-2 gap-3">
    <div>
      <label for="dur" class="block text-[10px] font-mono text-slate-400 mb-1">Duration (Hours)</label>
      <input id="dur" type="number" bind:value={duration} min="1" max="24" class="w-full bg-command-950 text-slate-100 px-3 py-1.5 rounded border border-command-border font-mono text-xs focus:border-water-light outline-none" />
    </div>
    <div>
      <label for="mn" class="block text-[10px] font-mono text-slate-400 mb-1">Manning's n</label>
      <input id="mn" type="number" bind:value={manningN} step="0.005" min="0.015" max="0.08" class="w-full bg-command-950 text-slate-100 px-3 py-1.5 rounded border border-command-border font-mono text-xs focus:border-water-light outline-none" />
    </div>
  </div>

  <!-- Validation Warnings -->
  {#if warnings.length > 0}
    <div class="p-2.5 bg-amber-500/10 border border-amber-500/30 rounded-lg text-amber-300 text-[11px] space-y-1">
      {#each warnings as w}
        <div class="flex items-start gap-1.5">
          <AlertCircle class="w-3.5 h-3.5 shrink-0 mt-0.5 text-amber-400" />
          <span>{w}</span>
        </div>
      {/each}
    </div>
  {/if}

  <!-- Errors -->
  {#if errorMsg}
    <div class="p-2.5 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-300 text-[11px]">
      {errorMsg}
    </div>
  {/if}

  <!-- Progress Bar during simulation -->
  {#if isRunning}
    <div class="space-y-1.5 p-3 bg-command-950/80 rounded-lg border border-sky-500/30">
      <div class="flex justify-between text-[11px] font-mono text-sky-400">
        <span>{progressStep}</span>
        <span>{progressPercent}%</span>
      </div>
      <div class="w-full bg-command-800 rounded-full h-2 overflow-hidden">
        <div class="bg-water-light h-full transition-all duration-300" style="width: {progressPercent}%"></div>
      </div>
    </div>
  {/if}

  <!-- Run Action Button -->
  <button
    on:click={handleRunSimulation}
    disabled={isRunning}
    class="w-full py-3 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-bold rounded-xl shadow-lg shadow-sky-500/25 flex items-center justify-center gap-2 text-xs transition-all disabled:opacity-50"
  >
    {#if isRunning}
      <RefreshCw class="w-4 h-4 animate-spin" />
      Simulating Hydrodynamics...
    {:else}
      <Play class="w-4 h-4 fill-white" />
      Run Hydrodynamic Simulation
    {/if}
  </button>
</div>
