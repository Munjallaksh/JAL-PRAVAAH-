<script lang="ts">
  import { Search, MapPin, ChevronRight, X } from 'lucide-svelte';
  import { searchLocations } from '../api';
  import { selectedLocation, type LocationItem } from '../store';

  let searchQuery = '';
  let searchResults: LocationItem[] = [];
  let isSearching = false;
  let isOpen = false;

  async function handleInput() {
    if (!searchQuery.trim()) {
      searchResults = [];
      isOpen = false;
      return;
    }
    isSearching = true;
    isOpen = true;
    try {
      searchResults = await searchLocations(searchQuery);
    } catch (e) {
      searchResults = [];
    } finally {
      isSearching = false;
    }
  }

  function selectItem(item: LocationItem) {
    selectedLocation.set(item);
    isOpen = false;
    searchQuery = item.name;
  }

  function clearSearch() {
    searchQuery = '';
    searchResults = [];
    isOpen = false;
  }
</script>

<div class="relative w-full max-w-xl">
  <div class="relative flex items-center">
    <Search class="absolute left-3.5 w-4 h-4 text-slate-400" />
    <input
      type="text"
      bind:value={searchQuery}
      on:input={handleInput}
      placeholder="Search dam, river, city, village or district... (e.g. Tehri Dam, Rishikesh)"
      class="w-full bg-command-900/90 text-slate-100 placeholder-slate-400 pl-10 pr-10 py-2.5 rounded-xl border border-command-border text-xs focus:outline-none focus:border-water/50 focus:ring-1 focus:ring-water/30 shadow-xl backdrop-blur-md"
    />
    {#if searchQuery}
      <button on:click={clearSearch} class="absolute right-3 text-slate-400 hover:text-slate-200">
        <X class="w-4 h-4" />
      </button>
    {/if}
  </div>

  {#if isOpen && searchResults.length > 0}
    <div class="absolute top-full left-0 right-0 mt-2 bg-command-900/95 border border-command-border rounded-xl shadow-2xl overflow-hidden z-50 backdrop-blur-md max-h-72 overflow-y-auto">
      {#each searchResults as item}
        <button
          on:click={() => selectItem(item)}
          class="w-full text-left px-4 py-2.5 flex items-center justify-between hover:bg-water-deep/20 transition-colors border-b border-command-border/40 last:border-0"
        >
          <div class="flex items-center gap-3">
            <div class="p-1.5 bg-water/10 text-water-light rounded-lg">
              <MapPin class="w-4 h-4" />
            </div>
            <div>
              <div class="text-xs font-semibold text-slate-100">{item.name}</div>
              <div class="text-[10px] text-slate-400 font-mono">
                {item.type} • {item.river} • {item.state}, {item.country}
              </div>
            </div>
          </div>
          <ChevronRight class="w-4 h-4 text-slate-500" />
        </button>
      {/each}
    </div>
  {/if}
</div>
