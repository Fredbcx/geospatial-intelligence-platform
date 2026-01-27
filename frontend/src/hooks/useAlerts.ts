import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import type { Alert, AlertStats, AlertFilters, AlertSeverity, AlertType } from '../types/alerts';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface UseAlertsReturn {
  alerts: Alert[];
  stats: AlertStats | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  acknowledgeAlert: (alertId: number) => Promise<void>;
  resolveAlert: (alertId: number) => Promise<void>;
  filters: AlertFilters;
  setFilters: (filters: AlertFilters) => void;
}

export const useAlerts = (autoRefresh: boolean = true, refreshInterval: number = 30000): UseAlertsReturn => {
  // initialize as empty array
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<AlertStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<AlertFilters>({
    active_only: true,
  });

  const fetchAlerts = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (filters.active_only !== undefined) {
        params.append('active_only', filters.active_only.toString());
      }
      if (filters.severity && filters.severity.length > 0) {
        params.append('severity', filters.severity.join(','));
      }
      if (filters.type && filters.type.length > 0) {
        params.append('type', filters.type.join(','));
      }

      const response = await axios.get(`${API_BASE_URL}/api/alerts?${params.toString()}`);
      
      console.log('📦 Raw API response type:', typeof response.data);
      console.log('📦 Is array?', Array.isArray(response.data));
      console.log('📦 Response sample:', JSON.stringify(response.data).substring(0, 200));
      
      // Handle all possible response formats
      let alertsData: Alert[] = [];
      
      if (Array.isArray(response.data)) {
        // Format 1: Direct array [...]
        alertsData = response.data;
        console.log('✅ Detected format: Direct array');
      } else if (response.data && typeof response.data === 'object') {
        // Format 2: Object wrapper 
        const possibleKeys = ['alerts', 'data', 'items', 'results'];
        
        for (const key of possibleKeys) {
          if (Array.isArray(response.data[key])) {
            alertsData = response.data[key];
            console.log(`✅ Detected format: {${key}: [...]}`);
            break;
          }
        }
        
        // If still no array found, scan all keys
        if (alertsData.length === 0) {
          const allKeys = Object.keys(response.data);
          console.log('📦 All available keys:', allKeys);
          
          for (const key of allKeys) {
            if (Array.isArray(response.data[key])) {
              alertsData = response.data[key];
              console.log(`✅ Found array in key: "${key}"`);
              break;
            }
          }
        }
      }
      
      // Final fallback - empty array
      if (!Array.isArray(alertsData)) {
        console.warn('⚠️ Could not parse alerts from response, using empty array');
        alertsData = [];
      }
      
      console.log('✅ Final alerts count:', alertsData.length);
      setAlerts(alertsData);
      
    } catch (err) {
      console.error('❌ Error fetching alerts:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch alerts');
      setAlerts([]); // always maintain array type
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  const fetchStats = useCallback(async () => {
    try {
      const response = await axios.get<AlertStats>(`${API_BASE_URL}/api/alerts/stats`);
      console.log('📊 Alert stats:', response.data);
      setStats(response.data);
    } catch (err) {
      console.error('❌ Error fetching alert stats:', err);
    }
  }, []);

  const acknowledgeAlert = useCallback(async (alertId: number) => {
    try {
      await axios.post(`${API_BASE_URL}/api/alerts/${alertId}/acknowledge`);
      await fetchAlerts();
      await fetchStats();
    } catch (err) {
      console.error('❌ Error acknowledging alert:', err);
      throw err;
    }
  }, [fetchAlerts, fetchStats]);

  const resolveAlert = useCallback(async (alertId: number) => {
    try {
      await axios.post(`${API_BASE_URL}/api/alerts/${alertId}/resolve`);
      await fetchAlerts();
      await fetchStats();
    } catch (err) {
      console.error('❌ Error resolving alert:', err);
      throw err;
    }
  }, [fetchAlerts, fetchStats]);

  // Initial fetch
  useEffect(() => {
    console.log('🔄 useAlerts: Initial fetch');
    fetchAlerts();
    fetchStats();
  }, [fetchAlerts, fetchStats]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    console.log(`🔄 useAlerts: Auto-refresh enabled (${refreshInterval / 1000}s)`);
    
    const interval = setInterval(() => {
      fetchAlerts();
      fetchStats();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchAlerts, fetchStats]);

  return {
    alerts,
    stats,
    isLoading,
    error,
    refetch: fetchAlerts,
    acknowledgeAlert,
    resolveAlert,
    filters,
    setFilters,
  };
};

// Helper function to get severity color
export const getSeverityColor = (severity: AlertSeverity): [number, number, number] => {
  switch (severity) {
    case 'HIGH':
      return [220, 38, 38]; // Red
    case 'MEDIUM':
      return [234, 179, 8]; // Yellow
    case 'LOW':
      return [34, 197, 94]; // Green
    default:
      return [156, 163, 175]; // Gray
  }
};

// Helper function to get alert type label
export const getAlertTypeLabel = (type: AlertType | undefined | null): string => {
  if (!type) return 'Unknown';
  if (typeof type !== 'string') return 'Invalid Type';
  
  if (!type.includes('_')) return type;
  
  return type
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
};

// Helper function to format timestamp
export const formatAlertTime = (timestamp: string): string => {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  } catch (err) {
    return 'Unknown time';
  }
};