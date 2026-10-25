import React from 'react'
import type { BatchMatchResult, SystemState } from '../types'
import { TrendingUp, ShieldCheck, Users, Zap, Leaf, Car } from 'lucide-react'

interface KpiBentoGridProps {
  latestResult: BatchMatchResult | null
  systemState: SystemState | null
}

export const KpiBentoGrid: React.FC<KpiBentoGridProps> = ({ latestResult, systemState }) => {
  const vkmSaved = latestResult ? latestResult.total_vkm_saved : 0
  const baselineKm = latestResult ? latestResult.total_vkm_baseline_no_pool : 0
  const savingsPct = baselineKm > 0 ? ((vkmSaved / baselineKm) * 100).toFixed(1) : '0.0'
  const co2SavedKg = (vkmSaved * 0.171).toFixed(1) // 171g CO2/km average ICE passenger car

  const gini = latestResult ? latestResult.gini_driver_detour : (systemState?.cohort_gini ?? 0)
  const matchRate = latestResult ? latestResult.match_rate_percent.toFixed(1) : '0.0'
  const matchedTripsCount = latestResult ? latestResult.matched_trips.length : 0
  const matchedRidersCount = latestResult
    ? latestResult.matched_trips.reduce((acc, t) => acc + t.request_ids.length, 0)
    : 0

  const runtimeMs = latestResult ? latestResult.runtime_ms.toFixed(1) : '0.0'
  const meanDetour = latestResult ? latestResult.mean_driver_detour_min.toFixed(1) : '0.0'

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* KPI 1: VKM Saved & Carbon Offset */}
      <div className="bento-card relative overflow-hidden group">
        <div className="card-ambient-glow bg-cyan-500/10"></div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
            <TrendingUp size={14} />
            Vehicle-Km Saved
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
            +{savingsPct}% vs Solo
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-extrabold font-mono tracking-tight text-white">
            {vkmSaved.toFixed(1)}
          </span>
          <span className="text-sm font-medium text-slate-400">veh-km</span>
        </div>
        <div className="mt-3 flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
          <Leaf size={13} />
          <span>~{co2SavedKg} kg CO₂ averted</span>
        </div>
      </div>

      {/* KPI 2: Detour Fairness Gini */}
      <div className="bento-card relative overflow-hidden group">
        <div className="card-ambient-glow bg-emerald-500/10"></div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
            <ShieldCheck size={14} />
            Driver Detour Gini
          </span>
          <span
            className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
              gini < 0.4
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
            }`}
          >
            {gini < 0.4 ? 'Equitable (Low)' : 'Moderate Drift'}
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-extrabold font-mono tracking-tight text-white">
            {gini.toFixed(4)}
          </span>
          <span className="text-xs text-slate-400">cohort index</span>
        </div>
        <div className="mt-3 text-xs text-slate-400 flex items-center justify-between">
          <span>Mean Detour:</span>
          <span className="font-mono text-slate-200 font-semibold">{meanDetour} min</span>
        </div>
      </div>

      {/* KPI 3: Commuter Match Rate */}
      <div className="bento-card relative overflow-hidden group">
        <div className="card-ambient-glow bg-amber-500/10"></div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
            <Users size={14} />
            Match Fulfillment
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
            {matchedRidersCount} / {systemState?.num_requests ?? 0} Riders
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-extrabold font-mono tracking-tight text-white">
            {matchRate}%
          </span>
          <span className="text-xs text-slate-400">served</span>
        </div>
        <div className="mt-3 text-xs text-slate-400 flex items-center justify-between">
          <span className="flex items-center gap-1">
            <Car size={13} /> Dispatched Pools:
          </span>
          <span className="font-mono text-slate-200 font-semibold">{matchedTripsCount} trips</span>
        </div>
      </div>

      {/* KPI 4: Solver Latency & Efficiency */}
      <div className="bento-card relative overflow-hidden group">
        <div className="card-ambient-glow bg-purple-500/10"></div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-purple-400 flex items-center gap-1.5">
            <Zap size={14} />
            Solver Latency
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
            {latestResult?.algorithm_name || 'FairPool Engine'}
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-extrabold font-mono tracking-tight text-white">
            {runtimeMs}
          </span>
          <span className="text-sm font-medium text-slate-400">ms</span>
        </div>
        <div className="mt-3 text-xs text-slate-400 flex items-center justify-between">
          <span>Max Detour Bound:</span>
          <span className="font-mono text-emerald-400 font-semibold">&le; 35% enforced</span>
        </div>
      </div>
    </div>
  )
}
