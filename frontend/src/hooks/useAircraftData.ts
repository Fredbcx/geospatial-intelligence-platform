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
      
      // DYNAMIC HEATMAP RESOLUTION BASED ON ZOOM LEVEL
      // This prevents giant blobs when zoomed out and too many tiny hexagons when zoomed in
      let h3Resolution: number;
      let minCount: number;
      
      if (viewState.zoom <= 4) {
        // World/Continent view: Large hexagons, high threshold
        h3Resolution = 5;  // ~252 km² hexagons
        minCount = 10;     // Only show very dense areas
      } else if (viewState.zoom <= 7) {
        // Country view: Medium hexagons, medium threshold
        h3Resolution = 6;  // ~36 km² hexagons
        minCount = 5;      // Show moderately dense areas
      } else if (viewState.zoom <= 10) {
        // Region view: Small hexagons, low threshold
        h3Resolution = 7;  // ~5 km² hexagons
        minCount = 3;      // Show less dense areas
      } else {
        // City view: Very small hexagons, minimal threshold
        h3Resolution = 8;  // ~0.7 km² hexagons
        minCount = 2;      // Show almost all activity
      }
      
      const [aircraft, heatmap] = await Promise.all([
        fetchAircraftInViewport(minLon, minLat, maxLon, maxLat, 1000),
        fetchDensityHeatmap(h3Resolution, minCount),
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