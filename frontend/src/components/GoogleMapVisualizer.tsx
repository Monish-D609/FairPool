import React, { useEffect, useRef, useState } from 'react'
import L from 'leaflet'
import type { LocationNode, NetworkEdge, Trip } from '../types'
import { ExternalLink, Compass, Layers, Move, Info, ChevronDown } from 'lucide-react'
import { getTripColor } from '../colors'

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
  onNodeMove?: (nodeId: string, lat: number, lng: number) => void
}

type GoogleLayerType = 'roadmap' | 'satellite' | 'terrain'

const GOOGLE_LAYERS: Record<GoogleLayerType, { url: string; subdomains: string[]; name: string }> = {
  roadmap: {
    url: 'https://mt{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    subdomains: ['0', '1', '2', '3'],
    name: 'Roadmap',
  },
  satellite: {
    url: 'https://mt{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    subdomains: ['0', '1', '2', '3'],
    name: 'Satellite',
  },
  terrain: {
    url: 'https://mt{s}.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
    subdomains: ['0', '1', '2', '3'],
    name: 'Terrain',
  },
}

export const GoogleMapVisualizer: React.FC<GoogleMapVisualizerProps> = ({
  nodes,
  edges,
  trips,
  selectedTripId,
  onSelectTrip,
  onSelectNodeAsOrigin,
  onSelectNodeAsDestination,
  onNodeMove,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const tileLayerRef = useRef<L.TileLayer | null>(null)
  const edgesLayerRef = useRef<L.LayerGroup | null>(null)
  const nodesLayerRef = useRef<L.LayerGroup | null>(null)
  const tripsLayerRef = useRef<L.LayerGroup | null>(null)

  const [activeLayer, setActiveLayer] = useState<GoogleLayerType>('roadmap')
  const [isLegendExpanded, setIsLegendExpanded] = useState(true)

  // Keep references to live polylines & markers for fluid dynamic dragging
  const markersMapRef = useRef<Map<string, L.Marker>>(new Map())
  const edgePolylinesRef = useRef<{ edge: NetworkEdge; poly: L.Polyline }[]>([])
  const tripPolylinesRef = useRef<
    {
      trip: Trip
      poly: L.Polyline
      casing?: L.Polyline
      glow?: L.Polyline
      vehicleMarker?: L.Marker
      stopBadges: { stop: any; marker: L.Marker }[]
    }[]
  >([])

  // Fast in-memory node lookup map
  const nodeMap = useRef<Map<string, LocationNode>>(new Map())
  useEffect(() => {
    nodeMap.current.clear()
    nodes.forEach((n) => nodeMap.current.set(n.id, { ...n }))
  }, [nodes])

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return

    // Center directly on VIT Chennai (Vandalur-Kelambakkam Road)
    const map = L.map(mapContainerRef.current, {
      center: [12.84085, 80.15393],
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
    edgePolylinesRef.current = []

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
          weight: 1.5,
          opacity: 0.45,
          dashArray: '3, 6',
        }
      )
      edgesLayerRef.current?.addLayer(poly)
      edgePolylinesRef.current.push({ edge, poly })
    })
  }, [nodes, edges])

  // Draw Dynamic Movable Nodes (Google Pins)
  useEffect(() => {
    if (!nodesLayerRef.current || nodes.length === 0) return

    // If marker count matches, just ensure coordinates match without recreating
    if (markersMapRef.current.size === nodes.length) {
      nodes.forEach((node) => {
        const marker = markersMapRef.current.get(node.id)
        if (marker) {
          const currentPos = marker.getLatLng()
          if (
            Math.abs(currentPos.lat - node.lat) > 0.00005 ||
            Math.abs(currentPos.lng - node.lng) > 0.00005
          ) {
            marker.setLatLng([node.lat, node.lng])
          }
        }
      })
      return
    }

    nodesLayerRef.current.clearLayers()
    markersMapRef.current.clear()

    nodes.forEach((node) => {
      const isHub = node.is_campus_hub
      const pinColor = isHub ? '#10B981' : '#EF4444'
      const iconHtml = `
        <div class="google-pin-wrapper ${isHub ? 'campus-hub-pin' : 'commuter-node-pin'}" title="Drag anywhere to reposition">
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

      // ALL PINS ARE DYNAMICALLY MOVABLE
      const marker = L.marker([node.lat, node.lng], {
        icon: customIcon,
        draggable: true,
      })

      // Dynamic Drag Handler: smoothly updates connected lines at 60 FPS
      marker.on('drag', () => {
        const newPos = marker.getLatLng()
        const n = nodeMap.current.get(node.id)
        if (n) {
          n.lat = newPos.lat
          n.lng = newPos.lng
        }

        // Live update road network edges connected to this pin
        edgePolylinesRef.current.forEach(({ edge, poly }) => {
          if (edge.from === node.id || edge.to === node.id) {
            const u = nodeMap.current.get(edge.from)
            const v = nodeMap.current.get(edge.to)
            if (u && v) {
              poly.setLatLngs([
                [u.lat, u.lng],
                [v.lat, v.lng],
              ])
            }
          }
        })

        // Live update carpool route polylines & stops passing through this pin
        tripPolylinesRef.current.forEach(({ trip, poly, casing, glow, vehicleMarker, stopBadges }) => {
          if (trip.stops.some((s) => s.location_id === node.id)) {
            const latLngs: [number, number][] = []
            trip.stops.forEach((s) => {
              const loc = nodeMap.current.get(s.location_id)
              if (loc) latLngs.push([loc.lat, loc.lng])
            })
            poly.setLatLngs(latLngs)
            casing?.setLatLngs(latLngs)
            glow?.setLatLngs(latLngs)
          }

          if (trip.stops[0]?.location_id === node.id && vehicleMarker) {
            vehicleMarker.setLatLng(newPos)
          }

          stopBadges.forEach(({ stop, marker: sMarker }) => {
            if (stop.location_id === node.id) {
              sMarker.setLatLng(newPos)
            }
          })
        })
      })

      // On Drag End: persist coordinates and notify parent
      marker.on('dragend', () => {
        const finalPos = marker.getLatLng()
        onNodeMove?.(node.id, finalPos.lat, finalPos.lng)
      })

      const popupContent = document.createElement('div')
      popupContent.className = 'google-popup-card'
      popupContent.innerHTML = `
        <div style="font-family: 'DM Sans', sans-serif; min-width: 170px; padding: 4px;">
          <div style="font-weight: 700; font-size: 13px; color: #0F172A; margin-bottom: 2px;">${node.name}</div>
          <div style="font-size: 11px; color: ${isHub ? '#059669' : '#64748B'}; font-weight: 600; margin-bottom: 6px;">
            ${isHub ? '🎓 Sole Campus Destination (VIT Chennai)' : '📍 Commuter Pickup (Movable)'}
          </div>
          <div style="font-size: 10px; color: #64748B; margin-bottom: 8px;">
            Drag pin to reposition anywhere
          </div>
          ${
            !isHub
              ? `<div style="display: flex; gap: 6px; margin-top: 4px;">
                  <button id="btn-orig-${node.id}" style="flex:1; padding: 4px 6px; background: #0284C7; color: white; border: none; border-radius: 4px; font-size: 10px; cursor: pointer; font-weight: 600;">
                    Pick as Origin
                  </button>
                </div>`
              : `<div style="padding: 4px 6px; background: #ECFDF5; color: #065F46; border-radius: 4px; font-size: 10px; font-weight: 700; text-align: center;">
                  Default & Only Drop Point
                </div>`
          }
        </div>
      `

      marker.bindPopup(popupContent)
      marker.on('popupopen', () => {
        const origBtn = document.getElementById(`btn-orig-${node.id}`)
        if (origBtn) {
          origBtn.onclick = () => {
            onSelectNodeAsOrigin?.(node)
            marker.closePopup()
          }
        }
      })

      nodesLayerRef.current?.addLayer(marker)
      markersMapRef.current.set(node.id, marker)
    })
  }, [nodes, onSelectNodeAsOrigin, onSelectNodeAsDestination, onNodeMove])

  // Draw Carpool Routes
  useEffect(() => {
    if (!tripsLayerRef.current || !mapRef.current) return
    tripsLayerRef.current.clearLayers()
    tripPolylinesRef.current = []

    trips.forEach((trip, idx) => {
      const isSelected = selectedTripId === trip.id
      const color = getTripColor(idx)

      // Extract coordinates from stops
      const latLngs: [number, number][] = []
      trip.stops.forEach((stop) => {
        const n = nodeMap.current.get(stop.location_id)
        if (n) latLngs.push([n.lat, n.lng])
      })

      if (latLngs.length < 2) return

      // Underlay / Casing: dark halo behind route for crisp contrast between overlapping routes
      const casingPoly = L.polyline(latLngs, {
        color: '#070C18',
        weight: isSelected ? 8.5 : 6,
        opacity: isSelected ? 0.95 : 0.75,
        lineCap: 'round',
        lineJoin: 'round',
      })
      tripsLayerRef.current?.addLayer(casingPoly)

      // Outer glow in the car's designated color if selected
      let glowPoly: L.Polyline | undefined
      if (isSelected) {
        glowPoly = L.polyline(latLngs, {
          color: color,
          weight: 14,
          opacity: 0.55,
          lineCap: 'round',
          lineJoin: 'round',
        })
        tripsLayerRef.current?.addLayer(glowPoly)
      }

      // Main route polyline in distinct car color
      const isAnyTripSelected = Boolean(selectedTripId)
      const line = L.polyline(latLngs, {
        color: color,
        weight: isSelected ? 5.5 : 4,
        opacity: isSelected ? 1.0 : isAnyTripSelected ? 0.45 : 0.95,
        lineCap: 'round',
        lineJoin: 'round',
      })

      line.on('click', () => {
        onSelectTrip(trip.id)
      })

      line.on('mouseover', () => {
        if (!isSelected) {
          line.setStyle({ weight: 5.5, opacity: 1.0 })
        }
      })

      line.on('mouseout', () => {
        if (!isSelected) {
          line.setStyle({
            weight: 4,
            opacity: selectedTripId ? 0.45 : 0.95,
          })
        }
      })

      const stopNames = trip.stops
        .map((s) => nodeMap.current.get(s.location_id)?.name.split(' ')[0] || s.location_id)
        .join(' → ')

      line.bindTooltip(
        `<div style="font-family: 'DM Sans', sans-serif; padding: 2px;">
          <div style="font-weight: 800; font-size: 12px; color: ${color}; margin-bottom: 2px; display: flex; align-items: center; gap: 4px;">
            <span>🚗</span> <span>Car #${idx + 1} (${trip.id})</span>
          </div>
          <div style="font-size: 11px; color: #F1F5F9; font-weight: 600;">
            Driver: ${trip.driver_id}
          </div>
          <div style="font-size: 10px; color: #94A3B8; margin-top: 2px;">
            👥 <b>${trip.request_ids.length}</b> commuters · ⚡ <b>${trip.saved_distance_km} km</b> saved
          </div>
          <div style="font-size: 10px; color: #CBD5E1; margin-top: 4px; border-top: 1px solid #334155; padding-top: 3px;">
            <b>Route:</b> ${stopNames}
          </div>
        </div>`,
        { sticky: true }
      )

      tripsLayerRef.current?.addLayer(line)

      // Car Vehicle Badge Marker at driver's origin
      const originNode = nodeMap.current.get(trip.stops[0]?.location_id)
      let vehicleMarker: L.Marker | undefined
      if (originNode) {
        const carHtml = `
          <div class="car-vehicle-badge" style="background: ${color}; box-shadow: 0 0 12px ${color}80;">
            <span class="car-badge-icon">🚗</span>
            <span class="car-badge-title">Car #${idx + 1}</span>
          </div>
        `
        const carIcon = L.divIcon({
          className: 'car-vehicle-div-icon',
          html: carHtml,
          iconSize: [64, 24],
          iconAnchor: [32, 28],
        })
        vehicleMarker = L.marker([originNode.lat, originNode.lng], {
          icon: carIcon,
          zIndexOffset: 1200 + (isSelected ? 500 : idx),
        })
        vehicleMarker.on('click', () => onSelectTrip(trip.id))
        vehicleMarker.bindTooltip(
          `<b>Car #${idx + 1}: ${trip.driver_id}</b><br/>👥 ${trip.request_ids.length} riders · ⚡ ${trip.saved_distance_km} km saved`,
          { direction: 'top' }
        )
        tripsLayerRef.current?.addLayer(vehicleMarker)
      }

      const stopBadges: { stop: any; marker: L.Marker }[] = []

      // Add Stop Badges along route
      if (isSelected || trips.length <= 4) {
        trip.stops.forEach((stop, sIdx) => {
          const n = nodeMap.current.get(stop.location_id)
          if (!n) return

          const isHub = n.is_campus_hub
          const stopHtml = `
            <div class="route-stop-badge" style="background: ${isHub ? '#10B981' : color};">
              ${isHub ? '🎓' : sIdx + 1}
            </div>
          `
          const stopIcon = L.divIcon({
            className: 'route-stop-icon',
            html: stopHtml,
            iconSize: [20, 20],
            iconAnchor: [10, 10],
          })
          const stopMarker = L.marker([n.lat, n.lng], { icon: stopIcon, zIndexOffset: 900 })
          stopMarker.bindTooltip(
            `<b>Stop ${sIdx + 1}: ${n.name}</b><br/>${stop.stop_type} · ${stop.estimated_arrival.toFixed(1)}m`
          )
          tripsLayerRef.current?.addLayer(stopMarker)
          stopBadges.push({ stop, marker: stopMarker })
        })
      }

      tripPolylinesRef.current.push({
        trip,
        poly: line,
        casing: casingPoly,
        glow: glowPoly,
        vehicleMarker,
        stopBadges,
      })
    })

    // If a trip is selected, fit bounds
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
          mapRef.current.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 })
        }
      }
    }
  }, [trips, selectedTripId, onSelectTrip])

  // Center directly on VIT Chennai
  const handleResetView = () => {
    mapRef.current?.setView([12.84085, 80.15393], 12)
    onSelectTrip(null)
  }

  // Open in Google Maps
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
    <div className="google-map-wrapper relative z-0 h-full w-full rounded-2xl overflow-hidden border border-slate-800 shadow-2xl bg-slate-950">
      {/* Top Floating Minimal Hint & Layers */}
      <div className="absolute top-3 left-3 right-3 z-20 flex items-center justify-between pointer-events-none gap-2">
        {/* Dynamic Move Hint */}
        <div className="pointer-events-auto flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/90 backdrop-blur-md border border-slate-700/80 text-xs text-slate-200 shadow-lg">
          <Move size={13} className="text-cyan-400 shrink-0" />
          <span className="hidden sm:inline font-medium">Pins are dynamically movable</span>
          <span className="sm:hidden font-medium">Drag pins</span>
          <span className="text-[10px] text-slate-400 font-mono hidden md:inline">
            · Routes recalculate live
          </span>
        </div>

        {/* Minimal Layer Switcher & Reset */}
        <div className="pointer-events-auto flex items-center gap-1 bg-slate-900/90 backdrop-blur-md p-1 rounded-xl border border-slate-700/80 shadow-lg">
          <Layers size={13} className="text-slate-400 ml-1.5 mr-0.5" />
          {(Object.keys(GOOGLE_LAYERS) as GoogleLayerType[]).map((layerKey) => (
            <button
              key={layerKey}
              onClick={() => setActiveLayer(layerKey)}
              className={`px-2 py-1 text-[11px] font-medium rounded-lg transition-all ${
                activeLayer === layerKey
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              {GOOGLE_LAYERS[layerKey].name}
            </button>
          ))}
          <button
            onClick={handleResetView}
            title="Recenter Map"
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition"
          >
            <Compass size={13} />
          </button>
        </div>
      </div>

      {/* Map DOM Element */}
      <div ref={mapContainerRef} className="h-full w-full min-h-[480px]" />

      {/* Bottom Floating Interactive Legend */}
      <div className="absolute bottom-3 left-3 z-20 pointer-events-auto bg-slate-900/95 backdrop-blur-md border border-slate-700/80 rounded-xl p-2.5 shadow-xl text-xs max-w-[310px]">
        {/* Header with collapse toggle */}
        <div
          className="flex items-center justify-between gap-3 cursor-pointer select-none"
          onClick={() => setIsLegendExpanded(!isLegendExpanded)}
        >
          <div className="flex items-center gap-1.5 font-bold text-white text-[11px] uppercase tracking-wider">
            <Info size={12} className="text-cyan-400" />
            <span>Map Legend & Route Key</span>
          </div>
          <button
            type="button"
            className="text-slate-400 hover:text-white p-0.5"
            aria-label="Toggle legend"
          >
            <ChevronDown
              size={13}
              className={`transition-transform duration-200 ${
                isLegendExpanded ? 'rotate-180' : ''
              }`}
            />
          </button>
        </div>

        {isLegendExpanded && (
          <div className="mt-2.5 space-y-2 border-t border-slate-800/80 pt-2 text-[11px]">
            {/* Network Lines & Route Meaning */}
            <div>
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">
                Route & Line Meanings
              </span>
              <div className="space-y-1.5 pl-0.5">
                <div className="flex items-center gap-2">
                  <svg width="22" height="6" className="shrink-0">
                    <line
                      x1="0"
                      y1="3"
                      x2="22"
                      y2="3"
                      stroke="#64748B"
                      strokeWidth="2"
                      strokeDasharray="3 3"
                    />
                  </svg>
                  <span className="text-slate-300">
                    <strong className="text-slate-200">Road Network:</strong> Arterial transit highway
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-0.5 shrink-0">
                    <span className="w-2.5 h-1 rounded-sm bg-cyan-400" />
                    <span className="w-2.5 h-1 rounded-sm bg-amber-400" />
                    <span className="w-2.5 h-1 rounded-sm bg-emerald-400" />
                  </div>
                  <span className="text-slate-300">
                    <strong className="text-white">Car Routes:</strong> Distinct color per vehicle
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <svg width="22" height="8" className="shrink-0">
                    <line
                      x1="0"
                      y1="4"
                      x2="22"
                      y2="4"
                      stroke="#38BDF8"
                      strokeWidth="6"
                      opacity="0.55"
                    />
                    <line
                      x1="0"
                      y1="4"
                      x2="22"
                      y2="4"
                      stroke="#FFFFFF"
                      strokeWidth="2.5"
                    />
                  </svg>
                  <span className="text-slate-300">
                    <strong className="text-cyan-300">Selected Route:</strong> Focused pool with matching glow
                  </span>
                </div>
              </div>
            </div>

            {/* Pins Key */}
            <div className="border-t border-slate-800/80 pt-1.5">
              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">
                Pin Types
              </span>
              <div className="grid grid-cols-2 gap-1.5 pl-0.5">
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block shrink-0"></span>
                  <span className="text-emerald-300 font-medium">🎓 VIT Chennai</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-400 inline-block shrink-0"></span>
                  <span className="text-slate-300">📍 Pickup (Movable)</span>
                </div>
              </div>
            </div>

            {/* Active Carpools Color Manifest */}
            {trips.length > 0 && (
              <div className="border-t border-slate-800/80 pt-1.5">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1">
                  Active Carpools ({trips.length})
                </span>
                <div className="max-h-24 overflow-y-auto space-y-1 custom-scrollbar pr-0.5">
                  {trips.map((trip, idx) => {
                    const c = getTripColor(idx)
                    const isSelected = selectedTripId === trip.id
                    return (
                      <button
                        key={trip.id}
                        type="button"
                        onClick={() => onSelectTrip(isSelected ? null : trip.id)}
                        className={`w-full flex items-center justify-between px-1.5 py-1 rounded text-[10px] transition text-left ${
                          isSelected
                            ? 'bg-slate-800 text-white font-bold ring-1 ring-cyan-400'
                            : 'hover:bg-slate-800/60 text-slate-300'
                        }`}
                      >
                        <div className="flex items-center gap-1.5 truncate">
                          <span
                            className="w-2.5 h-2.5 rounded-full shrink-0 shadow-sm"
                            style={{ backgroundColor: c }}
                          />
                          <span className="truncate">
                            <strong style={{ color: c }}>Car #{idx + 1}</strong> · {trip.driver_id.split('@')[0]}
                          </span>
                        </div>
                        <span className="text-[9px] font-mono text-slate-400 shrink-0 ml-1">
                          {trip.request_ids.length} riders
                        </span>
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            {trips.length > 0 && (
              <div className="border-t border-slate-800/80 pt-1.5 flex items-center justify-between">
                <span className="text-[10px] text-cyan-400 font-mono">
                  {trips.length} active pool(s)
                </span>
                <button
                  type="button"
                  onClick={handleOpenInGoogleMaps}
                  className="text-[10px] text-white hover:text-cyan-300 flex items-center gap-1 bg-blue-600/30 hover:bg-blue-600/50 px-2 py-0.5 rounded border border-blue-500/30 transition"
                >
                  <span>Google Maps</span>
                  <ExternalLink size={10} />
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
