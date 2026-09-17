<script lang="ts">
  import { simulationResults } from '../store';
  import { ShieldAlert, AlertTriangle, Hospital, Navigation, Users, Clock, ArrowRight, ExternalLink } from 'lucide-svelte';

  $: priorities = $simulationResults?.hadr_priorities || [];
</script>

<div class="space-y-4 select-none">
  <!-- Disclaimer Alert -->
  <div class="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-start gap-3 text-xs text-amber-300">
    <AlertTriangle class="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
    <div>
      <div class="font-bold text-amber-200">HADR DECISION-SUPPORT OUTPUT — RECOMMENDATION MATRIX</div>
      <div class="text-[11px] text-amber-300/90 font-mono mt-0.5">
        Multi-factor priority ranking based on modeled flood depth, arrival time, population density, hospital density, and road accessibility.
        <strong>Decision-support output — not an authoritative evacuation order.</strong>
      </div>
    </div>
  </div>

  {#if priorities.length > 0}
    <!-- Priority Table -->
    <div class="glass-panel rounded-xl overflow-hidden border border-command-border shadow-xl">
      <div class="p-3 bg-command-900 border-b border-command-border flex justify-between items-center text-xs font-bold text-slate-200">
        <span class="flex items-center gap-2">
          <ShieldAlert class="w-4 h-4 text-rose-400" />
          Emergency Response Priority Action List
        </span>
        <span class="font-mono text-[10px] text-slate-400">{priorities.length} Affected Settlements Ranked</span>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-command-950/80 text-slate-400 font-mono text-[10px] uppercase border-b border-command-border">
            <tr>
              <th class="p-3">Rank</th>
              <th class="p-3">Settlement</th>
              <th class="p-3">District</th>
              <th class="p-3">Priority Level</th>
              <th class="p-3">Pop. Exposed</th>
              <th class="p-3">Flood Arrival</th>
              <th class="p-3">Max Depth</th>
              <th class="p-3">Road Access</th>
              <th class="p-3">Recommended HADR Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-command-border/40 font-mono">
            {#each priorities as item, idx}
              <tr class="hover:bg-command-800/40 transition-colors">
                <td class="p-3 font-bold text-slate-300">#{idx + 1}</td>
                <td class="p-3 font-bold text-slate-100">{item.name}</td>
                <td class="p-3 text-slate-400">{item.district}</td>
                <td class="p-3">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold text-white shadow" style="background-color: {item.badge_color}">
                    {item.priority_level}
                  </span>
                </td>
                <td class="p-3 font-bold text-rose-400">{item.population?.toLocaleString()}</td>
                <td class="p-3 text-amber-400 font-bold">{item.arrival_time_formatted}</td>
                <td class="p-3 text-sky-400">{item.max_depth_m}m</td>
                <td class="p-3">
                  <span class="px-2 py-0.5 rounded text-[9px] font-bold border
                    {item.road_access_status === 'CUT_OFF' ? 'bg-rose-500/20 text-rose-300 border-rose-500/30' : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'}">
                    {item.road_access_status}
                  </span>
                </td>
                <td class="p-3 font-sans text-[11px] text-slate-300 leading-tight max-w-xs">{item.recommended_action}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {:else}
    <div class="glass-panel rounded-xl p-8 text-center text-slate-400 text-xs space-y-2 border border-command-border">
      <ShieldAlert class="w-8 h-8 text-slate-600 mx-auto" />
      <p class="font-semibold text-slate-300">No HADR Priority Data Available</p>
      <p class="text-[11px] text-slate-500">Run a simulation scenario in the SIMULATE tab to compute HADR decision priorities.</p>
    </div>
  {/if}
</div>
