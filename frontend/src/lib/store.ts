import { writable } from 'svelte/store';

export type NavTab = 'EXPLORE' | 'SIMULATE' | 'OBSERVE' | 'IMPACT' | 'COMPARE';

export interface LocationItem {
  id: string;
  name: string;
  type: string;
  state: string;
  country: string;
  river: string;
  lat: number;
  lng: number;
  zoom: number;
  dam_height_m?: number;
  reservoir_level_m?: number;
  reservoir_volume_mcm?: number;
  description?: string;
}

export interface LayerState {
  floodInundation: boolean;
  floodDepth: boolean;
  arrivalTime: boolean;
  rivers: boolean;
  dams: boolean;
  villages: boolean;
  infrastructure: boolean;
  sentinelObservation: boolean;
}

export const activeTab = writable<NavTab>('EXPLORE');

export const selectedLocation = writable<LocationItem>({
  id: 'loc-tehri-dam',
  name: 'Tehri Dam',
  type: 'Dam / Reservoir',
  state: 'Uttarakhand',
  country: 'India',
  river: 'Bhagirathi River',
  lat: 30.3781,
  lng: 78.4803,
  zoom: 12,
  dam_height_m: 260.5,
  reservoir_level_m: 820.0,
  reservoir_volume_mcm: 3540.0,
  description: 'Highest dam in India, primary reservoir on Bhagirathi River above Rishikesh & Haridwar.'
});

export const basemap = writable<'Satellite' | 'Terrain' | 'Streets' | 'Dark'>('Satellite');

export const layers = writable<LayerState>({
  floodInundation: true,
  floodDepth: false,
  arrivalTime: false,
  rivers: true,
  dams: true,
  villages: true,
  infrastructure: true,
  sentinelObservation: false
});

export const activeJobId = writable<string | null>(null);
export const jobStatus = writable<any>(null);
export const simulationResults = writable<any>(null);

// Timeline Scrubber
export const currentTimeIndex = writable<number>(0);
export const isTimelinePlaying = writable<boolean>(false);

// Inspector Modal
export const selectedFeatureInfo = writable<any>(null);
