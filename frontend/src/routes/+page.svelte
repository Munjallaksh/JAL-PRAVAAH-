<script lang="ts">
  import Navbar from '../lib/components/Navbar.svelte';
  import MapContainer from '../lib/components/MapContainer.svelte';
  import SimulationPanel from '../lib/components/SimulationPanel.svelte';
  import ResultsPanel from '../lib/components/ResultsPanel.svelte';
  import TimelineControl from '../lib/components/TimelineControl.svelte';
  import WhatIfLab from '../lib/components/WhatIfLab.svelte';
  import SphVsDelft3d from '../lib/components/SphVsDelft3d.svelte';
  import ObserveModule from '../lib/components/ObserveModule.svelte';
  import HadrPriority from '../lib/components/HadrPriority.svelte';
  import DataConfidence from '../lib/components/DataConfidence.svelte';
  import DataSourcesModule from '../lib/components/DataSourcesModule.svelte';
  import { activeTab, simulationResults } from '../lib/store';
</script>

<div class="flex flex-col h-screen w-screen bg-command-950 overflow-hidden text-slate-100 select-none">
  <!-- Top Command Center Navbar -->
  <Navbar />

  <!-- Main Viewport Area -->
  <div class="flex-1 flex relative overflow-hidden">
    <!-- Left Panel: Parameters & Domain Info (20-25% width) -->
    <aside class="w-80 lg:w-96 p-3 bg-command-950/90 border-r border-command-border z-20 flex flex-col gap-3 overflow-y-auto shrink-0 backdrop-blur-md">
      {#if $activeTab === 'SIMULATE'}
        <SimulationPanel />
      {:else}
        <SimulationPanel />
        <DataConfidence />
      {/if}
    </aside>

    <!-- Center: Interactive GIS Map Viewport (60-70% width) -->
    <main class="flex-1 relative h-full">
      <MapContainer />

      <!-- Bottom Overlay: Timeline Scrubber -->
      {#if $simulationResults}
        <div class="absolute bottom-4 left-4 right-4 z-20 max-w-4xl mx-auto">
          <TimelineControl />
        </div>
      {/if}
    </main>

    <!-- Right Panel: Results & HADR Priority (20-25% width) -->
    <aside class="w-80 lg:w-96 p-3 bg-command-950/90 border-l border-command-border z-20 flex flex-col gap-3 overflow-y-auto shrink-0 backdrop-blur-md">
      <ResultsPanel />
    </aside>
  </div>

  <!-- Bottom Drawer for Tab-specific Analytical Views (OBSERVE, IMPACT, COMPARE, DATASOURCES) -->
  {#if $activeTab === 'IMPACT'}
    <div class="absolute inset-x-0 bottom-0 top-16 z-40 bg-command-950/95 backdrop-blur-xl p-6 overflow-y-auto animate-in slide-in-from-bottom duration-300">
      <div class="max-w-6xl mx-auto space-y-6">
        <HadrPriority />
        <WhatIfLab />
      </div>
    </div>
  {:else if $activeTab === 'COMPARE'}
    <div class="absolute inset-x-0 bottom-0 top-16 z-40 bg-command-950/95 backdrop-blur-xl p-6 overflow-y-auto animate-in slide-in-from-bottom duration-300">
      <div class="max-w-6xl mx-auto space-y-6">
        <SphVsDelft3d />
      </div>
    </div>
  {:else if $activeTab === 'OBSERVE'}
    <div class="absolute inset-x-0 bottom-0 top-16 z-40 bg-command-950/95 backdrop-blur-xl p-6 overflow-y-auto animate-in slide-in-from-bottom duration-300">
      <div class="max-w-6xl mx-auto space-y-6">
        <ObserveModule />
      </div>
    </div>
  {:else if $activeTab === 'DATASOURCES'}
    <div class="absolute inset-x-0 bottom-0 top-16 z-40 bg-command-950/95 backdrop-blur-xl overflow-hidden animate-in slide-in-from-bottom duration-300">
      <DataSourcesModule />
    </div>
  {/if}
</div>
