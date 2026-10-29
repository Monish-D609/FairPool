import React from 'react'
import type { Trip, LocationNode } from '../types'
import { Car, ExternalLink, Clock, CheckCircle2 } from 'lucide-react'
import { getTripColor } from '../colors'

interface TripCardListProps {
  trips: Trip[]
  nodes: LocationNode[]
  selectedTripId: string | null
  onSelectTrip: (tripId: string | null) => void
  onRunMatch: () => void
  isMatching: boolean
}

export const TripCardList: React.FC<TripCardListProps> = ({
  trips,
  nodes,
  selectedTripId,
  onSelectTrip,
  onRunMatch,
  isMatching,
}) => {
  const nodeNameMap = new Map(nodes.map((n) => [n.id, n.name]))

  const openGoogleMapsDirections = (trip: Trip, e: React.MouseEvent) => {
    e.stopPropagation()
    const nodeMap = new Map(nodes.map((n) => [n.id, n]))
    const stopCoords = trip.stops
      .map((s) => nodeMap.get(s.location_id))
      .filter((n): n is LocationNode => !!n)

    if (stopCoords.length < 2) return

    const origin = `${stopCoords[0].lat},${stopCoords[0].lng}`
    const dest = `${stopCoords[stopCoords.length - 1].lat},${stopCoords[stopCoords.length - 1].lng}`
    const waypoints = stopCoords
      .slice(1, -1)
      .map((w) => `${w.lat},${w.lng}`)
      .join('|')

    const url = `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${dest}${
      waypoints ? `&waypoints=${waypoints}` : ''
    }&travelmode=driving`
    window.open(url, '_blank')
  }

  if (trips.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-slate-900/60 rounded-2xl border border-dashed border-slate-700/80 text-center h-full min-h-[300px]">
        <div className="w-12 h-12 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-400 mb-3">
          <Car size={24} />
        </div>
        <h4 className="text-base font-bold text-white mb-1">No Carpools Dispatched Yet</h4>
        <p className="text-xs text-slate-400 max-w-xs mb-4">
          Synthesize a rush batch or add commuter requests, then execute the FairPool solver to bundle
          compatible city-to-campus trips.
        </p>
        <button
          onClick={onRunMatch}
          disabled={isMatching}
          className="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-medium text-xs rounded-xl shadow-lg shadow-blue-500/25 transition disabled:opacity-50"
        >
          {isMatching ? 'Solving ILP / Set Packing...' : 'Run FairPool Match Now'}
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-3 overflow-y-auto max-h-[580px] pr-1 custom-scrollbar">
      {trips.map((trip, idx) => {
        const isSelected = selectedTripId === trip.id
        const color = getTripColor(idx)
        return (
          <div
            key={trip.id}
            onClick={() => onSelectTrip(isSelected ? null : trip.id)}
            style={{
              borderLeftColor: color,
              borderLeftWidth: '4px',
              ...(isSelected
                ? {
                    borderColor: color,
                    boxShadow: `0 0 20px ${color}35`,
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                  }
                : {}),
            }}
            className={`trip-card p-4 rounded-xl border transition-all cursor-pointer ${
              isSelected
                ? 'bg-slate-800/95'
                : 'bg-slate-900/70 hover:bg-slate-800/60 border-slate-700/60'
            }`}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-2.5">
              <div className="flex items-center gap-2.5">
                <span
                  className="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs shadow-sm transition"
                  style={{
                    backgroundColor: `${color}20`,
                    color: color,
                    border: `1px solid ${color}50`,
                  }}
                >
                  <Car size={16} />
                </span>
                <div>
                  <div className="text-xs font-bold text-white flex items-center gap-1.5">
                    <span
                      className="px-1.5 py-0.5 rounded text-[10px] font-extrabold uppercase font-mono tracking-wide"
                      style={{
                        backgroundColor: `${color}25`,
                        color: color,
                        border: `1px solid ${color}40`,
                      }}
                    >
                      Car #{idx + 1}
                    </span>
                    <span>{trip.id}</span>
                    <span className="text-[10px] font-normal text-slate-400">({trip.driver_id})</span>
                  </div>
                  <div className="text-[10px] text-emerald-400 font-medium flex items-center gap-1 mt-0.5">
                    <CheckCircle2 size={10} />
                    <span>{trip.request_ids.length} Commuters Matched</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-1.5">
                <button
                  onClick={(e) => openGoogleMapsDirections(trip, e)}
                  title="Open directions in Google Maps"
                  className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg border border-slate-700 transition text-[10px] flex items-center gap-1"
                >
                  <ExternalLink size={12} />
                  <span className="hidden sm:inline">Google Maps</span>
                </button>
              </div>
            </div>

            {/* Metrics Chips */}
            <div className="grid grid-cols-3 gap-2 mb-3 text-center">
              <div className="bg-slate-950/50 p-1.5 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-400">Dist Saved</div>
                <div className="text-xs font-mono font-bold text-cyan-400">
                  +{trip.saved_distance_km} km
                </div>
              </div>
              <div className="bg-slate-950/50 p-1.5 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-400">Driver Detour</div>
                <div className="text-xs font-mono font-bold text-amber-400">
                  +{trip.driver_detour_min}m
                </div>
              </div>
              <div className="bg-slate-950/50 p-1.5 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-400">Total Route</div>
                <div className="text-xs font-mono font-bold text-slate-200">
                  {trip.total_distance_km} km
                </div>
              </div>
            </div>

            {/* Stop-by-Stop Itinerary */}
            <div
              className="relative pl-3 space-y-2 border-l ml-1"
              style={{ borderLeftColor: `${color}40` }}
            >
              {trip.stops.map((stop, sIdx) => {
                const nodeName = nodeNameMap.get(stop.location_id) || stop.location_id
                const isOrigin = stop.stop_type === 'DRIVER_ORIGIN'
                const isDest = stop.stop_type === 'DRIVER_DESTINATION'

                return (
                  <div key={sIdx} className="relative flex items-center justify-between text-[11px]">
                    {/* Node Dot */}
                    <div
                      className="absolute -left-[17px] w-2 h-2 rounded-full"
                      style={{
                        backgroundColor: isDest ? '#10B981' : color,
                        boxShadow: `0 0 6px ${isDest ? '#10B981' : color}80`,
                      }}
                    />

                    <div className="flex items-center gap-1.5 text-slate-300">
                      <span className="font-medium truncate max-w-[170px]">{nodeName}</span>
                      <span className="text-[9px] text-slate-500 uppercase">
                        {isOrigin ? 'Start' : isDest ? 'VIT Campus' : `Stop #${sIdx + 1}`}
                      </span>
                    </div>

                    <div className="text-[10px] font-mono text-slate-400 flex items-center gap-1">
                      <Clock size={10} />
                      <span>{stop.estimated_arrival.toFixed(1)}m</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}
