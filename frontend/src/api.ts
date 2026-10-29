import type {
  NetworkData,
  SystemState,
  BatchMatchResult,
  BenchmarkResponse,
} from './types'

const BASE_URL = ''

export async function fetchNetwork(): Promise<NetworkData> {
  const res = await fetch(`${BASE_URL}/api/network`)
  if (!res.ok) throw new Error(`Failed to fetch road network: ${res.statusText}`)
  return res.json()
}

export async function updateNodePosition(nodeId: string, lat: number, lng: number): Promise<void> {
  await fetch(`${BASE_URL}/api/nodes/${nodeId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lat, lng }),
  }).catch((err) => console.warn('Could not sync node position with backend:', err))
}

export async function fetchState(): Promise<SystemState> {
  const res = await fetch(`${BASE_URL}/api/state`)
  if (!res.ok) throw new Error(`Failed to fetch state: ${res.statusText}`)
  return res.json()
}

export async function submitRiderRequest(data: {
  rider_id: string
  origin_id: string
  destination_id: string
  earliest_departure: number
  latest_arrival: number
  max_detour_ratio?: number
}) {
  const res = await fetch(`${BASE_URL}/api/requests`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Failed to submit rider request')
  }
  return res.json()
}

export async function submitDriverOffer(data: {
  driver_id: string
  origin_id: string
  destination_id: string
  departure_time: number
  capacity?: number
  max_driver_detour_min?: number
}) {
  const res = await fetch(`${BASE_URL}/api/offers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Failed to submit driver offer')
  }
  return res.json()
}

export async function generateSampleBatch(opts: {
  num_requests?: number
  num_offers?: number
  direction?: 'INBOUND' | 'OUTBOUND'
  seed?: number
}) {
  const res = await fetch(`${BASE_URL}/api/generate-sample`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      num_requests: opts.num_requests ?? 30,
      num_offers: opts.num_offers ?? 12,
      direction: opts.direction ?? 'INBOUND',
      seed: opts.seed ?? Math.floor(Math.random() * 1000),
    }),
  })
  if (!res.ok) throw new Error(`Failed to generate commute batch: ${res.statusText}`)
  return res.json()
}

export async function runMatch(opts: {
  algorithm?: 'fairpool' | 'greedy' | 'no_pool'
  enable_fairness?: boolean
  use_exact_solver?: boolean
  fairness_weight?: number
}): Promise<BatchMatchResult> {
  const res = await fetch(`${BASE_URL}/api/match`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      algorithm: opts.algorithm ?? 'fairpool',
      enable_fairness: opts.enable_fairness ?? true,
      use_exact_solver: opts.use_exact_solver ?? false,
      fairness_weight: opts.fairness_weight ?? 0.45,
    }),
  })
  if (!res.ok) throw new Error(`Failed to execute match: ${res.statusText}`)
  return res.json()
}

export async function runBenchmark(opts: {
  num_requests?: number
  num_offers?: number
  direction?: 'INBOUND' | 'OUTBOUND'
  seed?: number
}): Promise<BenchmarkResponse> {
  const res = await fetch(`${BASE_URL}/api/benchmark`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      num_requests: opts.num_requests ?? 25,
      num_offers: opts.num_offers ?? 12,
      direction: opts.direction ?? 'INBOUND',
      seed: opts.seed ?? 42,
    }),
  })
  if (!res.ok) throw new Error(`Failed to run benchmark: ${res.statusText}`)
  return res.json()
}

export async function resetSystem() {
  const res = await fetch(`${BASE_URL}/api/reset`, { method: 'POST' })
  if (!res.ok) throw new Error(`Failed to reset system: ${res.statusText}`)
  return res.json()
}

export function getExportCsvUrl(): string {
  return `${BASE_URL}/api/export-csv`
}
