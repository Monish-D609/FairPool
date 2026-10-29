import React, { useState, useEffect } from 'react'
import type { LocationNode } from '../types'
import { submitRiderRequest, submitDriverOffer } from '../api'
import { X, UserPlus, Car, MapPin, AlertCircle, CheckCircle2 } from 'lucide-react'

interface CommuterModalProps {
  isOpen: boolean
  onClose: () => void
  nodes: LocationNode[]
  initialOrigin?: LocationNode | null
  initialDestination?: LocationNode | null
  onSuccess: () => void
}

export const CommuterModal: React.FC<CommuterModalProps> = ({
  isOpen,
  onClose,
  nodes,
  initialOrigin,
  initialDestination: _initialDestination,
  onSuccess,
}) => {
  const [activeTab, setActiveTab] = useState<'rider' | 'driver'>('rider')
  const [riderId, setRiderId] = useState('student@vitstudent.ac.in')
  const [driverId, setDriverId] = useState('faculty@vit.ac.in')
  const [originId, setOriginId] = useState(initialOrigin?.id || 'TAMBARAM')
  const [destId, setDestId] = useState('VIT_CHENNAI')
  const [capacity, setCapacity] = useState(3)
  const [maxDetourRatio, setMaxDetourRatio] = useState(0.35)
  const [maxDriverDetourMin, setMaxDriverDetourMin] = useState(18)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Sync origin/destination when modal opens or map node selection changes
  useEffect(() => {
    if (isOpen) {
      if (initialOrigin && initialOrigin.id !== 'VIT_CHENNAI') {
        setOriginId(initialOrigin.id)
      }
      setDestId('VIT_CHENNAI')
      // Reset feedback messages on each open
      setErrorMsg(null)
      setSuccessMsg(null)
    }
  }, [isOpen, initialOrigin])

  if (!isOpen) return null

  const suburbs = nodes.filter((n) => !n.is_campus_hub)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg(null)
    setSuccessMsg(null)
    setIsSubmitting(true)

    try {
      const targetOrigin = originId || suburbs[0]?.id || 'TAMBARAM'
      const targetDest = destId || 'VIT_CHENNAI'

      if (activeTab === 'rider') {
        await submitRiderRequest({
          rider_id: riderId.trim(),
          origin_id: targetOrigin,
          destination_id: targetDest,
          earliest_departure: 0.0,
          latest_arrival: 45.0,
          max_detour_ratio: maxDetourRatio,
        })
        setSuccessMsg(`Rider request for ${riderId.trim()} registered!`)
      } else {
        await submitDriverOffer({
          driver_id: driverId.trim(),
          origin_id: targetOrigin,
          destination_id: targetDest,
          departure_time: 5.0,
          capacity: capacity,
          max_driver_detour_min: maxDriverDetourMin,
        })
        setSuccessMsg(`Driver offer for ${driverId.trim()} registered with ${capacity} seats!`)
      }

      setTimeout(() => {
        onSuccess()
        onClose()
      }, 900)
    } catch (err: any) {
      setErrorMsg(err.message || 'Error submitting commuter entry')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[99999] flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-fade-in">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-blue-500/10 text-blue-400">
              <UserPlus size={18} />
            </span>
            <div>
              <h3 className="text-base font-bold text-white">Join Morning/Evening Commute</h3>
              <p className="text-xs text-slate-400">Chennai City-to-Campus Algorithmic Carpool</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex p-2 bg-slate-950/60 border-b border-slate-800">
          <button
            onClick={() => setActiveTab('rider')}
            className={`flex-1 py-2 text-xs font-semibold rounded-xl flex items-center justify-center gap-2 transition ${
              activeTab === 'rider'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <MapPin size={14} />
            <span>I Need a Ride (Rider Request)</span>
          </button>
          <button
            onClick={() => setActiveTab('driver')}
            className={`flex-1 py-2 text-xs font-semibold rounded-xl flex items-center justify-center gap-2 transition ${
              activeTab === 'driver'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Car size={14} />
            <span>I Am Driving (Driver Offer)</span>
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {errorMsg && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-xs text-red-400 flex items-center gap-2">
              <AlertCircle size={14} />
              <span>{errorMsg}</span>
            </div>
          )}
          {successMsg && (
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-xs text-emerald-400 flex items-center gap-2">
              <CheckCircle2 size={14} />
              <span>{successMsg}</span>
            </div>
          )}

          {/* User Email */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Institutional Email (FR-1 Verification)
            </label>
            <input
              type="text"
              value={activeTab === 'rider' ? riderId : driverId}
              onChange={(e) =>
                activeTab === 'rider' ? setRiderId(e.target.value) : setDriverId(e.target.value)
              }
              placeholder="user@vitstudent.ac.in or user@vit.ac.in"
              required
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono"
            />
            <span className="text-[10px] text-slate-500 mt-1 block">
              Allowed: @vitstudent.ac.in, @vit.ac.in, @campus.edu
            </span>
          </div>

          {/* Origin & Destination */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Pickup Origin (City Suburb)
              </label>
              <select
                value={originId}
                onChange={(e) => setOriginId(e.target.value)}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
              >
                <optgroup label="Chennai Residential Suburbs">
                  {suburbs.map((n) => (
                    <option key={n.id} value={n.id}>
                      {n.name}
                    </option>
                  ))}
                </optgroup>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Sole Campus Destination
              </label>
              <div className="w-full px-3 py-2 bg-slate-950/80 border border-emerald-500/40 rounded-xl text-xs text-emerald-300 font-semibold flex items-center justify-between">
                <span className="truncate">🎓 VIT Chennai</span>
                <span className="text-[9px] uppercase font-mono px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 shrink-0">
                  Default Drop
                </span>
              </div>
            </div>
          </div>

          {/* Specific Parameters */}
          {activeTab === 'rider' ? (
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="font-semibold text-slate-300">Max Permitted Detour Ratio</span>
                <span className="font-mono text-cyan-400">+{Math.round(maxDetourRatio * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.6"
                step="0.05"
                value={maxDetourRatio}
                onChange={(e) => setMaxDetourRatio(parseFloat(e.target.value))}
                className="w-full accent-blue-500"
              />
              <span className="text-[10px] text-slate-400">
                Guarantee: Rider transit time will never exceed {(1 + maxDetourRatio).toFixed(2)}x direct driving time.
              </span>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Available Seats
                </label>
                <select
                  value={capacity}
                  onChange={(e) => setCapacity(parseInt(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                >
                  <option value={2}>2 Passengers</option>
                  <option value={3}>3 Passengers (Standard)</option>
                  <option value={4}>4 Passengers (SUV/Van)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Max Driver Detour (min)
                </label>
                <input
                  type="number"
                  min="5"
                  max="35"
                  value={maxDriverDetourMin}
                  onChange={(e) => setMaxDriverDetourMin(parseInt(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white font-mono focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-white transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs rounded-xl shadow-lg shadow-blue-500/25 transition disabled:opacity-50"
            >
              {isSubmitting ? 'Registering...' : activeTab === 'rider' ? 'Submit Rider Request' : 'Submit Driver Offer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
