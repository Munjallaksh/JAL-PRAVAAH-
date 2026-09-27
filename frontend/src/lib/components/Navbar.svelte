<script lang="ts">
  import { activeTab, type NavTab } from '../store';
  import { Compass, Waves, Satellite, AlertTriangle, GitCompare, Database } from 'lucide-svelte';
  import SearchBar from './SearchBar.svelte';

  const tabs: { id: NavTab; label: string; icon: any }[] = [
    { id: 'EXPLORE', label: 'EXPLORE', icon: Compass },
    { id: 'SIMULATE', label: 'SIMULATE', icon: Waves },
    { id: 'OBSERVE', label: 'OBSERVE', icon: Satellite },
    { id: 'IMPACT', label: 'IMPACT', icon: AlertTriangle },
    { id: 'COMPARE', label: 'COMPARE', icon: GitCompare },
    { id: 'DATASOURCES', label: 'DATA SOURCES', icon: Database }
  ];
</script>

<header class="h-16 bg-command-900 border-b border-command-border px-4 flex items-center justify-between z-40 shrink-0 select-none gap-4">
  <!-- Brand / Title -->
  <div class="flex items-center gap-3 shrink-0">
    <div class="w-10 h-10 rounded-xl overflow-hidden bg-white/95 p-0.5 border border-sky-400/40 shadow-lg shadow-sky-500/10 flex items-center justify-center shrink-0 group">
      <img
        src="/assets/jal-pravaah-logo.png"
        alt="JAL PRAVAAH Logo"
        class="w-full h-full object-contain group-hover:scale-105 transition-transform duration-200"
      />
    </div>
    <div class="hidden sm:block">
      <h1 class="text-sm font-extrabold text-slate-100 tracking-wider flex items-center gap-2">
        JAL PRAVAAH
      </h1>
      <p class="text-[10px] text-slate-400 font-mono">Hydrodynamic Decision Support Platform</p>
    </div>
  </div>

  <!-- Prominent Location Search Bar in Header Center -->
  <div class="flex-1 max-w-md mx-2">
    <SearchBar />
  </div>

  <!-- Navigation Tabs -->
  <nav class="flex items-center gap-1 bg-command-950/60 p-1 rounded-xl border border-command-border shrink-0">
    {#each tabs as tab}
      {@const Icon = tab.icon}
      <button
        on:click={() => activeTab.set(tab.id)}
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wider transition-all duration-200
          {$activeTab === tab.id 
            ? 'bg-water-deep text-white shadow-lg shadow-sky-500/20 border border-sky-400/30' 
            : 'text-slate-400 hover:text-slate-200 hover:bg-command-800/50'}"
      >
        <Icon class="w-3.5 h-3.5" />
        <span class="hidden lg:inline">{tab.label}</span>
      </button>
    {/each}
  </nav>

  <!-- Status Badge -->
  <div class="hidden xl:flex items-center gap-2 text-[11px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-1 rounded-full shrink-0">
    <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
    READY
  </div>
</header>
