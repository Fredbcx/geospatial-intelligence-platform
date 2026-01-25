import axios from 'axios';
import type {
  AircraftCollection,
  HeatmapData,
  TrajectoryFeature,
  Stats,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================
// AIRCRAFT ENDPOINTS
// ============================================================

export async function fetchAircraftInViewport(
  minLon: number,
  minLat: number,
  maxLon: number,
  maxLat: number,
  limit: number = 1000
): Promise<AircraftCollection> {
  const response = await apiClient.get<AircraftCollection>('/aircraft/viewport', {
    params: { min_lon: minLon, min_lat: minLat, max_lon: maxLon, max_lat: maxLat, limit },
  });
  return response.data;
}

export async function fetchAircraftNear(
  lon: number,
  lat: number,
  radiusKm: number,
  limit: number = 100
) {
  const response = await apiClient.get('/aircraft/near', {
    params: { lon, lat, radius_km: radiusKm, limit },
  });
  return response.data;
}

export async function fetchAircraftTrajectory(
  icao24: string,
  hours: number = 1
): Promise<TrajectoryFeature> {
  const response = await apiClient.get<TrajectoryFeature>(
    `/aircraft/${icao24}/trajectory`,
    { params: { hours } }
  );
  return response.data;
}

// ============================================================
// HEATMAP ENDPOINTS
// ============================================================

export async function fetchDensityHeatmap(
  resolution: number = 7,
  minCount: number = 1
): Promise<HeatmapData> {
  const response = await apiClient.get<HeatmapData>('/heatmap/density', {
    params: { resolution, min_count: minCount },
  });
  return response.data;
}

// ============================================================
// STATS ENDPOINTS
// ============================================================

export async function fetchStats(): Promise<Stats> {
  const response = await apiClient.get<Stats>('/stats/spatial');
  return response.data;
}

// ============================================================
// SCHEDULER ENDPOINTS
// ============================================================

export async function triggerDataFetch() {
  const response = await apiClient.post('/scheduler/trigger');
  return response.data;
}

// ============================================================
// DEFAULT EXPORT
// ============================================================

export default apiClient;