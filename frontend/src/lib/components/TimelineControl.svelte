<script lang="ts">
  import { simulationResults, currentTimeIndex, isTimelinePlaying } from '../store';
  import { Play, Pause, RotateCcw, FastForward, Clock } from 'lucide-svelte';
  import { onDestroy } from 'svelte';

  let speedMultiplier = 1;
  let timer: any = null;

  $: snapshots = $simulationResults?.temporal_snapshots || [];
  $: currentSnapshot = snapshots[$currentTimeIndex] || null;

  function togglePlay() {
    if ($isTimelinePlaying) {
      stop();
    } else {
      start();
    }
  }

  function start() {
    if (snapshots.length === 0) return;
    isTimelinePlaying.set(true);
    timer = setInterval(() => {
      currentTimeIndex.update(i => {
        if (i >= snapshots.length - 1) {
          stop();
          return i;
        }
        return i + 1;
      });
    }, 1200 / speedMultiplier);
  }

  function stop() {
    isTimelinePlaying.set(false);
    if (timer) clearInterval(timer);
  }

  function reset() {
    stop();
    currentTimeIndex.set(0);
  }

  function setSpeed(spd: number) {
    speedMultiplier = spd;
    if ($isTimelinePlaying) {
      stop();
      start();
    }
  }

  onDestroy(() => {
    if (timer) clearInterval(timer);
  });
</script>

{#if snapshots.length > 0}
  <div class="glass-panel-dark rounded-xl p-3 border border-command-border shadow-2xl flex items-center gap-4 text-xs select-none">
    <!-- Playback Controls -->
    <div class="flex items-center gap-1.5 shrink-0">
      <button
        on:click={togglePlay}
        class="p-2 rounded-lg bg-water-deep hover:bg-water text-white shadow-md transition-all"
        title={$isTimelinePlaying ? 'Pause' : 'Play'}
      >
        {#if $isTimelinePlaying}<Pause class="w-4 h-4" />{:else}<Play class="w-4 h-4 fill-white" />{/if}
      </button>

      <button
        on:click={reset}
        class="p-2 rounded-lg bg-command-800 hover:bg-command-700 text-slate-300 transition-all"
        title="Reset Timeline"
      >
        <RotateCcw class="w-4 h-4" />
      </button>
    </div>

    <!-- Timeline Slider -->
    <div class="flex-1 space-y-1">
      <div class="flex justify-between items-center text-[10px] font-mono text-slate-400">
        <span class="flex items-center gap-1">
          <Clock class="w-3 h-3 text-sky-400" />
          Simulation Elapsed Time:
          <strong class="text-slate-100">{currentSnapshot?.formatted_time || '0 min'}</strong>
        </span>
        <span>Wave Front: <strong class="text-sky-400">{currentSnapshot?.geojson?.features[0]?.properties?.wave_front_km || 0} km</strong> downstream</span>
      </div>

      <input
        type="range"
        min="0"
        max={snapshots.length - 1}
        bind:value={$currentTimeIndex}
        class="w-full h-1.5 bg-command-800 rounded-lg appearance-none cursor-pointer accent-sky-400"
      />
    </div>

    <!-- Speed Multiplier -->
    <div class="flex items-center gap-1 bg-command-900/80 p-1 rounded-lg border border-command-border shrink-0">
      {#each [1, 2, 5] as spd}
        <button
          on:click={() => setSpeed(spd)}
          class="px-2 py-0.5 rounded text-[10px] font-mono font-bold transition-all
            {speedMultiplier === spd ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30' : 'text-slate-400 hover:text-slate-200'}"
        >
          {spd}x
        </button>
      {/each}
    </div>
  </div>
{/if}
