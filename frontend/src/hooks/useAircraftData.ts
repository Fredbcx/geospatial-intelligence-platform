import { useState, useCallback, useEffect } from 'react';
import type { AircraftFeature, HeatmapCell } from '../types';
import { fetchAircraftInViewport, fetchDensityHeatmap } from '../services/api';

interface UseAircraftDataProps {
  viewState: {
    longitude: number;
    latitude: number;
    zoom: number;
  };
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export function useAircraftData({
  viewState,
  autoRefresh = true,
  refreshInterval = 30000,
}: UseAircraftDataProps) {
  const [aircraftData, setAircraftData] = useState<AircraftFeature[]>([]);
  const [heatmapData, setHeatmapData] = useState<HeatmapCell[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAircraftData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const latRange = 180 / Math.pow(2, viewState.zoom);
      const lonRange = 360 / Math.pow(2, viewState.zoom);

      const minLon = viewState.longitude - lonRange;
      const maxLon = viewState.longitude + lonRange;
      const minLat = viewState.latitude - latRange;
      const maxLat = viewState.latitude + latRange;

      const [aircraft, heatmap] = await Promise.all([
        fetchAircraftInViewport(minLon, minLat, maxLon, maxLat, 1000),
        fetchDensityHeatmap(7, 1),
      ]);

      setAircraftData(aircraft.features);
      setHeatmapData(heatmap.cells);
    } catch (err) {
      console.error('Error loading data:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [viewState.longitude, viewState.latitude, viewState.zoom]);

  useEffect(() => {
    loadAircraftData();

    if (autoRefresh) {
      const interval = setInterval(loadAircraftData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [loadAircraftData, autoRefresh, refreshInterval]);

  return {
    aircraftData,
    heatmapData,
    loading,
    error,
    refresh: loadAircraftData,
  };
}