<script lang="ts">
  import { selectedLocation } from '../store';
  import { startSimulation, fetchSimulationResults } from '../api';
  import { Layers, Plus, TrendingUp, AlertTriangle, ArrowRight } from 'lucide-svelte';

  interface ScenarioCard {
    id: string;
    name: string;
    breachWidth: number;
    formationTime: number;
    results: any;
    isLoading: boolean;
  }

  let scenarios: ScenarioCard[] = [
    { id: 'scn-a', name: 'Scenario A (50m Breach)', breachWidth: 50, formationTime: 45, results: null, isLoading: false },
    { id: 'scn-b', name: 'Scenario B (100m Breach)', breachWidth: 100, formationTime: 30, results: null, isLoading: false },
    { id: 'scn-c', name: 'Scenario C (200m Breach)', breachWidth: 200, formationTime: 15, results: null, isLoading: false }
  ];

  async function runScenario(index: number) {
    const scn = scenarios[index];
    scn.isLoading = true;
    scenarios = [...scenarios];

    try {
      const launch = await startSimulation({
        scenario_type: 'DAM_BREAK',
        dam_name: $selectedLocation.name,
        river_name: $selectedLocation.river,
        reservoir_level_m: 820.0,
        reservoir_volume_mcm: 3540.0,
        dam_height_m: 260.5,
        breach_width_m: scn.breachWidth,
        breach_formation_time_min: scn.formationTime,
        simulation_duration_hours: 6,
        engine_type: 'SPH'
      });

      // Poll until done
      setTimeout(async () => {
        const res = await fetchSimulationResults(launch.job_id);
        scn.results = res;
        scn.isLoading = false;
        scenarios = [...scenarios];
      }, 1500);
    } catch (e) {
      scn.isLoading = false;
      scenarios = [...scenarios];
    }
  }

  function runAll() {
    runScenario(0);
    runScenario(1);
    runScenario(2);
  }

  // Calculate percentage deltas live
  $: popA = scenarios[0].results?.impact_summary?.population_exposed || 0;
  $: popC = scenarios[2].results?.impact_summary?.population_exposed || 0;
  $: popDeltaPct = popA > 0 ? Math.round(((popC - popA) / popA) * 100) : 0;
</script>

<div class="space-y-4 select-none">
  <div class="flex items-center justify-between">
    <div>
      <h3 class="text-sm font-bold text-slate-100 flex items-center gap-2">
        <Layers class="w-4 h-4 text-sky-400" />
        What-If Scenario Laboratory
      </h3>
      <p class="text-xs text-slate-400 font-mono">Evaluate multi-breach geometry sensitivity & dynamic population exposure deltas.</p>
    </div>
    <button
      on:click={runAll}
      class="px-4 py-2 bg-water-deep hover:bg-water text-white font-bold rounded-lg text-xs shadow-lg flex items-center gap-2"
    >
      Run All 3 Scenarios
    </button>
  </div>

  <!-- Cards Grid -->
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    {#each scenarios as scn, idx}
      <div class="glass-panel p-4 rounded-xl border border-command-border space-y-3">
        <div class="flex items-center justify-between border-b border-command-border/60 pb-2">
          <span class="font-bold text-xs text-slate-200">{scn.name}</span>
          <span class="text-[10px] font-mono text-slate-400">Breach: {scn.breachWidth}m</span>
        </div>

        {#if scn.results}
          <div class="space-y-2 font-mono text-xs">
            <div class="flex justify-between text-slate-300">
              <span>Peak Flow:</span>
              <strong class="text-sky-400">{scn.results.peak_flow_cumecs?.toLocaleString()} m³/s</strong>
            </div>
            <div class="flex justify-between text-slate-300">
              <span>Inundated Area:</span>
              <strong class="text-slate-100">{scn.results.impact_summary?.inundated_area_sqkm} km²</strong>
            </div>
            <div class="flex justify-between text-slate-300">
              <span>Max Depth:</span>
              <strong class="text-amber-400">{scn.results.max_depth_m} m</strong>
            </div>
            <div class="flex justify-between text-slate-300">
              <span>Pop. Exposed:</span>
              <strong class="text-rose-400">{scn.results.impact_summary?.population_exposed?.toLocaleString()}</strong>
            </div>
          </div>
        {:else}
          <div class="py-8 text-center text-slate-500 text-xs">
            {#if scn.isLoading}
              <div class="text-sky-400 animate-pulse font-mono">Running Hydrodynamics...</div>
            {:else}
              <button on:click={() => runScenario(idx)} class="px-3 py-1.5 bg-command-800 hover:bg-command-700 text-slate-300 rounded text-xs">
                Run {scn.name}
              </button>
            {/if}
          </div>
        {/if}
      </div>
    {/each}
  </div>

  <!-- Dynamic Analytical Insights Card -->
  {#if scenarios[0].results && scenarios[2].results}
    <div class="p-4 bg-sky-500/10 border border-sky-500/30 rounded-xl flex items-center justify-between text-xs">
      <div class="flex items-center gap-3">
        <TrendingUp class="w-6 h-6 text-sky-400 shrink-0" />
        <div>
          <div class="font-bold text-slate-100">Calculated Multi-Scenario Impact Insights</div>
          <div class="text-slate-300 text-xs font-mono">
            Scenario C (200m breach) exposes <strong class="text-rose-400">{popDeltaPct}% more population</strong> than Scenario A (50m breach) along the Ganges valley reach.
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>
