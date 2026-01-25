export interface ViewState {
  longitude: number;
  latitude: number;
  zoom: number;
  pitch: number;
  bearing: number;
}

export interface AircraftProperties {
  icao24: string;
  callsign: string | null;
  origin_country: string;
  altitude: number | null;
  velocity: number | null;
  heading: number | null;
  vertical_rate: number | null;
  on_ground: boolean;
  last_update: string;
}

export interface AircraftFeature {
  type: 'Feature';
  properties: AircraftProperties;
  geometry: {
    type: 'Point';
    coordinates: [number, number, number]; // [lon, lat, altitude]
  };
}

export interface AircraftCollection {
  type: 'FeatureCollection';
  count: number;
  features: AircraftFeature[];
}

export interface HeatmapCell {
  h3_cell: string;
  count: number;
  avg_altitude: number | null;
  avg_velocity: number | null;
  min_lon: number;
  max_lon: number;
  min_lat: number;
  max_lat: number;
}

export interface HeatmapData {
  resolution: number;
  count: number;
  cells: HeatmapCell[];
}

export interface TrajectoryFeature {
  type: 'Feature';
  properties: {
    icao24: string;
    callsign: string | null;
    origin_country: string;
    count: number;
  };
  geometry: {
    type: 'LineString';
    coordinates: [number, number, number][]; // Array of [lon, lat, altitude]
  };
}

export interface Stats {
  total_aircraft: number;
  total_aircraft_positions: number;
  total_vessels: number;
  total_vessel_positions: number;
  total_events: number;
}