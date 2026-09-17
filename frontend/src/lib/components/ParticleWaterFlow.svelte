<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { simulationResults, currentTimeIndex, selectedLocation } from '../store';
  import type maplibregl from 'maplibre-gl';

  export let map: maplibregl.Map | null = null;

  let canvas: HTMLCanvasElement;
  let animId: number;
  
  interface SPHParticle {
    x_progress: number;       // 0.0 (dam breach) to 1.0 (downstream end)
    offset_lateral: number;   // -1.0 to 1.0 lateral dispersion across channel width
    speed: number;            // Flow velocity along reach
    size: number;             // Particle radius (pixels)
    alpha: number;            // Transparency
    color: string;            // SPH fluid color
  }

  let particles: SPHParticle[] = [];
  const PARTICLE_COUNT = 6000; // 6,000 High-density SPH hydrodynamics fluid particles

  const particleColors = [
    '#38bdf8', // Bright aqua cyan
    '#0ea5e9', // Hydro azure
    '#0284c7', // Deep blue
    '#60a5fa', // Electric blue
    '#7dd3fc', // Bright aqua
    '#3b82f6', // Pure water blue
    '#e0f2fe'  // Foam white-blue
  ];

  function initParticles() {
    particles = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x_progress: Math.random(),
        offset_lateral: (Math.random() - 0.5) * 2.2,
        speed: 0.0015 + Math.random() * 0.0035,
        size: 1.6 + Math.random() * 2.6,
        alpha: 0.45 + Math.random() * 0.50,
        color: particleColors[Math.floor(Math.random() * particleColors.length)]
      });
    }
  }

  function getActiveRiverCoords(): [number, number][] {
    // 1. Extract midline of current simulation flood extent polygon
    if ($simulationResults?.max_inundation?.features[0]?.geometry?.coordinates[0]) {
      const poly = $simulationResults.max_inundation.features[0].geometry.coordinates[0];
      if (poly && poly.length > 4) {
        const half = Math.floor(poly.length / 2);
        const midline: [number, number][] = [];
        for (let i = 0; i < half; i++) {
          const p1 = poly[i];
          const p2 = poly[poly.length - 2 - i] || p1;
          midline.push([(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2]);
        }
        if (midline.length >= 3) {
          return midline;
        }
      }
    }

    // 2. Dynamic river reach for active location
    const centerLng = $selectedLocation?.lng || 78.4803;
    const centerLat = $selectedLocation?.lat || 30.3781;

    const riverPath: [number, number][] = [];
    const numPoints = 16;
    const dLat = centerLat > 20.0 ? -0.028 : -0.020;
    const dLng = centerLng > 78.0 ? -0.022 : 0.025;

    for (let i = 0; i < numPoints; i++) {
      const meander = Math.sin(i * 0.65) * 0.018;
      const ptLat = centerLat + i * dLat + meander;
      const ptLng = centerLng + i * dLng + meander * 0.7;
      riverPath.push([ptLng, ptLat]);
    }

    return riverPath;
  }

  function getActiveFloodPolygon(): [number, number][] | null {
    if (!$simulationResults) return null;

    const snapshots = $simulationResults.temporal_snapshots || [];
    if (snapshots.length > 0) {
      const idx = Math.min($currentTimeIndex, snapshots.length - 1);
      const snapPoly = snapshots[idx]?.geojson?.features[0]?.geometry?.coordinates[0];
      if (snapPoly && snapPoly.length > 3) {
        return snapPoly;
      }
    }

    const maxPoly = $simulationResults.max_inundation?.features[0]?.geometry?.coordinates[0];
    if (maxPoly && maxPoly.length > 3) {
      return maxPoly;
    }

    return null;
  }

  function isPointInPolygon(pt: [number, number], poly: [number, number][]): boolean {
    const x = pt[0];
    const y = pt[1];
    let inside = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      const xi = poly[i][0], yi = poly[i][1];
      const xj = poly[j][0], yj = poly[j][1];
      const intersect = ((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi + 1e-10) + xi);
      if (intersect) inside = !inside;
    }
    return inside;
  }

  function interpolatePoint(path: [number, number][], progress: number): [number, number] {
    if (path.length === 0) return [0, 0];
    if (path.length === 1) return path[0];

    const totalSegs = path.length - 1;
    const scaledProg = Math.max(0, Math.min(1.0, progress)) * totalSegs;
    const segIdx = Math.min(Math.floor(scaledProg), totalSegs - 1);
    const rem = scaledProg - segIdx;

    const p1 = path[segIdx];
    const p2 = path[segIdx + 1] || p1;

    const lng = p1[0] + (p2[0] - p1[0]) * rem;
    const lat = p1[1] + (p2[1] - p1[1]) * rem;

    return [lng, lat];
  }

  function updateCanvasDimensions() {
    if (!canvas || !map) return;
    const mapCanvas = map.getCanvas();
    if (mapCanvas) {
      if (canvas.width !== mapCanvas.clientWidth || canvas.height !== mapCanvas.clientHeight) {
        canvas.width = mapCanvas.clientWidth;
        canvas.height = mapCanvas.clientHeight;
      }
    }
  }

  function draw() {
    if (!canvas || !map) {
      animId = requestAnimationFrame(draw);
      return;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) {
      animId = requestAnimationFrame(draw);
      return;
    }

    updateCanvasDimensions();
    const width = canvas.width;
    const height = canvas.height;

    if (width === 0 || height === 0) {
      animId = requestAnimationFrame(draw);
      return;
    }

    ctx.clearRect(0, 0, width, height);

    const riverPath = getActiveRiverCoords();
    const activePoly = getActiveFloodPolygon();
    const snapshots = $simulationResults?.temporal_snapshots || [];
    
    // Wave front marker position for active timeline scrubber
    const waveFrontPosition = snapshots.length > 0
      ? Math.min(1.0, ($currentTimeIndex + 1) / snapshots.length)
      : 1.0;

    // Simulation hydraulic velocity scale
    const baseVelMps = $simulationResults?.max_inundation?.features[0]?.properties?.max_velocity_mps || 5.0;
    const velScale = $simulationResults ? Math.min(2.0, Math.max(0.6, baseVelMps / 4.0)) : 1.0;

    for (let p of particles) {
      // 1. Calculate base position along river reach
      const [lng, lat] = interpolatePoint(riverPath, p.x_progress);

      // Lateral channel width spreading expands inside flooded plain
      const isFloodedZone = $simulationResults ? (p.x_progress <= waveFrontPosition) : false;
      const isWaveFront = snapshots.length > 0 && Math.abs(p.x_progress - waveFrontPosition) < 0.035;

      const spreadMultiplier = isFloodedZone ? 3.0 : 1.2;
      const widthOffset = 0.0032 * p.offset_lateral * (1.0 + p.x_progress * spreadMultiplier);
      let ptLng = lng + widthOffset;
      let ptLat = lat - widthOffset * 0.45;

      // 2. Flood Boundary & Terrain Constraint Enforcement
      let insideFlood = true;
      if (activePoly && $simulationResults) {
        insideFlood = isPointInPolygon([ptLng, ptLat], activePoly);

        // If lateral offset pushes particle outside active flood polygon, pull it inward
        if (!insideFlood) {
          p.offset_lateral *= 0.82;
          const adjustedOffset = 0.0032 * p.offset_lateral * (1.0 + p.x_progress * spreadMultiplier);
          ptLng = lng + adjustedOffset;
          ptLat = lat - adjustedOffset * 0.45;
          insideFlood = isPointInPolygon([ptLng, ptLat], activePoly);
        }
      }

      // 3. Realistic Flow Speed Modulation
      // Faster flow in deep channel center, slower near inundated boundary margins
      const centerFactor = 1.4 - Math.abs(p.offset_lateral) * 0.7;
      let currentSpeed = p.speed * velScale * Math.max(0.3, centerFactor);

      if ($simulationResults) {
        if (!insideFlood || p.x_progress > waveFrontPosition) {
          // Particles at or beyond active flood boundary slow down to 0 and stop
          currentSpeed = 0.0;
        }
      }

      // Advect particle downstream
      p.x_progress += currentSpeed;
      if (p.x_progress > 1.0) {
        p.x_progress = 0.0;
      }

      // Render particle if inside active domain
      if (insideFlood || !$simulationResults) {
        try {
          const screenPt = map.project([ptLng, ptLat]);

          if (screenPt && screenPt.x >= -40 && screenPt.x <= width + 40 && screenPt.y >= -40 && screenPt.y <= height + 40) {
            
            // Velocity vector tails for fast flowing water
            if (currentSpeed > 0.0018) {
              const prevLngLat = interpolatePoint(riverPath, Math.max(0, p.x_progress - 0.014));
              const prevPt = map.project([prevLngLat[0] + (ptLng - lng), prevLngLat[1] + (ptLat - lat)]);
              
              ctx.beginPath();
              ctx.moveTo(prevPt.x, prevPt.y);
              ctx.lineTo(screenPt.x, screenPt.y);
              ctx.strokeStyle = isWaveFront ? '#ffffff' : (isFloodedZone ? '#38bdf8' : p.color);
              ctx.lineWidth = p.size * (isFloodedZone ? 0.9 : 0.6);
              ctx.globalAlpha = (isFloodedZone ? p.alpha * 0.75 : p.alpha * 0.35);
              ctx.stroke();
            }

            // Main particle dot
            ctx.beginPath();
            const effectiveSize = isWaveFront ? p.size * 1.6 : (isFloodedZone ? p.size * 1.25 : p.size);
            ctx.arc(screenPt.x, screenPt.y, effectiveSize, 0, Math.PI * 2);
            
            if (isWaveFront) {
              ctx.fillStyle = '#ffffff';
              ctx.shadowColor = '#7dd3fc';
              ctx.shadowBlur = 14;
              ctx.globalAlpha = 0.95;
            } else if (isFloodedZone) {
              ctx.fillStyle = p.color;
              ctx.shadowColor = '#38bdf8';
              ctx.shadowBlur = 8;
              ctx.globalAlpha = Math.min(1.0, p.alpha * 1.25);
            } else {
              ctx.fillStyle = p.color;
              ctx.shadowColor = '#0284c7';
              ctx.shadowBlur = 4;
              ctx.globalAlpha = p.alpha * 0.85;
            }
            
            ctx.fill();
          }
        } catch (e) {
          // Ignore map projection during zoom/pan
        }
      }
    }

    ctx.globalAlpha = 1.0;
    ctx.shadowBlur = 0;
    animId = requestAnimationFrame(draw);
  }

  $: if (map) {
    updateCanvasDimensions();
  }

  onMount(() => {
    initParticles();
    window.addEventListener('resize', updateCanvasDimensions);
    draw();
  });

  onDestroy(() => {
    window.removeEventListener('resize', updateCanvasDimensions);
    if (animId) cancelAnimationFrame(animId);
  });
</script>

<canvas
  bind:this={canvas}
  class="absolute inset-0 pointer-events-none z-20 w-full h-full"
></canvas>
