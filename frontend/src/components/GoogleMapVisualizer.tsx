import React, { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import type { LocationNode, NetworkEdge, Trip } from '../types'
import { ExternalLink, Compass } from 'lucide-react'

// Fix default Leaflet icon paths
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

interface GoogleMapVisualizerProps {
  nodes: LocationNode[]
  edges: NetworkEdge[]
  trips: Trip[]
  selectedTripId: string | null
  onSelectTrip: (tripId: string | null) => void
  onSelectNodeAsOrigin?: (node: LocationNode) => void
  onSelectNodeAsDestination?: (node: LocationNode) => void
}

type GoogleLayerType = 'roadmap' | 'satellite' | 'terrain' | 'traffic'

const GOOGLE_LAYERS: Record<GoogleLayerType, { url: string; subdomains: string[]; name: string }> = {
  roadmap: {
    url: 'https://mt{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    subdomains: ['0', '1', '2', '3'],
    name: 'Roadmap',
  },
  satellite: {
    url: 'https://mt{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    subdomains: ['0', '1', '2', '3'],
    name: 'Satellite Hybrid',
  },
  terrain: {
    url: 'https://mt{s}.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
    subdomains: ['0', '1', '2', '3'],
    name: 'Terrain',
  },
  traffic: {
    url: 'https://mt{s}.google.com/vt/lyrs=m,traffic&x={x}&y={y}&z={z}',
    subdomains: ['0', '1', '2', '3'],
    name: 'Live Traffic',
  },
}

// Distinct vibrant route colors
const ROUTE_PALETTE = [
  '#06B6D4', // Cyan
  '#10B981', // Emerald
  '#F59E0B', // Amber
  '#EC4899', // Pink
  '#8B5CF6', // Purple
  '#3B82F6', // Blue
  '#14B8A6', // Teal
  '#F97316', // Orange
]

export const GoogleMapVisualizer: React.FC<GoogleMapVisualizerProps> = ({
  nodes,
  edges,
  trips,
  selectedTripId,
  onSelectTrip,
  onSelectNodeAsOrigin,
  onSelectNodeAsDestination,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const tileLayerRef = useRef<L.TileLayer | null>(null)
  const edgesLayerRef = useRef<L.LayerGroup | null>(null)
  const nodesLayerRef = useRef<L.LayerGroup | null>(null)
  const tripsLayerRef = useRef<L.LayerGroup | null>(null)

  const [activeLayer, setActiveLayer] = useState<GoogleLayerType>('roadmap')

  // Node lookup map
  const nodeMap = useRef<Map<string, LocationNode>>(new Map())
  useEffect(() => {
    nodeMap.current.clear()
    nodes.forEach((n) => nodeMap.current.set(n.id, n))
  }, [nodes])

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return

    // Center on Chennai (Adyar / Guindy / IIT Madras corridor)
    const map = L.map(mapContainerRef.current, {
      center: [12.9915, 80.2337],
      zoom: 12,
      zoomControl: false,
    })

    L.control.zoom({ position: 'bottomright' }).addTo(map)

    const initialCfg = GOOGLE_LAYERS.roadmap
    const tileLayer = L.tileLayer(initialCfg.url, {
      subdomains: initialCfg.subdomains,
      maxZoom: 20,
      attribution: '&copy; Google Maps',
    }).addTo(map)

    tileLayerRef.current = tileLayer
    edgesLayerRef.current = L.layerGroup().addTo(map)
    nodesLayerRef.current = L.layerGroup().addTo(map)
    tripsLayerRef.current = L.layerGroup().addTo(map)
    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Switch Tile Layer
  useEffect(() => {
    if (!mapRef.current) return
    const cfg = GOOGLE_LAYERS[activeLayer]
    if (tileLayerRef.current) {
      mapRef.current.removeLayer(tileLayerRef.current)
    }
    tileLayerRef.current = L.tileLayer(cfg.url, {
      subdomains: cfg.subdomains,
      maxZoom: 20,
      attribution: '&copy; Google Maps',
    }).addTo(mapRef.current)
    tileLayerRef.current.bringToBack()
  }, [activeLayer])

  // Draw Network Edges
  useEffect(() => {
    if (!edgesLayerRef.current || nodes.length === 0) return
    edgesLayerRef.current.clearLayers()

    edges.forEach((edge) => {
      const u = nodeMap.current.get(edge.from)
      const v = nodeMap.current.get(edge.to)
      if (!u || !v) return

      const poly = L.polyline(
        [
          [u.lat, u.lng],
          [v.lat, v.lng],
        ],
        {
          color: '#334155',
          weight: 2,
          opacity: 0.6,
          dashArray: '4, 6',
        }
      )
      edgesLayerRef.current?.addLayer(poly)
    })
  }, [nodes, edges])

  // Draw Nodes (Google Pins)
  useEffect(() => {
    if (!nodesLayerRef.current || nodes.length === 0) return
    nodesLayerRef.current.clearLayers()

    nodes.forEach((node) => {
      const isHub = node.is_campus_hub
      const pinColor = isHub ? '#10B981' : '#EF4444'
      const iconHtml = `
        <div class="google-pin-wrapper ${isHub ? 'campus-hub-pin' : 'commuter-node-pin'}">
          <div class="google-pin-head" style="background: ${pinColor};">
            <span class="pin-symbol">${isHub ? '🎓' : '📍'}</span>
          </div>
          <div class="google-pin-tip" style="border-top-color: ${pinColor};"></div>
          <div class="google-pin-label">${node.name.split(' ')[0]}</div>
        </div>
      `

      const customIcon = L.divIcon({
        className: 'google-map-marker',
        html: iconHtml,
        iconSize: [32, 42],
        iconAnchor: [16, 38],
      })

      const marker = L.marker([node.lat, node.lng], { icon: customIcon })

      const popupContent = document.createElement('div')
      popupContent.className = 'google-popup-card'
      popupContent.innerHTML = `
        <div style="font-family: 'DM Sans', sans-serif; min-width: 180px; padding: 4px;">
          <div style="font-weight: 700; font-size: 14px; color: #0F172A; margin-bottom: 2px;">${node.name}</div>
          <div style="font-size: 11px; color: ${isHub ? '#059669' : '#64748B'}; font-weight: 600; margin-bottom: 8px;">
            ${isHub ? '⭐ Central Campus / Workplace Hub' : '🏙️ Suburban Commuter Cluster'}
          </div>
          <div style="font-size: 11px; color: #475569; margin-bottom: 8px;">
            GPS: <code>${node.lat.toFixed(4)}, ${node.lng.toFixed(4)}</code>
          </div>
          <div style="display: flex; gap: 6px; margin-top: 6px;">
            <button id="btn-orig-${node.id}" style="flex:1; padding: 4px 8px; background: #0284C7; color: white; border: none; border-radius: 4px; font-size: 10px; cursor: pointer; font-weight: 600;">
              Pick as Origin
            </button>
            <button id="btn-dest-${node.id}" style="flex:1; padding: 4px 8px; background: #059669; color: white; border: none; border-radius: 4px; font-size: 10px; cursor: pointer; font-weight: 600;">
              Pick as Dest
            </button>
          </div>
        </div>
      `

      marker.bindPopup(popupContent)
      marker.on('popupopen', () => {
        const origBtn = document.getElementById(`btn-orig-${node.id}`)
        const destBtn = document.getElementById(`btn-dest-${node.id}`)
        if (origBtn) {
          origBtn.onclick = () => {
            onSelectNodeAsOrigin?.(node)
            marker.closePopup()
          }
        }
        if (destBtn) {
          destBtn.onclick = () => {
            onSelectNodeAsDestination?.(node)
            marker.closePopup()
          }
        }
      })

      nodesLayerRef.current?.addLayer(marker)
    })
  }, [nodes, onSelectNodeAsOrigin, onSelectNodeAsDestination])

  // Draw Carpool Routes
  useEffect(() => {
    if (!tripsLayerRef.current || !mapRef.current) return
    tripsLayerRef.current.clearLayers()

    trips.forEach((trip, idx) => {
      const isSelected = selectedTripId === trip.id
      const color = ROUTE_PALETTE[idx % ROUTE_PALETTE.length]

      // Extract coordinates from stops
      const latLngs: [number, number][] = []
      trip.stops.forEach((stop) => {
        const n = nodeMap.current.get(stop.location_id)
        if (n) latLngs.push([n.lat, n.lng])
      })

      if (latLngs.length < 2) return

      // Outer glow if selected
      if (isSelected) {
        const glow = L.polyline(latLngs, {
          color: '#38BDF8',
          weight: 10,
          opacity: 0.5,
          lineCap: 'round',
          lineJoin: 'round',
        })
        tripsLayerRef.current?.addLayer(glow)
      }

      // Main route polyline
      const line = L.polyline(latLngs, {
        color: color,
        weight: isSelected ? 6 : 4,
        opacity: isSelected ? 1.0 : 0.85,
        dashArray: isSelected ? undefined : '8, 6',
      })

      line.on('click', () => {
        onSelectTrip(trip.id)
      })

      line.bindTooltip(
        `<b>Trip ${trip.id}</b> (${trip.driver_id})<br/>👥 ${trip.request_ids.length} riders | ⚡ ${trip.saved_distance_km} km saved`,
        { sticky: true }
      )

      tripsLayerRef.current?.addLayer(line)

      // Add Stop Markers along route if selected or few trips
      if (isSelected || trips.length <= 4) {
        trip.stops.forEach((stop, sIdx) => {
          const n = nodeMap.current.get(stop.location_id)
          if (!n) return

          const stopHtml = `
            <div class="route-stop-badge" style="background: ${color};">
              ${sIdx + 1}
            </div>
          `
          const stopIcon = L.divIcon({
            className: 'route-stop-icon',
            html: stopHtml,
            iconSize: [20, 20],
            iconAnchor: [10, 10],
          })
          const stopMarker = L.marker([n.lat, n.lng], { icon: stopIcon })
          stopMarker.bindTooltip(
            `<b>Stop ${sIdx + 1}: ${n.name}</b><br/>Type: ${stop.stop_type}<br/>ETA: ${stop.estimated_arrival.toFixed(1)}m | Occ: ${stop.occupancy_after_stop}`
          )
          tripsLayerRef.current?.addLayer(stopMarker)
        })
      }
    })

    // If a trip is selected, zoom to fit its bounds
    if (selectedTripId) {
      const activeTrip = trips.find((t) => t.id === selectedTripId)
      if (activeTrip) {
        const pts: [number, number][] = activeTrip.stops
          .map((s) => {
            const n = nodeMap.current.get(s.location_id)
            return n ? ([n.lat, n.lng] as [number, number]) : null
          })
          .filter((p): p is [number, number] => p !== null)

        if (pts.length >= 2) {
          const bounds = L.latLngBounds(pts)
          mapRef.current.fitBounds(bounds, { padding: [60, 60], maxZoom: 14 })
        }
      }
    }
  }, [trips, selectedTripId, onSelectTrip])

  // Center on Chennai Hub
  const handleResetView = () => {
    mapRef.current?.setView([12.9915, 80.2337], 12)
    onSelectTrip(null)
  }

  // Open Selected Trip in Google Maps Navigation
  const handleOpenInGoogleMaps = () => {
    const trip = trips.find((t) => t.id === selectedTripId) || trips[0]
    if (!trip || trip.stops.length < 2) return

    const stopCoords = trip.stops
      .map((s) => nodeMap.current.get(s.location_id))
      .filter((n): n is LocationNode => !!n)

    if (stopCoords.length < 2) return

    const origin = `${stopCoords[0].lat},${stopCoords[0].lng}`
    const dest = `${stopCoords[stopCoords.length - 1].lat},${stopCoords[stopCoords.length - 1].lng}`
    const waypoints = stopCoords
      .slice(1, -1)
      .map((w) => `${w.lat},${w.lng}`)
      .join('|')

    const gmapsUrl = `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${dest}${
      waypoints ? `&waypoints=${waypoints}` : ''
    }&travelmode=driving`

    window.open(gmapsUrl, '_blank')
  }

  return (
    <div className="google-map-wrapper relative z-0 isolate h-full w-full rounded-2xl overflow-hidden border border-slate-700/60 shadow-2xl bg-slate-900">
      {/* Top Floating Controls */}
      <div className="map-floating-header">
        <div className="flex items-center gap-2">
          <div className="google-brand-badge">
            <span className="google-g-logo">G</span>
            <span>Google Maps Engine</span>
          </div>
          <span className="text-xs text-slate-400 font-mono hidden md:inline">
            Chennai Metropolitan Commuter Corridor (13.0°N, 80.2°E)
          </span>
        </div>

        {/* Layer Selector */}
        <div className="flex items-center gap-1.5 bg-slate-900/90 backdrop-blur-md p-1 rounded-xl border border-slate-700">
          {(Object.keys(GOOGLE_LAYERS) as GoogleLayerType[]).map((layerKey) => (
            <button
              key={layerKey}
              onClick={() => setActiveLayer(layerKey)}
              className={`px-2.5 py-1 text-xs font-medium rounded-lg transition-all ${
                activeLayer === layerKey
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/30'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              {GOOGLE_LAYERS[layerKey].name}
            </button>
          ))}

          <button
            onClick={handleResetView}
            title="Recenter Map on IIT Madras / Anna Univ Hub"
            className="p-1.5 ml-1 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition"
          >
            <Compass size={14} />
          </button>
        </div>
      </div>

      {/* Map Container */}
      <div ref={mapContainerRef} className="h-full w-full min-h-[460px]" />

      {/* Bottom Floating Info / Action Bar */}
      <div className="map-floating-footer">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block"></span>
            <span>Destination Campus Hubs (3)</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-slate-300">
            <span className="w-2.5 h-2.5 rounded-full bg-red-400 inline-block"></span>
            <span>City Suburbs (16)</span>
          </div>
          {trips.length > 0 && (
            <div className="flex items-center gap-1.5 text-xs text-cyan-300">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse inline-block"></span>
              <span>{trips.length} Dispatched Pools</span>
            </div>
          )}
        </div>

        {trips.length > 0 && (
          <button
            onClick={handleOpenInGoogleMaps}
            className="flex items-center gap-1.5 px-3 py-1 bg-white/10 hover:bg-white/20 text-white text-xs font-medium rounded-lg border border-white/20 transition backdrop-blur-sm"
            title="Open turn-by-turn route directly in Google Maps"
          >
            <ExternalLink size={12} />
            <span>Open in Google Maps Live</span>
          </button>
        )}
      </div>
    </div>
  )
}
