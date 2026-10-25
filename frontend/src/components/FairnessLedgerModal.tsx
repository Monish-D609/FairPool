import React from 'react'
import type { SystemState } from '../types'
import { X, Scale } from 'lucide-react'

interface FairnessLedgerModalProps {
  isOpen: boolean
  onClose: () => void
  systemState: SystemState | null
}

export const FairnessLedgerModal: React.FC<FairnessLedgerModalProps> = ({
  isOpen,
  onClose,
  systemState,
}) => {
  if (!isOpen) return null

  const detours = systemState?.driver_cumulative_detours || {}
  const drivers = Object.entries(detours).sort((a, b) => b[1] - a[1])
  const cohortGini = systemState?.cohort_gini ?? 0
  const meanDetour = systemState?.mean_cumulative_detour_min ?? 0

  return (
    <div className="fixed inset-0 z-[99999] flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-fade-in">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden max-h-[85vh] flex flex-col relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
              <Scale size={20} />
            </span>
            <div>
              <h3 className="text-base font-bold text-white">Dynamic Driver Fairness Ledger</h3>
              <p className="text-xs text-slate-400">
                Detour burden distribution ledger preventing repetitive driver detour fatigue
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Overview Stats */}
        <div className="p-6 overflow-y-auto space-y-4 custom-scrollbar">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800">
              <div className="text-xs text-slate-400 mb-1">Cohort Gini Coefficient</div>
              <div className="text-2xl font-bold font-mono text-emerald-400">
                {cohortGini.toFixed(4)}
              </div>
              <div className="text-[10px] text-slate-500 mt-1">
                Zero = Perfect equity | 1.0 = Extreme concentration
              </div>
            </div>

            <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800">
              <div className="text-xs text-slate-400 mb-1">Mean Historical Detour</div>
              <div className="text-2xl font-bold font-mono text-cyan-400">
                {meanDetour.toFixed(2)} min
              </div>
              <div className="text-[10px] text-slate-500 mt-1">
                Average extra driving burden per registered driver
              </div>
            </div>
          </div>

          {/* Drivers Table */}
          <div className="rounded-xl border border-slate-800 overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800 font-mono">
                <tr>
                  <th className="py-2.5 px-4">Driver Identifier</th>
                  <th className="py-2.5 px-4">Accumulated Detour</th>
                  <th className="py-2.5 px-4">Fairness Rotation Priority</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {drivers.map(([driverId, detourMin]) => {
                  const isHighDetour = detourMin > meanDetour * 1.2
                  return (
                    <tr key={driverId} className="text-slate-300">
                      <td className="py-2.5 px-4 font-sans font-medium flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                        <span>{driverId}</span>
                      </td>
                      <td className="py-2.5 px-4 font-bold text-white">
                        {detourMin.toFixed(1)} min
                      </td>
                      <td className="py-2.5 px-4">
                        {isHighDetour ? (
                          <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                            🛡️ Detour-Protected (Rotated to Direct Routes)
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400">
                            Eligible for Pooling Detour
                          </span>
                        )}
                      </td>
                    </tr>
                  )
                })}
                {drivers.length === 0 && (
                  <tr>
                    <td colSpan={3} className="py-6 text-center text-slate-500 text-xs">
                      No drivers registered in ledger yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
