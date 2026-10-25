/**
 * FairPool: Interactive Frontend Controller & Road Network Visualizer
 * Implements HTML5 Canvas route rendering, reactive KPI updates,
 * match manifest interaction, and deterministic benchmark exploration.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Application State
  const state = {
    network: null,
    requests: [],
    offers: [],
    matchedTrips: [],
    selectedTripId: null,
    latestResult: null,
    benchmarkData: null,
    viewTransform: { x: 0, y: 0, scale: 1 },
    hoveredNode: null,
  };

  // DOM Elements
  const canvas = document.getElementById('roadNetworkCanvas');
  const ctx = canvas.getContext('2d');
  const canvasWrapper = document.getElementById('canvasWrapper');

  // KPI Elements
  const kpiSavedVkm = document.getElementById('kpiSavedVkm');
  const kpiSavingsTag = document.getElementById('kpiSavingsTag');
  const kpiCo2Saved = document.getElementById('kpiCo2Saved');
  const kpiSavingsBar = document.getElementById('kpiSavingsBar');
  const kpiGiniValue = document.getElementById('kpiGiniValue');
  const kpiGiniBar = document.getElementById('kpiGiniBar');
  const kpiMatchRate = document.getElementById('kpiMatchRate');
  const kpiMatchRateTag = document.getElementById('kpiMatchRateTag');
  const kpiTripsCount = document.getElementById('kpiTripsCount');
  const kpiMatchRateBar = document.getElementById('kpiMatchRateBar');
  const kpiRuntime = document.getElementById('kpiRuntime');
  const kpiMeanDetour = document.getElementById('kpiMeanDetour');
  const kpiSpeedBar = document.getElementById('kpiSpeedBar');
  const kpiAlgorithmBadge = document.getElementById('kpiAlgorithmBadge');

  // Interactive Elements
  const manifestList = document.getElementById('manifestList');
  const tabTripCount = document.getElementById('tabTripCount');
  const selectedTripLabel = document.getElementById('selectedTripLabel');
  const nodeInspector = document.getElementById('nodeInspector');
  const toastContainer = document.getElementById('toastContainer');

  // Controls
  const batchSizeSelect = document.getElementById('batchSizeSelect');
  const btnGenerateBatch = document.getElementById('btnGenerateBatch');
  const btnRunMatch = document.getElementById('btnRunMatch');
  const btnRunBenchmark = document.getElementById('btnRunBenchmark');
  const btnTriggerBenchmark = document.getElementById('btnTriggerBenchmark');
  const btnResetAll = document.getElementById('btnResetAll');
  const btnResetView = document.getElementById('btnResetView');
  const checkFairnessToggle = document.getElementById('checkFairnessToggle');
  const btnSimulate5Days = document.getElementById('btnSimulate5Days');

  // Sliders
  const reqDetourSlider = document.getElementById('reqDetourSlider');
  const valDetourTol = document.getElementById('valDetourTol');
  reqDetourSlider?.addEventListener('input', (e) => {
    valDetourTol.textContent = `${e.target.value}%`;
  });

  const offDetourSlider = document.getElementById('offDetourSlider');
  const valMaxDetour = document.getElementById('valMaxDetour');
  offDetourSlider?.addEventListener('input', (e) => {
    valMaxDetour.textContent = `${e.target.value} min`;
  });

  // Setup Canvas Sizing
  function resizeCanvas() {
    canvas.width = canvasWrapper.clientWidth * window.devicePixelRatio;
    canvas.height = canvasWrapper.clientHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    renderMap();
  }
  window.addEventListener('resize', resizeCanvas);

  // Tab Switching
  document.querySelectorAll('.tab-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach((p) => p.classList.remove('active'));

      btn.classList.add('active');
      const targetPane = document.getElementById(btn.getAttribute('data-tab'));
      if (targetPane) targetPane.classList.add('active');
    });
  });

  // Toast Notification Helper
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // Fetch Road Network Data
  async function loadNetwork() {
    try {
      const res = await fetch('/api/network');
      state.network = await res.json();
      populateDropdowns();
      resizeCanvas();
    } catch (err) {
      console.error('Failed to load network:', err);
      showToast('Error loading road network', 'danger');
    }
  }

  // Populate node dropdowns in submission portal
  function populateDropdowns() {
    if (!state.network || !state.network.nodes) return;
    const origins = ['reqOriginSelect', 'offOriginSelect'];
    const dests = ['reqDestSelect', 'offDestSelect'];

    origins.forEach((id) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.innerHTML = '';
      state.network.nodes.forEach((n) => {
        const opt = document.createElement('option');
        opt.value = n.id;
        opt.textContent = `${n.name} (${n.id})`;
        if (!n.is_campus_hub) opt.selected = true;
        el.appendChild(opt);
      });
    });

    dests.forEach((id) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.innerHTML = '';
      state.network.nodes.forEach((n) => {
        const opt = document.createElement('option');
        opt.value = n.id;
        opt.textContent = `${n.name} (${n.id})`;
        if (n.is_campus_hub) opt.selected = true;
        el.appendChild(opt);
      });
    });
  }

  // Coordinate Projection Helpers
  function getCanvasCoords(lat, lng) {
    if (!state.network || !state.network.nodes.length) return { x: 0, y: 0 };
    // Compute bounds
    const lats = state.network.nodes.map((n) => n.lat);
    const lngs = state.network.nodes.map((n) => n.lng);

    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);

    const padding = 60;
    const w = canvasWrapper.clientWidth - padding * 2;
    const h = canvasWrapper.clientHeight - padding * 2;

    const normX = (lng - minLng) / (maxLng - minLng || 1);
    const normY = 1.0 - (lat - minLat) / (maxLat - minLat || 1);

    return {
      x: padding + normX * w,
      y: padding + normY * h,
    };
  }

  // Main Canvas Map Renderer
  function renderMap() {
    if (!state.network || !ctx) return;
    const w = canvasWrapper.clientWidth;
    const h = canvasWrapper.clientHeight;
    ctx.clearRect(0, 0, w, h);

    // 1. Draw Network Edges (Roads)
    state.network.edges.forEach((edge) => {
      const uNode = state.network.nodes.find((n) => n.id === edge.from);
      const vNode = state.network.nodes.find((n) => n.id === edge.to);
      if (!uNode || !vNode) return;

      const p1 = getCanvasCoords(uNode.lat, uNode.lng);
      const p2 = getCanvasCoords(vNode.lat, vNode.lng);

      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // Road Speed badge in midpoint
      const midX = (p1.x + p2.x) / 2;
      const midY = (p1.y + p2.y) / 2;
      ctx.fillStyle = 'rgba(100, 116, 139, 0.4)';
      ctx.font = '9px Fira Code';
      ctx.fillText(`${edge.speed_kmh}km/h`, midX - 12, midY - 4);
    });

    // 2. Draw Active/Selected Trip Path if any
    if (state.selectedTripId) {
      const selectedTrip = state.matchedTrips.find((t) => t.id === state.selectedTripId);
      if (selectedTrip && selectedTrip.stops.length > 1) {
        ctx.beginPath();
        for (let i = 0; i < selectedTrip.stops.length; i++) {
          const locId = selectedTrip.stops[i].location_id;
          const node = state.network.nodes.find((n) => n.id === locId);
          if (node) {
            const pt = getCanvasCoords(node.lat, node.lng);
            if (i === 0) ctx.moveTo(pt.x, pt.y);
            else ctx.lineTo(pt.x, pt.y);
          }
        }
        // Glowing electric blue & emerald path
        ctx.strokeStyle = '#10B981';
        ctx.lineWidth = 4.5;
        ctx.shadowColor = '#10B981';
        ctx.shadowBlur = 14;
        ctx.stroke();
        ctx.shadowBlur = 0; // reset
      }
    }

    // 3. Draw Nodes (Pins)
    state.network.nodes.forEach((node) => {
      const pt = getCanvasCoords(node.lat, node.lng);
      const isHovered = state.hoveredNode && state.hoveredNode.id === node.id;

      ctx.beginPath();
      const radius = node.is_campus_hub ? 9 : 7;
      ctx.arc(pt.x, pt.y, radius, 0, Math.PI * 2);

      if (node.is_campus_hub) {
        ctx.fillStyle = isHovered ? '#60A5FA' : '#3B82F6';
        ctx.shadowColor = '#3B82F6';
        ctx.shadowBlur = 10;
      } else {
        ctx.fillStyle = isHovered ? '#FCD34D' : '#F59E0B';
        ctx.shadowColor = '#F59E0B';
        ctx.shadowBlur = 8;
      }
      ctx.fill();
      ctx.shadowBlur = 0;

      // Inner dot
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 3, 0, Math.PI * 2);
      ctx.fillStyle = '#FFFFFF';
      ctx.fill();

      // Node Label
      ctx.font = isHovered ? '600 12px Outfit' : '500 11px Outfit';
      ctx.fillStyle = isHovered ? '#FFFFFF' : '#CBD5E1';
      ctx.fillText(node.name, pt.x + 12, pt.y + 4);
    });
  }

  // Canvas Mouse Move (Node Hover Detection)
  canvas.addEventListener('mousemove', (e) => {
    if (!state.network) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    let found = null;
    for (const node of state.network.nodes) {
      const pt = getCanvasCoords(node.lat, node.lng);
      const dist = Math.hypot(pt.x - mouseX, pt.y - mouseY);
      if (dist < 18) {
        found = node;
        break;
      }
    }

    if (found !== state.hoveredNode) {
      state.hoveredNode = found;
      if (found) {
        nodeInspector.innerHTML = `
          <div class="inspector-badge">
            <strong>${found.name}</strong> [${found.id}] &bull; ${
          found.is_campus_hub ? 'Academic Hub' : 'Commuter Gateway'
        }
          </div>
        `;
      } else {
        nodeInspector.innerHTML = `<div class="inspector-badge">Hover a node or click a trip to inspect</div>`;
      }
      renderMap();
    }
  });

  // KPI UI Animation
  function updateKPIs(result) {
    if (!result) return;
    const saved = result.total_vkm_saved || 0;
    const baseline = result.total_vkm_baseline_no_pool || 1;
    const pct = ((saved / baseline) * 100).toFixed(1);
    const co2 = (saved * 0.192).toFixed(1); // 192g CO2/km average passenger vehicle

    kpiSavedVkm.textContent = saved.toFixed(1);
    kpiSavingsTag.textContent = `+${pct}%`;
    kpiCo2Saved.textContent = `🌱 ${co2} kg CO₂ emissions prevented`;
    kpiSavingsBar.style.width = `${Math.min(100, pct * 2)}%`;

    kpiGiniValue.textContent = (result.gini_driver_detour || 0).toFixed(4);
    const gini = result.gini_driver_detour || 0;
    const giniScore = gini < 0.6 ? 'Equitable' : gini < 0.75 ? 'Moderate' : 'Unbalanced';
    document.getElementById('kpiFairnessTag').textContent = giniScore;
    kpiGiniBar.style.width = `${Math.min(100, (1.0 - gini) * 100)}%`;

    kpiMatchRate.textContent = `${(result.match_rate_percent || 0).toFixed(1)}%`;
    const matchedCount = (state.requests.length || 0) - (result.unmatched_request_ids ? result.unmatched_request_ids.length : 0);
    kpiMatchRateTag.textContent = `${matchedCount} / ${state.requests.length || matchedCount}`;
    kpiTripsCount.textContent = `${(result.matched_trips || []).length} shared vehicle trips dispatched`;
    kpiMatchRateBar.style.width = `${Math.min(100, result.match_rate_percent || 0)}%`;

    kpiRuntime.textContent = (result.runtime_ms || 0).toFixed(1);
    kpiMeanDetour.textContent = `Mean driver detour: ${(result.mean_driver_detour_min || 0).toFixed(1)} min`;
    kpiAlgorithmBadge.textContent = result.algorithm_name || 'FairPool';
  }

  // Render Manifest Cards
  function renderManifest(trips) {
    manifestList.innerHTML = '';
    tabTripCount.textContent = trips.length;

    if (!trips.length) {
      manifestList.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">🚗💨</div>
          <h4>No Matched Trips Dispatched</h4>
          <p>Click "Synthesize Rush" then "Run FairPool Match" to dispatch carpools.</p>
        </div>
      `;
      return;
    }

    trips.forEach((trip, idx) => {
      const card = document.createElement('div');
      card.className = `trip-card ${trip.id === state.selectedTripId ? 'selected' : ''}`;
      card.dataset.tripId = trip.id;

      let stopsHtml = '';
      trip.stops.forEach((s) => {
        let badgeClass = 'driver';
        let badgeLabel = 'DEP';
        if (s.stop_type === 'PICKUP') {
          badgeClass = 'pickup';
          badgeLabel = `+1 RIDER`;
        } else if (s.stop_type === 'DROPOFF') {
          badgeClass = 'dropoff';
          badgeLabel = `-1 DROP`;
        } else if (s.stop_type === 'DRIVER_DESTINATION') {
          badgeClass = 'driver';
          badgeLabel = 'DEST';
        }

        stopsHtml += `
          <div class="stop-item">
            <span class="stop-badge ${badgeClass}">${badgeLabel}</span>
            <span class="stop-loc">${s.location_id}</span>
            <span class="stop-time">T+${s.estimated_arrival.toFixed(1)}m</span>
          </div>
        `;
      });

      card.innerHTML = `
        <div class="trip-card-header">
          <span class="trip-driver-badge">🚘 Driver: ${trip.driver_id}</span>
          <span class="trip-savings-pill">+${trip.saved_distance_km.toFixed(1)} km saved</span>
        </div>
        <div class="trip-meta-row">
          <span>Passengers: ${trip.request_ids.length} riders</span>
          <span>Detour: +${trip.driver_detour_min.toFixed(1)} min</span>
        </div>
        <div class="stops-sequence-view">
          ${stopsHtml}
        </div>
      `;

      card.addEventListener('click', () => {
        document.querySelectorAll('.trip-card').forEach((c) => c.classList.remove('selected'));
        card.classList.add('selected');
        state.selectedTripId = trip.id;
        selectedTripLabel.textContent = `Trip ${trip.id} (Driver: ${trip.driver_id}, ${trip.request_ids.length} riders, Saved: ${trip.saved_distance_km.toFixed(1)} km)`;
        renderMap();
      });

      manifestList.appendChild(card);
    });
  }

  // Generate Synthetic Batch
  btnGenerateBatch?.addEventListener('click', async () => {
    const [numReq, numOff] = (batchSizeSelect.value || '25_12').split('_').map(Number);
    btnGenerateBatch.disabled = true;
    btnGenerateBatch.innerHTML = '<span class="btn-icon">⏳</span> Synthesizing...';

    try {
      const res = await fetch('/api/generate-sample', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          num_requests: numReq,
          num_offers: numOff,
          direction: 'INBOUND',
          seed: Math.floor(Math.random() * 10000),
        }),
      });
      const data = await res.json();
      showToast(`Synthesized ${numReq} commuters and ${numOff} vehicles!`, 'success');
      loadSystemState();
    } catch (err) {
      console.error(err);
      showToast('Error synthesizing batch', 'danger');
    } finally {
      btnGenerateBatch.disabled = false;
      btnGenerateBatch.innerHTML = '<span class="btn-icon">⚡</span> Synthesize Rush';
    }
  });

  // Run FairPool Match
  btnRunMatch?.addEventListener('click', async () => {
    btnRunMatch.disabled = true;
    btnRunMatch.innerHTML = '<span class="btn-icon">⏳</span> Solving...';

    try {
      const enableFairness = checkFairnessToggle.checked;
      const res = await fetch('/api/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          algorithm: 'fairpool',
          enable_fairness: enableFairness,
          use_exact_solver: false,
          fairness_weight: 0.45,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Match failed');
      }

      const result = await res.json();
      state.latestResult = result;
      state.matchedTrips = result.matched_trips;
      updateKPIs(result);
      renderManifest(result.matched_trips);

      if (result.matched_trips.length > 0) {
        state.selectedTripId = result.matched_trips[0].id;
        selectedTripLabel.textContent = `Trip ${state.selectedTripId} (Driver: ${result.matched_trips[0].driver_id})`;
      }

      showToast(`Matching complete: ${result.matched_trips.length} pooled trips dispatched!`, 'success');
      renderMap();
      loadSystemState();
    } catch (err) {
      console.error(err);
      showToast(err.message || 'Error running match', 'danger');
    } finally {
      btnRunMatch.disabled = false;
      btnRunMatch.innerHTML = '<span class="btn-icon">🎯</span> Run FairPool Match';
    }
  });

  // Run Benchmark
  async function executeBenchmark() {
    const btn = btnTriggerBenchmark || btnRunBenchmark;
    btn.disabled = true;
    btn.innerHTML = 'Running 4-Way Evaluation...';

    try {
      const [numReq, numOff] = (batchSizeSelect.value || '25_12').split('_').map(Number);
      const res = await fetch('/api/benchmark', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          num_requests: numReq,
          num_offers: numOff,
          direction: 'INBOUND',
          seed: 42,
        }),
      });
      const data = await res.json();
      state.benchmarkData = data;
      renderBenchmarkResults(data);
      showToast('Deterministic benchmark completed across all 4 algorithms!', 'success');

      // Switch to benchmark tab
      document.querySelector('[data-tab="benchmarkTab"]')?.click();
    } catch (err) {
      console.error(err);
      showToast('Error executing benchmark', 'danger');
    } finally {
      btn.disabled = false;
      btn.innerHTML = 'Run 4-Way Evaluation';
    }
  }

  btnRunBenchmark?.addEventListener('click', executeBenchmark);
  btnTriggerBenchmark?.addEventListener('click', executeBenchmark);

  function renderBenchmarkResults(data) {
    const container = document.getElementById('benchmarkResultsView');
    if (!container || !data) return;

    const b = data.single_batch;
    const epoch = data.multi_epoch_study;

    container.innerHTML = `
      <div class="benchmark-card">
        <h4>Single-Batch Scientific Comparison (Seed: 42)</h4>
        <table class="benchmark-table">
          <thead>
            <tr>
              <th>Method</th>
              <th>Trips</th>
              <th>Match %</th>
              <th>Veh-km Saved</th>
              <th>Gini Detour</th>
              <th>Speed</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>No-Pooling (Solo)</td>
              <td>0</td>
              <td>0.0%</td>
              <td>0.0 km</td>
              <td>0.000</td>
              <td>${b.no_pool.runtime_ms.toFixed(2)}ms</td>
            </tr>
            <tr>
              <td>Greedy Nearest-Pair</td>
              <td>${b.greedy.matched_trips.length}</td>
              <td>${b.greedy.match_rate_percent.toFixed(1)}%</td>
              <td>${b.greedy.total_vkm_saved.toFixed(1)} km</td>
              <td>${b.greedy.gini_driver_detour.toFixed(4)}</td>
              <td>${b.greedy.runtime_ms.toFixed(2)}ms</td>
            </tr>
            <tr>
              <td>FairPool (Ablation - No Fairness)</td>
              <td>${b.fairpool_no_fairness.matched_trips.length}</td>
              <td>${b.fairpool_no_fairness.match_rate_percent.toFixed(1)}%</td>
              <td>${b.fairpool_no_fairness.total_vkm_saved.toFixed(1)} km</td>
              <td>${b.fairpool_no_fairness.gini_driver_detour.toFixed(4)}</td>
              <td>${b.fairpool_no_fairness.runtime_ms.toFixed(2)}ms</td>
            </tr>
            <tr class="highlight">
              <td>★ FairPool (Dynamic Fairness)</td>
              <td>${b.fairpool_fairness.matched_trips.length}</td>
              <td>${b.fairpool_fairness.match_rate_percent.toFixed(1)}%</td>
              <td>${b.fairpool_fairness.total_vkm_saved.toFixed(1)} km</td>
              <td>${b.fairpool_fairness.gini_driver_detour.toFixed(4)}</td>
              <td>${b.fairpool_fairness.runtime_ms.toFixed(2)}ms</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="benchmark-card">
        <h4>5-Day Multi-Epoch Fairness Convergence</h4>
        <p style="font-size:12px; color:#94A3B8; margin-bottom:10px;">
          Gini Detour Disparity over time (lower = fairer rotation). Notice FairPool steadily redistributes the burden.
        </p>
        <div class="epoch-chart-bar-container">
          ${epoch.fair_epoch_ginis
            .map(
              (g, i) => `
            <div class="epoch-bar-group">
              <div class="epoch-bar fair" style="height: ${Math.round(g * 80)}px;" title="Day ${i + 1} Fair Gini: ${g}"></div>
              <span class="epoch-label">Day ${i + 1}</span>
            </div>
          `
            )
            .join('')}
        </div>
        <div style="display:flex; justify-content:space-between; font-size:11px; color:#60A5FA; margin-top:12px;">
          <span>Initial Gini: ${epoch.fair_epoch_ginis[0]}</span>
          <span>Final Stabilized Gini: ${epoch.final_fair_gini}</span>
          <span>Total Saved: ${epoch.fair_vkm_saved_total} km</span>
        </div>
      </div>
    `;
  }

  // Load Current State from Server
  async function loadSystemState() {
    try {
      const res = await fetch('/api/state');
      const data = await res.json();
      state.requests = data.requests;
      state.offers = data.offers;

      if (data.latest_result) {
        state.latestResult = data.latest_result;
        state.matchedTrips = data.latest_result.matched_trips;
        updateKPIs(data.latest_result);
        renderManifest(data.latest_result.matched_trips);
      }

      // Update Fairness Ledger Tab
      const ledgerBody = document.getElementById('driverLedgerBody');
      const meanEl = document.getElementById('cohortMeanDetour');
      const giniEl = document.getElementById('cohortGiniDetour');

      if (meanEl) meanEl.textContent = `${data.mean_cumulative_detour_min} min`;
      if (giniEl) giniEl.textContent = data.cohort_gini.toFixed(4);

      if (ledgerBody && data.driver_cumulative_detours) {
        const drivers = Object.entries(data.driver_cumulative_detours);
        if (drivers.length > 0) {
          ledgerBody.innerHTML = drivers
            .map(([drvId, det]) => {
              const rel = det > data.mean_cumulative_detour_min ? 'Above Mean (Protected)' : 'Below Mean (Eligible)';
              const badgeClass = det > data.mean_cumulative_detour_min ? 'warning' : 'success';
              return `
                <tr>
                  <td><strong>${drvId}</strong></td>
                  <td>${det.toFixed(1)} min</td>
                  <td><span class="kpi-tag ${badgeClass}">${rel}</span></td>
                  <td>Active</td>
                </tr>
              `;
            })
            .join('');
        }
      }
    } catch (err) {
      console.error('Failed to load system state:', err);
    }
  }

  // Reset View Button
  btnResetView?.addEventListener('click', () => {
    state.selectedTripId = null;
    selectedTripLabel.textContent = 'Select a trip from the manifest panel to visualize its route';
    renderMap();
  });

  // Reset System Button
  btnResetAll?.addEventListener('click', async () => {
    if (!confirm('Reset all commute requests, offers, and simulation state?')) return;
    try {
      await fetch('/api/reset', { method: 'POST' });
      state.requests = [];
      state.offers = [];
      state.matchedTrips = [];
      state.selectedTripId = null;
      state.latestResult = null;
      updateKPIs({
        total_vkm_saved: 0,
        total_vkm_baseline_no_pool: 1,
        gini_driver_detour: 0,
        match_rate_percent: 0,
        runtime_ms: 0,
      });
      renderManifest([]);
      renderMap();
      showToast('System state reset successfully', 'info');
    } catch (err) {
      console.error(err);
    }
  });

  // Submit Rider Request Form
  document.getElementById('btnSubmitRequest')?.addEventListener('click', async () => {
    const riderId = document.getElementById('reqRiderId').value;
    const orig = document.getElementById('reqOriginSelect').value;
    const dest = document.getElementById('reqDestSelect').value;
    const dep = parseFloat(document.getElementById('reqEarliestDep').value) || 0;
    const buf = parseFloat(document.getElementById('reqBuffer').value) || 15;
    const tol = (parseFloat(document.getElementById('reqDetourSlider').value) || 35) / 100.0;

    if (orig === dest) {
      showToast('Origin and destination cannot be the same', 'warning');
      return;
    }

    try {
      const res = await fetch('/api/requests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rider_id: riderId,
          origin_id: orig,
          destination_id: dest,
          earliest_departure: dep,
          latest_arrival: dep + 20 + buf,
          max_detour_ratio: tol,
        }),
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Error submitting rider request');
      }
      const data = await res.json();
      showToast(`Request submitted for ${riderId}`, 'success');
      loadSystemState();
    } catch (err) {
      showToast(err.message || 'Error submitting rider request', 'warning');
    }
  });

  // Export Anonymized CSV Action (FR-20)
  document.getElementById('btnExportCsv')?.addEventListener('click', () => {
    window.location.href = '/api/export-csv';
    showToast('Exporting anonymized trip logs CSV (FR-20)...', 'success');
  });

  // Submit Driver Offer Form
  document.getElementById('btnSubmitOffer')?.addEventListener('click', async () => {
    const driverId = document.getElementById('offDriverId').value;
    const orig = document.getElementById('offOriginSelect').value;
    const dest = document.getElementById('offDestSelect').value;
    const dep = parseFloat(document.getElementById('offDepTime').value) || 0;
    const cap = parseInt(document.getElementById('offCapacitySelect').value) || 3;
    const detour = parseFloat(document.getElementById('offDetourSlider').value) || 18;

    if (orig === dest) {
      showToast('Origin and destination cannot be the same', 'warning');
      return;
    }

    try {
      const res = await fetch('/api/offers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          driver_id: driverId,
          origin_id: orig,
          destination_id: dest,
          departure_time: dep,
          capacity: cap,
          max_driver_detour_min: detour,
        }),
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Error submitting driver offer');
      }
      const data = await res.json();
      showToast(`Driver offer submitted by ${driverId}`, 'success');
      loadSystemState();
    } catch (err) {
      showToast(err.message || 'Error submitting driver offer', 'warning');
    }
  });

  // Initialize
  loadNetwork().then(() => {
    loadSystemState();
  });
});
