import React, { useState } from 'react'
import type { BenchmarkResponse } from '../types'
import { runBenchmark } from '../api'
import { X, BarChart3, CheckCircle2, TrendingDown, Cpu } from 'lucide-react'

interface BenchmarkModalProps {
  isOpen: boolean
  onClose: () => void
}

export const BenchmarkModal: React.FC<BenchmarkModalProps> = ({ isOpen, onClose }) => {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<BenchmarkResponse | null>(null)
  const [numRequests, setNumRequests] = useState(30)
  const [numOffers, setNumOffers] = useState(12)

  if (!isOpen) return null

  const handleRun = async () => {
    setLoading(true)
    try {
      const res = await runBenchmark({
        num_requests: numRequests,
        num_offers: numOffers,
        direction: 'INBOUND',
        seed: 42,
      })
      setData(res)
    } catch (err: any) {
      alert(`Benchmark failed: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-fade-in">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-4xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-purple-500/10 text-purple-400">
              <BarChart3 size={20} />
            </span>
            <div>
              <h3 className="text-base font-bold text-white">Algorithmic Benchmark Harness</h3>
              <p className="text-xs text-slate-400">
                Comparative Analysis: No-Pool vs Greedy Nearest Pair vs FairPool MILP Set Packing
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

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 custom-scrollbar">
          {/* Controls */}
          <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-slate-950/60 rounded-xl border border-slate-800">
            <div className="flex items-center gap-4 text-xs">
              <div>
                <span className="text-slate-400 block mb-1">Commuters Batch:</span>
                <input
                  type="number"
                  min="10"
                  max="100"
                  value={numRequests}
                  onChange={(e) => setNumRequests(parseInt(e.target.value) || 25)}
                  className="w-20 px-2 py-1 bg-slate-800 border border-slate-700 rounded font-mono text-white text-xs font-bold"
                />
              </div>
              <div className="w-px h-8 bg-slate-800"></div>
              <div>
                <span className="text-slate-400 block mb-1">Available Drivers:</span>
                <input
                  type="number"
                  min="4"
                  max="40"
                  value={numOffers}
                  onChange={(e) => setNumOffers(parseInt(e.target.value) || 10)}
                  className="w-16 px-2 py-1 bg-slate-800 border border-slate-700 rounded font-mono text-white text-xs font-bold"
                />
              </div>
              <div className="w-px h-8 bg-slate-800"></div>
              <div>
                <span className="text-slate-400 block mb-1">Corridor:</span>
                <span className="text-cyan-400 font-semibold">Chennai City &rarr; Campus</span>
              </div>
            </div>

            <button
              onClick={handleRun}
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-purple-500/25 transition disabled:opacity-50"
            >
              <Cpu size={14} />
              <span>{loading ? 'Evaluating Solvers...' : 'Run Comparative Benchmark'}</span>
            </button>
          </div>

          {/* Results Table */}
          {data?.single_batch && (
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
                <span>Single-Batch Performance Matrix</span>
              </h4>
              <div className="overflow-x-auto rounded-xl border border-slate-800">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800 font-mono">
                    <tr>
                      <th className="py-3 px-4">Algorithm</th>
                      <th className="py-3 px-4">Match %</th>
                      <th className="py-3 px-4">VKM Saved</th>
                      <th className="py-3 px-4">Driver Detour</th>
                      <th className="py-3 px-4">Cohort Gini</th>
                      <th className="py-3 px-4">Runtime</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {Object.entries(data.single_batch).map(([key, m]) => {
                      const isFairPool = key.includes('FairPool')
                      return (
                        <tr
                          key={key}
                          className={isFairPool ? 'bg-cyan-500/5 font-semibold text-white' : 'text-slate-300'}
                        >
                          <td className="py-3 px-4 flex items-center gap-1.5 font-sans">
                            {isFairPool && <CheckCircle2 size={12} className="text-cyan-400" />}
                            <span>{m.algorithm_name}</span>
                          </td>
                          <td className="py-3 px-4">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] ${
                                m.match_rate_percent > 70
                                  ? 'bg-emerald-500/20 text-emerald-300'
                                  : 'bg-slate-800 text-slate-400'
                              }`}
                            >
                              {m.match_rate_percent.toFixed(1)}%
                            </span>
                          </td>
                          <td className="py-3 px-4 text-cyan-400 font-bold">
                            {m.vkm_saved.toFixed(1)} km
                          </td>
                          <td className="py-3 px-4 text-amber-400">
                            {m.mean_driver_detour_min.toFixed(1)} min
                          </td>
                          <td className="py-3 px-4">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] ${
                                m.gini_driver_detour < 0.4
                                  ? 'bg-emerald-500/20 text-emerald-300'
                                  : 'bg-amber-500/20 text-amber-300'
                              }`}
                            >
                              {m.gini_driver_detour.toFixed(4)}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-purple-400">{m.runtime_ms.toFixed(1)} ms</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Multi-Epoch Fairness Rotation Study */}
          {data?.multi_epoch_study && (
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-2 flex items-center gap-2">
                <TrendingDown size={14} className="text-emerald-400" />
                <span>5-Day Fairness Rotation (Gini Reduction over Time)</span>
              </h4>
              <p className="text-xs text-slate-400 mb-3">
                Demonstrates how FairPool's dynamic historical detour penalty prevents driver burnout by
                rotating detours across 5 consecutive morning rush batches.
              </p>

              <div className="grid grid-cols-5 gap-3">
                {data.multi_epoch_study.map((ep) => (
                  <div
                    key={ep.epoch}
                    className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 text-center"
                  >
                    <div className="text-[11px] font-bold text-slate-300 mb-1">Day {ep.epoch}</div>
                    <div className="space-y-1 text-xs">
                      <div className="text-[10px] text-slate-400">Standard Gini</div>
                      <div className="font-mono text-amber-400 font-semibold">
                        {ep.gini_no_fairness.toFixed(3)}
                      </div>
                      <div className="text-[10px] text-slate-400 mt-2">FairPool Gini</div>
                      <div className="font-mono text-emerald-400 font-bold">
                        {ep.gini_with_fairness.toFixed(3)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!data && !loading && (
            <div className="p-8 text-center text-slate-500 text-xs">
              Click "Run Comparative Benchmark" to execute the solver harness across all algorithms.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
