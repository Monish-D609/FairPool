export interface LocationNode {
  id: string
  name: string
  lat: number
  lng: number
  is_campus_hub: boolean
}

export interface NetworkEdge {
  from: string
  to: string
  distance_km: number
  speed_kmh: number
  travel_time_min: number
}

export interface NetworkData {
  city: string
  center: { lat: number; lng: number }
  nodes: LocationNode[]
  edges: NetworkEdge[]
}

export interface RiderRequest {
  id: string
  rider_id: string
  origin_id: string
  destination_id: string
  earliest_departure: number
  latest_arrival: number
  max_detour_ratio: number
  status: string
  direct_travel_time: number
  direct_distance_km: number
}

export interface DriverOffer {
  id: string
  driver_id: string
  origin_id: string
  destination_id: string
  departure_time: number
  capacity: number
  max_driver_detour_min: number
  cumulative_detour_min: number
  status: string
  direct_travel_time: number
  direct_distance_km: number
}

export interface RouteStop {
  location_id: string
  stop_type: 'DRIVER_ORIGIN' | 'PICKUP' | 'DROPOFF' | 'DRIVER_DESTINATION'
  rider_id?: string | null
  request_id?: string | null
  estimated_arrival: number
  occupancy_after_stop: number
}

export interface Trip {
  id: string
  offer_id: string
  driver_id: string
  request_ids: string[]
  stops: RouteStop[]
  total_travel_time: number
  total_distance_km: number
  solo_driver_distance_km: number
  saved_distance_km: number
  driver_detour_min: number
  rider_detours_min: Record<string, number>
  fairness_penalty: number
}

export interface BatchMatchResult {
  batch_id: string
  matched_trips: Trip[]
  unmatched_request_ids: string[]
  unused_offer_ids: string[]
  total_vkm_saved: number
  total_vkm_baseline_no_pool: number
  total_vkm_pooled: number
  match_rate_percent: number
  mean_driver_detour_min: number
  p90_driver_detour_min: number
  mean_rider_detour_min: number
  p90_rider_detour_min: number
  gini_driver_detour: number
  runtime_ms: number
  algorithm_name: string
}

export interface SystemState {
  num_requests: number
  num_offers: number
  requests: RiderRequest[]
  offers: DriverOffer[]
  latest_result: BatchMatchResult | null
  cohort_gini: number
  mean_cumulative_detour_min: number
  driver_cumulative_detours: Record<string, number>
  allowed_domains: string[]
}

export interface BenchmarkMetrics {
  algorithm_name: string
  match_rate_percent: number
  vkm_saved: number
  mean_driver_detour_min: number
  p90_driver_detour_min: number
  mean_rider_detour_min: number
  gini_driver_detour: number
  runtime_ms: number
  num_trips: number
}

export interface EpochResult {
  epoch: number
  gini_no_fairness: number
  gini_with_fairness: number
  vkm_saved_no_fairness: number
  vkm_saved_with_fairness: number
}

export interface BenchmarkResponse {
  single_batch: Record<string, BenchmarkMetrics>
  multi_epoch_study: EpochResult[]
  markdown_table: string
}
