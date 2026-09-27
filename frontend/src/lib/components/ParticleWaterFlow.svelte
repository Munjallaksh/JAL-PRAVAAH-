<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { simulationResults, currentTimeIndex, selectedLocation, domainRiverCoords } from '../store';
  import type maplibregl from 'maplibre-gl';

  export let map: maplibregl.Map | null = null;

  let canvas: HTMLCanvasElement;
  let animId: number;

  interface WaterParticle {
    prog: number;          // 0.0 (reservoir / dam breach) to 1.0 (downstream plain)
    lateral: number;       // -1.0 to 1.0 cross-channel position (dynamic!)
    latVel: number;        // Dynamic cross-channel velocity (turbulent lateral mixing)
    baseSpeed: number;     // Downstream advection velocity
    size: number;          // Droplet / fluid element radius
    tier: 'core' | 'deep' | 'mid' | 'shallow' | 'fringe';
    isFoam: boolean;       // White/cyan surface froth fleck
    isFroth: boolean;      // Intense whitewater rapid spray
    phase: number;         // Wave / oscillation phase
    life: number;          // Current particle age
    maxLife: number;       // Particle lifespan before smooth re-seeding
    alpha: number;         // Base transparency
  }

  let particles: WaterParticle[] = [];
  const PARTICLE_COUNT = 10500; // Dense fluid field: closely packed to form continuous water

  // Pre-rendered offscreen fluid sprites for 60 FPS hardware-accelerated fluid rendering
  let spriteCore: HTMLCanvasElement;
  let spriteDeep: HTMLCanvasElement;
  let spriteMid: HTMLCanvasElement;
  let spriteShallow: HTMLCanvasElement;
  let spriteFringe: HTMLCanvasElement;
  let spriteFoam: HTMLCanvasElement;
  let spriteFroth: HTMLCanvasElement;

  function createRadialSprite(
    size: number,
    colorStops: { stop: number; color: string; alpha: number }[]
  ): HTMLCanvasElement {
    const c = document.createElement('canvas');
    c.width = size;
    c.height = size;
    const ctx = c.getContext('2d');
    if (!ctx) return c;

    const r = size / 2;
    const grad = ctx.createRadialGradient(r, r, 0, r, r, r);
    for (const cs of colorStops) {
      grad.addColorStop(cs.stop, cs.color);
    }
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, size, size);
    return c;
  }

  function initSprites() {
    // 1. Core Deep Water (> 10m): Deep indigo/navy fluid disc
    spriteCore = createRadialSprite(48, [
      { stop: 0.0, color: 'rgba(9, 40, 98, 0.96)', alpha: 0.96 },
      { stop: 0.45, color: 'rgba(18, 73, 156, 0.88)', alpha: 0.88 },
      { stop: 0.75, color: 'rgba(29, 109, 216, 0.42)', alpha: 0.42 },
      { stop: 1.0, color: 'rgba(29, 109, 216, 0.0)', alpha: 0.0 }
    ]);

    // 2. Deep Water (5 - 10m): Royal blue fluid disc
    spriteDeep = createRadialSprite(44, [
      { stop: 0.0, color: 'rgba(18, 73, 156, 0.92)', alpha: 0.92 },
      { stop: 0.50, color: 'rgba(29, 109, 216, 0.80)', alpha: 0.80 },
      { stop: 0.80, color: 'rgba(59, 167, 245, 0.35)', alpha: 0.35 },
      { stop: 1.0, color: 'rgba(59, 167, 245, 0.0)', alpha: 0.0 }
    ]);

    // 3. Mid Depth (2 - 5m): Cobalt / vibrant azure fluid disc
    spriteMid = createRadialSprite(40, [
      { stop: 0.0, color: 'rgba(29, 109, 216, 0.88)', alpha: 0.88 },
      { stop: 0.50, color: 'rgba(59, 167, 245, 0.72)', alpha: 0.72 },
      { stop: 0.80, color: 'rgba(124, 203, 249, 0.30)', alpha: 0.30 },
      { stop: 1.0, color: 'rgba(124, 203, 249, 0.0)', alpha: 0.0 }
    ]);

    // 4. Shallow Water (0.5 - 2m): Bright azure sky fluid disc
    spriteShallow = createRadialSprite(36, [
      { stop: 0.0, color: 'rgba(59, 167, 245, 0.82)', alpha: 0.82 },
      { stop: 0.50, color: 'rgba(124, 203, 249, 0.65)', alpha: 0.65 },
      { stop: 0.80, color: 'rgba(191, 219, 254, 0.25)', alpha: 0.25 },
      { stop: 1.0, color: 'rgba(191, 219, 254, 0.0)', alpha: 0.0 }
    ]);

    // 5. Fringe Water (0.1 - 0.5m): Soft pale cyan boundary fluid disc
    spriteFringe = createRadialSprite(32, [
      { stop: 0.0, color: 'rgba(124, 203, 249, 0.70)', alpha: 0.70 },
      { stop: 0.50, color: 'rgba(191, 219, 254, 0.45)', alpha: 0.45 },
      { stop: 0.80, color: 'rgba(224, 242, 254, 0.15)', alpha: 0.15 },
      { stop: 1.0, color: 'rgba(224, 242, 254, 0.0)', alpha: 0.0 }
    ]);

    // 6. Surface Foam: Rolling white foam froth
    spriteFoam = createRadialSprite(28, [
      { stop: 0.0, color: 'rgba(255, 255, 255, 0.98)', alpha: 0.98 },
      { stop: 0.40, color: 'rgba(240, 249, 255, 0.85)', alpha: 0.85 },
      { stop: 0.70, color: 'rgba(186, 230, 253, 0.40)', alpha: 0.40 },
      { stop: 1.0, color: 'rgba(186, 230, 253, 0.0)', alpha: 0.0 }
    ]);

    // 7. Whitewater Rapid Spray: Intense churning white froth
    spriteFroth = createRadialSprite(20, [
      { stop: 0.0, color: 'rgba(255, 255, 255, 1.0)', alpha: 1.0 },
      { stop: 0.45, color: 'rgba(224, 242, 254, 0.85)', alpha: 0.85 },
      { stop: 1.0, color: 'rgba(224, 242, 254, 0.0)', alpha: 0.0 }
    ]);
  }

  function spawnParticle(initProg?: number): WaterParticle {
    const prog = initProg !== undefined ? initProg : Math.random();
    
    // Gaussian lateral distribution: heavily concentrated along the central deep thalweg
    const u1 = Math.random();
    const u2 = Math.random();
    const randStdNormal = Math.sqrt(-2.0 * Math.log(Math.max(1e-5, u1))) * Math.cos(2.0 * Math.PI * u2);
    const lateral = Math.max(-0.98, Math.min(0.98, randStdNormal * 0.42));
    const absLat = Math.abs(lateral);

    let tier: 'core' | 'deep' | 'mid' | 'shallow' | 'fringe';
    if (absLat < 0.24) tier = 'core';
    else if (absLat < 0.48) tier = 'deep';
    else if (absLat < 0.70) tier = 'mid';
    else if (absLat < 0.88) tier = 'shallow';
    else tier = 'fringe';

    const isFroth = Math.random() < 0.08;
    const isFoam = !isFroth && Math.random() < 0.16;

    // Fluid speed governed by water depth and canyon geometry:
    // Core rushes with immense kinetic energy; shallows move gently with bank friction
    let baseSpeed = 0.0016;
    if (tier === 'core') baseSpeed = 0.0036 + Math.random() * 0.0022;
    else if (tier === 'deep') baseSpeed = 0.0028 + Math.random() * 0.0016;
    else if (tier === 'mid') baseSpeed = 0.0018 + Math.random() * 0.0012;
    else if (tier === 'shallow') baseSpeed = 0.0010 + Math.random() * 0.0008;
    else baseSpeed = 0.0005 + Math.random() * 0.0005;

    // Generous droplet size: soft radial discs overlap heavily, fusing into continuous fluid
    let size = 6.0;
    if (isFroth) size = 3.5 + Math.random() * 2.5;
    else if (isFoam) size = 4.5 + Math.random() * 3.5;
    else if (tier === 'core') size = 8.5 + Math.random() * 4.0;
    else if (tier === 'deep') size = 7.5 + Math.random() * 3.5;
    else if (tier === 'mid') size = 6.5 + Math.random() * 3.0;
    else if (tier === 'shallow') size = 5.5 + Math.random() * 2.5;
    else size = 4.5 + Math.random() * 2.0;

    return {
      prog,
      lateral,
      latVel: (Math.random() - 0.5) * 0.0012,
      baseSpeed,
      size,
      tier,
      isFoam,
      isFroth,
      phase: Math.random() * Math.PI * 2,
      life: Math.floor(Math.random() * 150),
      maxLife: 260 + Math.floor(Math.random() * 240),
      alpha: isFroth ? 0.95 : isFoam ? 0.85 : 0.75
    };
  }

  function initParticles() {
    particles = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push(spawnParticle());
    }
  }

  function getActiveRiverCoords(): [number, number][] {
    // 1. If simulation is complete: use the hydrodynamic model's predicted path (dam breach to exact extinction point)
    if ($simulationResults?.active_river_coords && $simulationResults.active_river_coords.length >= 2) {
      return $simulationResults.active_river_coords;
    }

    // 2. If domain GIS is loaded for selected dam: use the dynamic domain river coords
    if ($domainRiverCoords && $domainRiverCoords.length >= 2) {
      return $domainRiverCoords;
    }

    if ($simulationResults?.max_inundation?.features[0]?.geometry?.coordinates[0]) {
      const poly = $simulationResults.max_inundation.features[0].geometry.coordinates[0];
      if (poly && poly.length > 8) {
        const half = Math.floor(poly.length / 2);
        const midline: [number, number][] = [];
        for (let i = 0; i < half; i++) {
          const p1 = poly[i];
          const p2 = poly[poly.length - 2 - i] || p1;
          midline.push([(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2]);
        }
        if (midline.length >= 6) return midline;
      }
    }

    const centerLng = $selectedLocation?.lng || 78.4803;
    const centerLat = $selectedLocation?.lat || 30.3781;

    // Bhagirathi / Ganga River natural coordinates from Tehri Dam down to Haridwar
    if (centerLng > 78.0 && centerLng < 79.0 && centerLat > 29.8 && centerLat < 30.6) {
      return [
        [78.4803, 30.3781], // Tehri Dam breach failure point
        [78.5020, 30.3540], // Tehri town reach
        [78.5280, 30.2780], // Upper gorge
        [78.5610, 30.2210], // Valley bend
        [78.5980, 30.1470], // Devprayag confluence pool
        [78.5520, 30.1210], // Malakunti bend
        [78.4820, 30.1150], // Byasi gorge
        [78.4120, 30.1080], // Shivpuri
        [78.3450, 30.1340], // Brahmpuri
        [78.2980, 30.1020], // Tapovan gorge
        [78.2676, 30.0869], // Rishikesh expansion
        [78.2480, 30.0410], // Raiwala
        [78.2120, 29.9850], // Bhopatwala
        [78.1642, 29.9457], // Haridwar
        [78.1320, 29.9010]  // Downstream alluvial plain
      ];
    }

    const riverPath: [number, number][] = [];
    const numPoints = 18;
    const dLat = centerLat > 20.0 ? -0.020 : -0.016;
    const dLng = centerLng > 78.0 ? -0.016 : 0.018;

    for (let i = 0; i < numPoints; i++) {
      const meander = Math.sin(i * 0.65) * 0.015;
      const ptLat = centerLat + i * dLat + meander;
      const ptLng = centerLng + i * dLng + meander * 0.7;
      riverPath.push([ptLng, ptLat]);
    }

    return riverPath;
  }

  function interpolatePoint(path: [number, number][], progress: number): { pt: [number, number]; normal: [number, number]; curvature: number } {
    if (path.length === 0) return { pt: [0, 0], normal: [0, 1], curvature: 0 };
    if (path.length === 1) return { pt: path[0], normal: [0, 1], curvature: 0 };

    const totalSegs = path.length - 1;
    const scaledProg = Math.max(0, Math.min(1.0, progress)) * totalSegs;
    const segIdx = Math.min(Math.floor(scaledProg), totalSegs - 1);
    const rem = scaledProg - segIdx;

    const p0 = path[Math.max(0, segIdx - 1)];
    const p1 = path[segIdx];
    const p2 = path[segIdx + 1] || p1;
    const p3 = path[Math.min(totalSegs, segIdx + 2)];

    // Catmull-Rom cubic interpolation for ultra-smooth fluid midline
    const lng = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * rem + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * (rem ** 2) + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * (rem ** 3));
    const lat = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * rem + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * (rem ** 2) + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * (rem ** 3));

    const dx = p2[0] - p1[0];
    const dy = p2[1] - p1[1];
    const len = Math.hypot(dx, dy) || 1.0;
    const nx = -dy / len;
    const ny = dx / len;

    // Approximate channel curvature (for centrifugal water drift around bends)
    const dxPrev = p1[0] - p0[0];
    const dyPrev = p1[1] - p0[1];
    const headingCur = Math.atan2(dy, dx);
    const headingPrev = Math.atan2(dyPrev, dxPrev);
    let curvature = headingCur - headingPrev;
    if (curvature > Math.PI) curvature -= 2 * Math.PI;
    if (curvature < -Math.PI) curvature += 2 * Math.PI;

    return { pt: [lng, lat], normal: [nx, ny], curvature };
  }

  function getValleyHalfWidth(prog: number): number {
    const isTehri = ($selectedLocation?.name || '').toLowerCase().includes('tehri') || ($selectedLocation?.river || '').toLowerCase().includes('bhagirathi');
    if (isTehri) {
      const reservoirPool = 0.026 * Math.pow(Math.max(0.0, 1.0 - prog / 0.18), 1.25);
      const devprayagPool = 0.018 * Math.exp(-Math.pow((prog - 0.38) / 0.055, 2));
      const haridwarPlain = 0.030 * Math.pow(Math.max(0.0, (prog - 0.60) / 0.40), 1.35);
      const valleyHarmonics = 0.0025 * Math.sin(prog * 18.0) + 0.0018 * Math.cos(prog * 34.0);
      return 0.0075 + reservoirPool + devprayagPool + haridwarPlain + valleyHarmonics;
    }

    // Generic hydrodynamic valley width expansion for ANY Indian dam and river
    const damBreachPool = 0.020 * Math.pow(Math.max(0.0, 1.0 - prog / 0.20), 1.2);
    const downstreamPlain = 0.024 * Math.pow(Math.max(0.0, (prog - 0.55) / 0.45), 1.3);
    const valleyNoise = 0.0020 * Math.sin(prog * 16.0) + 0.0014 * Math.cos(prog * 32.0);
    return 0.0070 + damBreachPool + downstreamPlain + valleyNoise;
  }

  // Realistic whirlpool eddy zones in the mountain river (confluences and gorge bends)
  const EDDY_ZONES = [
    { centerProg: 0.10, lat: 0.35, radius: 0.07, strength: 0.0020 },  // Reservoir gyre
    { centerProg: 0.38, lat: -0.42, radius: 0.06, strength: -0.0035 }, // Devprayag confluence vortex
    { centerProg: 0.54, lat: 0.38, radius: 0.05, strength: 0.0028 },  // Byasi gorge recirculating eddy
    { centerProg: 0.72, lat: -0.32, radius: 0.055, strength: -0.0025 } // Rishikesh terrace vortex
  ];

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

  let simTime = 0;

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

    // Clean clear: strictly NO lingering streaks or lines
    ctx.clearRect(0, 0, width, height);

    simTime += 0.016;

    const riverPath = getActiveRiverCoords();
    const snapshots = $simulationResults?.temporal_snapshots || [];
    
    // Wave front marker position for timeline video playback
    const waveFrontPosition = snapshots.length > 0
      ? Math.min(1.0, ($currentTimeIndex + 1) / snapshots.length)
      : 1.0;

    const baseVelMps = $simulationResults?.max_inundation?.features[0]?.properties?.max_velocity_mps || 6.5;
    const velScale = $simulationResults ? Math.min(2.2, Math.max(0.7, baseVelMps / 4.8)) : 1.0;

    // Zoom-adaptive fluid scaling so droplets blend into a continuous fluid sheet at ANY zoom
    const mapZoom = map.getZoom ? map.getZoom() : 10;
    const zoomScale = Math.max(0.65, Math.min(3.2, Math.pow(1.32, mapZoom - 10)));

    for (let p of particles) {
      p.life++;

      // Smooth life cycle re-seeding: eliminates any repetitive trajectories
      if (p.life > p.maxLife || p.prog > 1.0) {
        const respawnProg = $simulationResults
          ? Math.random() * Math.min(waveFrontPosition, 0.25)
          : Math.random() * 0.20;
        const fresh = spawnParticle(respawnProg);
        Object.assign(p, fresh);
      }

      // 1. Natural river valley center, normal vector, and curvature
      const { pt, normal, curvature } = interpolatePoint(riverPath, p.prog);
      const halfWidth = getValleyHalfWidth(p.prog);

      // 2. Real 2D Hydrodynamic Motion (NO FIXED RAILS / NO LINES!)
      // A. Turbulent lateral diffusion (Brownian fluid wander)
      p.phase += 0.035;
      const turbulentDrift = (Math.sin(p.phase * 1.7) * 0.0006 + (Math.random() - 0.5) * 0.0008);
      p.latVel += turbulentDrift;

      // B. Centrifugal inertia around river bends (water momentum pushes to outside bank)
      p.latVel += curvature * 0.0022;

      // C. Valley expansion / contraction lateral drift
      if (p.prog > 0.60) {
        // Haridwar plain: water fans out laterally
        p.latVel += p.lateral * 0.0006;
      }

      // D. Rotational whirlpool eddies
      for (const eddy of EDDY_ZONES) {
        const dProg = p.prog - eddy.centerProg;
        const dLat = p.lateral - eddy.lat;
        const distSq = (dProg * 2.0) ** 2 + dLat ** 2;
        if (distSq < eddy.radius ** 2) {
          // Tangential rotational swirl
          const factor = (1.0 - Math.sqrt(distSq) / eddy.radius);
          p.latVel += factor * eddy.strength;
          p.prog += factor * eddy.strength * 0.8;
        }
      }

      // E. Viscous fluid damping & bank containment
      p.latVel *= 0.90;
      p.lateral += p.latVel;

      // Soft rebound from valley margins (recirculating bank boundary layer)
      if (p.lateral > 0.96) {
        p.lateral = 0.95;
        p.latVel = -Math.abs(p.latVel) * 0.6;
      } else if (p.lateral < -0.96) {
        p.lateral = -0.95;
        p.latVel = Math.abs(p.latVel) * 0.6;
      }

      // Dynamic depth tier update as particle migrates across the channel
      const curAbsLat = Math.abs(p.lateral);
      if (curAbsLat < 0.24) p.tier = 'core';
      else if (curAbsLat < 0.48) p.tier = 'deep';
      else if (curAbsLat < 0.70) p.tier = 'mid';
      else if (curAbsLat < 0.88) p.tier = 'shallow';
      else p.tier = 'fringe';

      // 3. True 2D geographic coordinates across the flood body
      const lateralDist = p.lateral * halfWidth;
      const ptLng = pt[0] + normal[0] * lateralDist;
      const ptLat = pt[1] + normal[1] * lateralDist;

      // 4. Wave front check for video playback
      const isBehindWaveFront = p.prog <= waveFrontPosition;
      const isWaveFrontCrest = snapshots.length > 0 && Math.abs(p.prog - waveFrontPosition) < 0.035;

      // 5. Surge pulse waves & velocity profile
      // Logarithmic velocity profile: fast central thalweg, slow boundary edges
      const velocityProfile = 1.35 - Math.pow(curAbsLat, 1.6) * 0.75;
      // Surge wave pulse traveling downstream
      const surgePulse = 1.0 + 0.28 * Math.sin(16.0 * p.prog - simTime * 5.5);

      // Hydraulic extinction factor: as water reaches predicted termination boundary (prog -> 1.0),
      // flow slows down to near-zero and dissipates
      let extinctionFactor = 1.0;
      if (p.prog > 0.82) {
        extinctionFactor = Math.max(0.04, 1.0 - Math.pow((p.prog - 0.82) / 0.18, 1.5));
      }

      // High-velocity hydraulic jet emerging from the broken dam breach (prog < 0.08)
      let breachJet = 1.0;
      if (p.prog < 0.08) {
        breachJet = 1.65 - (p.prog / 0.08) * 0.65;
      }

      let effectiveSpeed = p.baseSpeed * velScale * velocityProfile * surgePulse * extinctionFactor * breachJet;

      if ($simulationResults && !isBehindWaveFront) {
        effectiveSpeed = 0.0;
      }

      // Advance fluid particle downstream
      p.prog += effectiveSpeed;

      // Exact termination: particles stop at predicted extinction point and re-spawn at the dam breach
      if (p.prog >= 1.0) {
        const fresh = spawnParticle(0.0);
        Object.assign(p, fresh);
      }

      // 6. Fluid Sprite Rendering (Continuous liquid sheet, NO LINES!)
      if (isBehindWaveFront || !$simulationResults) {
        try {
          const screenPt = map.project([ptLng, ptLat]);

          if (screenPt && screenPt.x >= -40 && screenPt.x <= width + 40 && screenPt.y >= -40 && screenPt.y <= height + 40) {
            let sprite = spriteMid;
            let drawRadius = p.size * zoomScale;
            let extAlpha = 1.0;
            if (p.prog > 0.92) {
              extAlpha = Math.max(0.0, (1.0 - p.prog) / 0.08);
            }

            if (isWaveFrontCrest) {
              // Tumbling whitewater surge at the advancing flood front
              sprite = spriteFroth;
              drawRadius *= 1.6;
              ctx.globalAlpha = 0.95 * extAlpha;
            } else if (p.isFroth || p.prog < 0.06) {
              // Intense spray at breach jet or rapid churning froth flecks
              sprite = spriteFroth;
              drawRadius *= 1.25;
              ctx.globalAlpha = 0.90 * extAlpha;
            } else if (p.isFoam) {
              // Rolling surface foam
              sprite = spriteFoam;
              drawRadius *= 1.15;
              ctx.globalAlpha = 0.82 * extAlpha;
            } else {
              // Cohesive fluid droplets that seamlessly blend together
              if (p.tier === 'core') sprite = spriteCore;
              else if (p.tier === 'deep') sprite = spriteDeep;
              else if (p.tier === 'mid') sprite = spriteMid;
              else if (p.tier === 'shallow') sprite = spriteShallow;
              else sprite = spriteFringe;

              ctx.globalAlpha = p.alpha * extAlpha;
            }

            const drawSize = drawRadius * 2;
            ctx.drawImage(
              sprite,
              screenPt.x - drawRadius,
              screenPt.y - drawRadius,
              drawSize,
              drawSize
            );
          }
        } catch (e) {
          // Ignore projection out of bounds
        }
      }
    }

    // Reset alpha
    ctx.globalAlpha = 1.0;

    animId = requestAnimationFrame(draw);
  }

  onMount(() => {
    initSprites();
    initParticles();
    animId = requestAnimationFrame(draw);
  });

  onDestroy(() => {
    if (animId) cancelAnimationFrame(animId);
  });

  $: if ($selectedLocation) {
    initParticles();
  }
</script>

<canvas
  bind:this={canvas}
  class="absolute inset-0 pointer-events-none z-10 w-full h-full"
></canvas>
