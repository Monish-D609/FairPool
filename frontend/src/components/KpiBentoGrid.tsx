import React from 'react'
import type { BatchMatchResult, SystemState } from '../types'
import { TrendingUp, ShieldCheck, Users, Car } from 'lucide-react'

interface KpiBentoGridProps {
  latestResult: BatchMatchResult | null
  systemState: SystemState | null
}

export const KpiBentoGrid: React.FC<KpiBentoGridProps> = ({ latestResult, systemState }) => {
  const vkmSaved = latestResult ? latestResult.total_vkm_saved : 0
  const baselineKm = latestResult ? latestResult.total_vkm_baseline_no_pool : 0
  const savingsPct = baselineKm > 0 ? ((vkmSaved / baselineKm) * 100).toFixed(0) : '0'
  const gini = latestResult ? latestResult.gini_driver_detour : (systemState?.cohort_gini ?? 0)
  const matchRate = latestResult ? latestResult.match_rate_percent.toFixed(0) : '0'
  const matchedRiders = latestResult
    ? latestResult.matched_trips.reduce((acc, t) => acc + t.request_ids.length, 0)
    : 0
  const totalRequests = systemState?.num_requests ?? 0
  const tripsCount = latestResult ? latestResult.matched_trips.length : 0

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/60 backdrop-blur-md border border-slate-800/80 rounded-xl px-4 py-2.5 mb-4 shadow-md">
      <div className="flex items-center gap-2.5">
        <span className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 shrink-0">
          <TrendingUp size={15} />
        </span>
        <div>
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">
            Distance Saved
          </span>
          <div className="text-sm font-bold font-mono text-white flex items-center gap-1.5">
            <span>{vkmSaved.toFixed(1)} km</span>
            <span className="text-[10px] text-emerald-400 font-sans font-normal">(-{savingsPct}%)</span>
          </div>
        </div>
      </div>

      <div className="h-6 w-px bg-slate-800 hidden sm:block" />

      <div className="flex items-center gap-2.5">
        <span className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400 shrink-0">
          <Users size={15} />
        </span>
        <div>
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">
            Matched Commuters
          </span>
          <div className="text-sm font-bold font-mono text-white flex items-center gap-1.5">
            <span>
              {matchedRiders} / {totalRequests}
            </span>
            <span className="text-[10px] text-cyan-400 font-sans font-normal">({matchRate}%)</span>
          </div>
        </div>
      </div>

      <div className="h-6 w-px bg-slate-800 hidden sm:block" />

      <div className="flex items-center gap-2.5">
        <span className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 shrink-0">
          <ShieldCheck size={15} />
        </span>
        <div>
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">
            Detour Fairness
          </span>
          <div className="text-sm font-bold font-mono text-white flex items-center gap-1.5">
            <span>{gini.toFixed(3)} Gini</span>
            <span className="text-[10px] text-emerald-400 font-sans font-normal">
              {gini <= 0.35 ? 'Balanced' : 'High Detour'}
            </span>
          </div>
        </div>
      </div>

      <div className="h-6 w-px bg-slate-800 hidden md:block" />

      <div className="flex items-center gap-2.5">
        <span className="p-1.5 rounded-lg bg-purple-500/10 text-purple-400 shrink-0">
          <Car size={15} />
        </span>
        <div>
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block font-semibold">
            Dispatched Pools
          </span>
          <div className="text-sm font-bold font-mono text-purple-300">
            {tripsCount} Active Pools
          </div>
        </div>
      </div>
    </div>
  )
}
