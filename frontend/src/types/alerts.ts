// frontend/src/types/alerts.ts

export type AlertSeverity = 'HIGH' | 'MEDIUM' | 'LOW';
export type AlertType = 
  | 'SPEED_ANOMALY' 
  | 'ALTITUDE_ANOMALY' 
  | 'GEOFENCE_VIOLATION' 
  | 'VERTICAL_RATE_ANOMALY' 
  | 'ML_ANOMALY';

export interface Alert {
  id: number;
  alert_type: AlertType;
  severity: AlertSeverity;
  reason: string;
  aircraft_icao24: string;
  aircraft_callsign: string | null;
  position: {
    type: 'Point';
    coordinates: [number, number]; // [longitude, latitude]
  };
  detected_at: string; // ISO datetime
  is_active: boolean;
  is_acknowledged: boolean;
  acknowledged_at: string | null;
  resolved_at: string | null;
  priority: number;
  details: Record<string, any>;
}

export interface AlertStats {
  total: number;
  by_severity: {
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };
  by_type: Record<AlertType, number>;
  active_count: number;
  acknowledged_count: number;
  resolved_count: number;
}

export interface AlertFilters {
  severity?: AlertSeverity[];
  type?: AlertType[];
  active_only?: boolean;
}
