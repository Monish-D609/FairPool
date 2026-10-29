import React, { useState, useEffect } from 'react'
import type { LocationNode, NetworkEdge, SystemState, Trip } from './types'
import {
  fetchNetwork,
  fetchState,
  generateSampleBatch,
  runMatch,
  resetSystem,
  updateNodePosition,
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
  Sparkles,
  Car,
} from 'lucide-react'
import './App.css'

export const App: React.FC = () => {
  const [nodes, setNodes] = useState<LocationNode[]>([])
  const [edges, setEdges] = useState<NetworkEdge[]>([])
  const [state, setState] = useState<SystemState | null>(null)
  const [selectedTripId, setSelectedTripId] = useState<string | null>(null)

  // Modals
  const [isCommuterModalOpen, setIsCommuterModalOpen] = useState(false)
  const [isBenchmarkModalOpen, setIsBenchmarkModalOpen] = useState(false)
  const [isFairnessModalOpen, setIsFairnessModalOpen] = useState(false)

  // Solver options
  const [algorithm, setAlgorithm] = useState<'fairpool' | 'greedy'>('fairpool')
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

  // Action: Move Pin Dynamically
  const handleNodeMove = (nodeId: string, lat: number, lng: number) => {
    setNodes((prev) =>
      prev.map((n) => (n.id === nodeId ? { ...n, lat, lng } : n))
    )
    // Sync new location with backend graph engine
    updateNodePosition(nodeId, lat, lng)
  }

  // Action: Synthesize Morning Rush
  const handleSynthesizeRush = async () => {
    setIsGenerating(true)
    try {
      await generateSampleBatch({
        num_requests: 12,
        num_offers: 5,
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
        enable_fairness: algorithm === 'fairpool',
        use_exact_solver: false,
        fairness_weight: 0.45,
      })
      const st = await fetchState()
      setState(st)
      if (res.matched_trips.length > 0) {
        setSelectedTripId(res.matched_trips[0].id)
      }
    } catch (err: any) {
      alert(`Matching failed: ${err.message}`)
    } finally {
      setIsMatching(false)
    }
  }

  // Action: Reset System
  const handleReset = async () => {
    if (confirm('Reset commute simulation to default 6-node corridor?')) {
      await resetSystem()
      await loadInitialData()
      setSelectedTripId(null)
    }
  }

  const trips: Trip[] = state?.latest_result?.matched_trips || []

  return (
    <div className="fairpool-app-container min-h-screen bg-[#080D1A] text-slate-100 flex flex-col font-sans">
      {/* Sleek Minimal Header */}
      <header className="sticky top-0 z-40 bg-[#0B132B]/90 backdrop-blur-md border-b border-slate-800 px-4 lg:px-8 py-2.5 flex items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 via-cyan-500 to-emerald-400 p-0.5 shadow-md shadow-cyan-500/20">
            <div className="w-full h-full bg-[#080D1A] rounded-[10px] flex items-center justify-center font-black text-cyan-400 text-sm">
              FP
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-extrabold tracking-tight text-white">FairPool</h1>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                VIT Chennai
              </span>
            </div>
            <p className="text-[10px] text-slate-400 hidden sm:block">
              City-to-Campus Carpool Engine · Vandalur-Kelambakkam Main Road
            </p>
          </div>
        </div>

        {/* Minimal Actions Bar */}
        <div className="flex items-center gap-2">
          {/* Quick Algorithm Switch */}
          <div className="hidden md:flex items-center bg-slate-900 border border-slate-800 p-0.5 rounded-xl text-xs font-semibold">
            <button
              onClick={() => setAlgorithm('fairpool')}
              className={`px-2.5 py-1 rounded-lg transition ${
                algorithm === 'fairpool'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              FairPool
            </button>
            <button
              onClick={() => setAlgorithm('greedy')}
              className={`px-2.5 py-1 rounded-lg transition ${
                algorithm === 'greedy'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Greedy
            </button>
          </div>

          {/* Synthesize Rush */}
          <button
            onClick={handleSynthesizeRush}
            disabled={isGenerating}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition"
            title="Generate sample commuter batch across Chennai"
          >
            <Sparkles size={13} className="text-cyan-400" />
            <span className="hidden sm:inline">
              {isGenerating ? 'Synthesizing...' : 'Synthesize Rush'}
            </span>
          </button>

          {/* Book / Offer Ride Modal */}
          <button
            onClick={() => setIsCommuterModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition"
          >
            <PlusCircle size={13} className="text-blue-400" />
            <span className="hidden sm:inline">Book / Offer</span>
          </button>

          {/* Run Match Action */}
          <button
            onClick={handleRunMatch}
            disabled={isMatching}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-xs font-bold text-white shadow-md shadow-emerald-500/20 transition disabled:opacity-50"
          >
            <Play size={12} fill="currentColor" />
            <span>{isMatching ? 'Matching...' : 'Run Match'}</span>
          </button>

          {/* Secondary Tools */}
          <div className="flex items-center gap-1 ml-1 border-l border-slate-800 pl-2">
            <button
              onClick={() => setIsFairnessModalOpen(true)}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition"
              title="Inspect Driver Fairness Ledger"
            >
              <Scale size={14} />
            </button>
            <button
              onClick={() => setIsBenchmarkModalOpen(true)}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition"
              title="Benchmark Algorithms"
            >
              <BarChart3 size={14} />
            </button>
            <button
              onClick={handleReset}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-red-500/20 text-slate-400 hover:text-red-400 border border-slate-700 transition"
              title="Reset state"
            >
              <RefreshCw size={14} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Workspace Body */}
      <main className="flex-1 p-4 lg:p-6 max-w-[1720px] mx-auto w-full flex flex-col">
        {/* Compact Stat Bar */}
        <KpiBentoGrid latestResult={state?.latest_result || null} systemState={state} />

        {/* 2-Column Clean Workspace: Map & Carpools */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 flex-1 min-h-[580px]">
          {/* Left Column (7/12 cols): Interactive Map with Dynamically Movable Pins */}
          <div className="lg:col-span-7 flex flex-col h-[520px] lg:h-auto min-h-[500px]">
            <GoogleMapVisualizer
              nodes={nodes}
              edges={edges}
              trips={trips}
              selectedTripId={selectedTripId}
              onSelectTrip={(id) => setSelectedTripId(id)}
              onNodeMove={handleNodeMove}
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

          {/* Right Column (5/12 cols): Formed Carpools Manifest */}
          <div className="lg:col-span-5 flex flex-col bg-slate-900/60 rounded-2xl border border-slate-800 p-4 shadow-xl">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400">
                  <Car size={15} />
                </div>
                <div>
                  <h2 className="text-xs font-bold text-white uppercase tracking-wider">
                    Matched Carpools
                  </h2>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {trips.length} active commuter bundles
                  </span>
                </div>
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

            {/* Carpool Trip Cards */}
            <div className="flex-1 overflow-hidden">
              <TripCardList
                trips={trips}
                nodes={nodes}
                selectedTripId={selectedTripId}
                onSelectTrip={(id) => setSelectedTripId(id)}
                onRunMatch={handleRunMatch}
                isMatching={isMatching}
              />
            </div>
          </div>
        </div>
      </main>

      {/* Modals */}
      <CommuterModal
        isOpen={isCommuterModalOpen}
        onClose={() => {
          setIsCommuterModalOpen(false)
          setPickedOrigin(null)
          setPickedDest(null)
        }}
        nodes={nodes}
        initialOrigin={pickedOrigin}
        initialDestination={pickedDest}
        onSuccess={loadInitialData}
        onNodeAdded={loadInitialData}
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
