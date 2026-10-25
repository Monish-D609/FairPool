import React, { useState, useEffect } from 'react'
import type { LocationNode, NetworkEdge, SystemState, Trip } from './types'
import {
  fetchNetwork,
  fetchState,
  generateSampleBatch,
  runMatch,
  resetSystem,
  getExportCsvUrl,
} from './api'
import { GoogleMapVisualizer } from './components/GoogleMapVisualizer'
import { KpiBentoGrid } from './components/KpiBentoGrid'
import { TripCardList } from './components/TripCardList'
import { CommuterModal } from './components/CommuterModal'
import { BenchmarkModal } from './components/BenchmarkModal'
import { FairnessLedgerModal } from './components/FairnessLedgerModal'
import {
  Play,
  RefreshCw,
  PlusCircle,
  BarChart3,
  Scale,
  Download,
  Clock,
  Sparkles,
  Sliders,
  Users,
  Car,
  ChevronRight,
} from 'lucide-react'
import './App.css'

export const App: React.FC = () => {
  const [nodes, setNodes] = useState<LocationNode[]>([])
  const [edges, setEdges] = useState<NetworkEdge[]>([])
  const [state, setState] = useState<SystemState | null>(null)
  const [selectedTripId, setSelectedTripId] = useState<string | null>(null)
  const [activeRightTab, setActiveRightTab] = useState<'trips' | 'queue' | 'settings'>('trips')

  // Modals
  const [isCommuterModalOpen, setIsCommuterModalOpen] = useState(false)
  const [isBenchmarkModalOpen, setIsBenchmarkModalOpen] = useState(false)
  const [isFairnessModalOpen, setIsFairnessModalOpen] = useState(false)

  // Solver options
  const [algorithm, setAlgorithm] = useState<'fairpool' | 'greedy' | 'no_pool'>('fairpool')
  const [enableFairness, setEnableFairness] = useState(true)
  const [useExactSolver, setUseExactSolver] = useState(false)
  const [fairnessWeight, setFairnessWeight] = useState(0.45)
  const [isMatching, setIsMatching] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)

  // Map click origin/dest
  const [pickedOrigin, setPickedOrigin] = useState<LocationNode | null>(null)
  const [pickedDest, setPickedDest] = useState<LocationNode | null>(null)

  // Initial load
  const loadInitialData = async () => {
    try {
      const net = await fetchNetwork()
      setNodes(net.nodes)
      setEdges(net.edges)

      const st = await fetchState()
      setState(st)
    } catch (err) {
      console.error('Failed to load initial FairPool data:', err)
    }
  }

  useEffect(() => {
    loadInitialData()
  }, [])

  // Action: Synthesize Morning Rush
  const handleSynthesizeRush = async () => {
    setIsGenerating(true)
    try {
      await generateSampleBatch({
        num_requests: 30,
        num_offers: 12,
        direction: 'INBOUND',
        seed: Math.floor(Math.random() * 1000),
      })
      const st = await fetchState()
      setState(st)
    } catch (err: any) {
      alert(`Synthesis failed: ${err.message}`)
    } finally {
      setIsGenerating(false)
    }
  }

  // Action: Run Matching Engine
  const handleRunMatch = async () => {
    setIsMatching(true)
    try {
      const res = await runMatch({
        algorithm,
        enable_fairness: enableFairness,
        use_exact_solver: useExactSolver,
        fairness_weight: fairnessWeight,
      })
      const st = await fetchState()
      setState(st)
      if (res.matched_trips.length > 0) {
        setSelectedTripId(res.matched_trips[0].id)
        setActiveRightTab('trips')
      }
    } catch (err: any) {
      alert(`Matching failed: ${err.message}`)
    } finally {
      setIsMatching(false)
    }
  }

  // Action: Reset System
  const handleReset = async () => {
    if (confirm('Reset current commute simulation, matching pool, and ledger?')) {
      await resetSystem()
      const st = await fetchState()
      setState(st)
      setSelectedTripId(null)
    }
  }

  const trips: Trip[] = state?.latest_result?.matched_trips || []

  return (
    <div className="fairpool-app-container min-h-screen bg-[#080D1A] text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="navbar-header sticky top-0 z-40 bg-[#0B132B]/85 backdrop-blur-md border-b border-slate-800 px-4 lg:px-8 py-3 flex flex-wrap items-center justify-between gap-4">
        {/* Brand & Context */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-cyan-500 to-emerald-400 p-0.5 shadow-lg shadow-cyan-500/20">
            <div className="w-full h-full bg-[#080D1A] rounded-[10px] flex items-center justify-center font-black text-cyan-400 text-lg">
              FP
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-extrabold tracking-tight text-white">FairPool</h1>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                Chennai Metro
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              City-to-Campus Algorithmic Carpooling & Detour Equity Engine
            </p>
          </div>
        </div>

        {/* Peak Rush Status & Quick Actions */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Commute Window Indicator */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-amber-300">
            <Clock size={13} className="text-amber-400" />
            <span className="font-semibold">Morning Rush</span>
            <span className="text-[10px] text-slate-400 font-mono">08:00 - 09:30 AM</span>
          </div>

          {/* Action: Synthesize Rush */}
          <button
            onClick={handleSynthesizeRush}
            disabled={isGenerating}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition"
            title="Generate synthetic commuters from Tambaram, Porur, Anna Nagar, Velachery, etc."
          >
            <Sparkles size={13} className="text-cyan-400" />
            <span>{isGenerating ? 'Synthesizing...' : 'Synthesize Rush'}</span>
          </button>

          {/* Action: Join Commute (Modal) */}
          <button
            onClick={() => setIsCommuterModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white shadow-md shadow-blue-500/25 transition"
          >
            <PlusCircle size={13} />
            <span>Book / Offer Ride</span>
          </button>

          {/* Action: Run Match */}
          <button
            onClick={handleRunMatch}
            disabled={isMatching}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-xs font-bold text-white shadow-lg shadow-emerald-500/25 transition disabled:opacity-50"
          >
            <Play size={13} fill="currentColor" />
            <span>{isMatching ? 'Solving Set Packing...' : 'Run FairPool Match'}</span>
          </button>

          {/* Secondary Actions */}
          <button
            onClick={() => setIsBenchmarkModalOpen(true)}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition"
            title="Open Comparative Benchmark Suite"
          >
            <BarChart3 size={15} />
          </button>

          <button
            onClick={() => setIsFairnessModalOpen(true)}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition"
            title="Inspect Driver Fairness Ledger"
          >
            <Scale size={15} />
          </button>

          <a
            href={getExportCsvUrl()}
            download
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition"
            title="Download Anonymized Trips CSV (FR-20)"
          >
            <Download size={15} />
          </a>

          <button
            onClick={handleReset}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-red-500/20 text-slate-400 hover:text-red-400 border border-slate-700 transition"
            title="Reset system state"
          >
            <RefreshCw size={15} />
          </button>
        </div>
      </header>

      {/* Main Workspace Body */}
      <main className="flex-1 p-4 lg:p-6 max-w-[1720px] mx-auto w-full flex flex-col">
        {/* Bento Box KPIs */}
        <KpiBentoGrid latestResult={state?.latest_result || null} systemState={state} />

        {/* 2-Column Split Workspace */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-[580px]">
          {/* Left Column (7/12 cols): Google Maps Visualizer */}
          <div className="lg:col-span-7 flex flex-col h-[520px] lg:h-auto min-h-[500px]">
            <GoogleMapVisualizer
              nodes={nodes}
              edges={edges}
              trips={trips}
              selectedTripId={selectedTripId}
              onSelectTrip={(id) => setSelectedTripId(id)}
              onSelectNodeAsOrigin={(n) => {
                setPickedOrigin(n)
                setIsCommuterModalOpen(true)
              }}
              onSelectNodeAsDestination={(n) => {
                setPickedDest(n)
                setIsCommuterModalOpen(true)
              }}
            />
          </div>

          {/* Right Column (5/12 cols): Operational Control & Trip Manifest */}
          <div className="lg:col-span-5 flex flex-col bg-slate-900/60 rounded-2xl border border-slate-800 p-4 shadow-xl">
            {/* Tab Navigation */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
              <div className="flex items-center gap-1 bg-slate-950/80 p-1 rounded-xl border border-slate-800">
                <button
                  onClick={() => setActiveRightTab('trips')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                    activeRightTab === 'trips'
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Car size={13} />
                  <span>Carpools ({trips.length})</span>
                </button>

                <button
                  onClick={() => setActiveRightTab('queue')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                    activeRightTab === 'queue'
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Users size={13} />
                  <span>Commuter Pool ({state?.num_requests || 0})</span>
                </button>

                <button
                  onClick={() => setActiveRightTab('settings')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                    activeRightTab === 'settings'
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Sliders size={13} />
                  <span>Solver Settings</span>
                </button>
              </div>

              {selectedTripId && (
                <button
                  onClick={() => setSelectedTripId(null)}
                  className="text-[11px] text-cyan-400 hover:underline"
                >
                  Clear Selection
                </button>
              )}
            </div>

            {/* Tab Content: Trips */}
            {activeRightTab === 'trips' && (
              <div className="flex-1 flex flex-col">
                <TripCardList
                  trips={trips}
                  nodes={nodes}
                  selectedTripId={selectedTripId}
                  onSelectTrip={(id) => setSelectedTripId(id)}
                  onRunMatch={handleRunMatch}
                  isMatching={isMatching}
                />
              </div>
            )}

            {/* Tab Content: Queue */}
            {activeRightTab === 'queue' && (
              <div className="flex-1 overflow-y-auto space-y-4 max-h-[540px] pr-1 custom-scrollbar">
                {/* Rider Requests */}
                <div>
                  <div className="flex items-center justify-between text-xs font-bold text-slate-300 mb-2">
                    <span>Pending Rider Requests ({state?.requests.length || 0})</span>
                    <span className="text-[10px] text-slate-500 font-normal">
                      City Suburb &rarr; Hub
                    </span>
                  </div>
                  <div className="space-y-1.5">
                    {state?.requests.slice(0, 15).map((r) => (
                      <div
                        key={r.id}
                        className="p-2.5 rounded-lg bg-slate-950/50 border border-slate-800/80 flex items-center justify-between text-xs"
                      >
                        <div>
                          <div className="font-semibold text-white flex items-center gap-1.5">
                            <span>{r.origin_id}</span>
                            <ChevronRight size={12} className="text-slate-500" />
                            <span className="text-emerald-400">{r.destination_id}</span>
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono">
                            {r.rider_id} | Direct: {r.direct_distance_km}km
                          </div>
                        </div>
                        <span
                          className={`text-[9px] font-mono px-2 py-0.5 rounded-full ${
                            r.status === 'MATCHED'
                              ? 'bg-emerald-500/20 text-emerald-300'
                              : 'bg-amber-500/20 text-amber-300'
                          }`}
                        >
                          {r.status}
                        </span>
                      </div>
                    ))}
                    {(state?.requests.length || 0) === 0 && (
                      <div className="text-center py-6 text-slate-500 text-xs">
                        No rider requests queued. Click "Synthesize Rush" or "Book Ride".
                      </div>
                    )}
                  </div>
                </div>

                {/* Driver Offers */}
                <div>
                  <div className="flex items-center justify-between text-xs font-bold text-slate-300 mb-2">
                    <span>Available Driver Offers ({state?.offers.length || 0})</span>
                  </div>
                  <div className="space-y-1.5">
                    {state?.offers.slice(0, 10).map((o) => (
                      <div
                        key={o.id}
                        className="p-2.5 rounded-lg bg-slate-950/50 border border-slate-800/80 flex items-center justify-between text-xs"
                      >
                        <div>
                          <div className="font-semibold text-white flex items-center gap-1.5">
                            <span>{o.origin_id}</span>
                            <ChevronRight size={12} className="text-slate-500" />
                            <span className="text-emerald-400">{o.destination_id}</span>
                          </div>
                          <div className="text-[10px] text-slate-400 font-mono">
                            {o.driver_id} | Seats: {o.capacity} | Max Detour: +{o.max_driver_detour_min}m
                          </div>
                        </div>
                        <span
                          className={`text-[9px] font-mono px-2 py-0.5 rounded-full ${
                            o.status === 'ASSIGNED'
                              ? 'bg-blue-500/20 text-blue-300'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {o.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Tab Content: Solver Settings */}
            {activeRightTab === 'settings' && (
              <div className="flex-1 space-y-5 p-2 text-xs">
                {/* Algorithm Choice */}
                <div>
                  <label className="block font-bold text-slate-300 mb-2">Matching Algorithm</label>
                  <div className="space-y-2">
                    {[
                      {
                        id: 'fairpool',
                        title: 'FairPool Set-Packing Engine (Recommended)',
                        desc: 'Bipartite shareability graph + Branch & Bound stop ordering + Detour fairness penalty',
                      },
                      {
                        id: 'greedy',
                        title: 'Greedy Nearest-Pair Matcher',
                        desc: 'Standard local greedy pairing baseline (ignores long-term driver fairness)',
                      },
                      {
                        id: 'no_pool',
                        title: 'No-Pooling Solo Commute Baseline',
                        desc: 'Single occupancy vehicles (unpooled reference)',
                      },
                    ].map((opt) => (
                      <label
                        key={opt.id}
                        className={`flex items-start gap-2.5 p-3 rounded-xl border cursor-pointer transition ${
                          algorithm === opt.id
                            ? 'bg-blue-600/10 border-blue-500/60 text-white'
                            : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:border-slate-700'
                        }`}
                      >
                        <input
                          type="radio"
                          name="algo"
                          checked={algorithm === opt.id}
                          onChange={() => setAlgorithm(opt.id as any)}
                          className="mt-0.5 accent-blue-500"
                        />
                        <div>
                          <div className="font-semibold text-slate-200">{opt.title}</div>
                          <div className="text-[11px] text-slate-500 mt-0.5">{opt.desc}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Fairness Weight */}
                <div className="p-3 bg-slate-950/50 rounded-xl border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200">Dynamic Fairness Weight (&alpha;)</span>
                    <span className="font-mono text-cyan-400 font-bold">{fairnessWeight.toFixed(2)}</span>
                  </div>
                  <input
                    type="range"
                    min="0.0"
                    max="1.0"
                    step="0.05"
                    value={fairnessWeight}
                    onChange={(e) => setFairnessWeight(parseFloat(e.target.value))}
                    className="w-full accent-cyan-500"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500">
                    <span>Pure Distance Savings (0.0)</span>
                    <span>Balanced (0.45)</span>
                    <span>Maximum Driver Equity (1.0)</span>
                  </div>
                </div>

                {/* Toggles */}
                <div className="space-y-2">
                  <label className="flex items-center justify-between p-3 bg-slate-950/50 rounded-xl border border-slate-800 cursor-pointer">
                    <span className="text-slate-300 font-medium">Enable Historical Detour Tracking</span>
                    <input
                      type="checkbox"
                      checked={enableFairness}
                      onChange={(e) => setEnableFairness(e.target.checked)}
                      className="w-4 h-4 accent-blue-500 rounded"
                    />
                  </label>

                  <label className="flex items-center justify-between p-3 bg-slate-950/50 rounded-xl border border-slate-800 cursor-pointer">
                    <span className="text-slate-300 font-medium">Use Exact MILP Branch & Bound Solver</span>
                    <input
                      type="checkbox"
                      checked={useExactSolver}
                      onChange={(e) => setUseExactSolver(e.target.checked)}
                      className="w-4 h-4 accent-blue-500 rounded"
                    />
                  </label>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Modals */}
      <CommuterModal
        isOpen={isCommuterModalOpen}
        onClose={() => setIsCommuterModalOpen(false)}
        nodes={nodes}
        initialOrigin={pickedOrigin}
        initialDestination={pickedDest}
        onSuccess={async () => {
          const st = await fetchState()
          setState(st)
        }}
      />

      <BenchmarkModal
        isOpen={isBenchmarkModalOpen}
        onClose={() => setIsBenchmarkModalOpen(false)}
      />

      <FairnessLedgerModal
        isOpen={isFairnessModalOpen}
        onClose={() => setIsFairnessModalOpen(false)}
        systemState={state}
      />
    </div>
  )
}
export default App
