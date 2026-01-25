export interface Aircraft {
  icao24: string;
  callsign: string | null;
  origin_country: string;
  longitude: number;
  latitude: number;
  altitude: number | null;
  velocity: number | null;
  heading: number | null;
  on_ground: boolean;
  last_update: string;
}

export interface AircraftFeature {
  type: "Feature";
  geometry: {
    type: "Point";
    coordinates: [number, number];
  };
  properties: {
    icao24: string;
    callsign: string | null;
    origin_country: string;
    altitude: number | null;
    velocity: number | null;
    heading: number | null;
    on_ground: boolean;
    last_update: string;
  };
}

export interface AircraftResponse {
  type: "FeatureCollection";
  features: AircraftFeature[];
  count: number;
  timestamp: string;
}

export interface ViewState {
  longitude: number;
  latitude: number;
  zoom: number;
  pitch: number;
  bearing: number;
}

export interface HeatmapCell {
  h3_cell: string;
  count: number;
  avg_altitude: number | null;
  avg_velocity: number | null;
}

export interface Stats {
  total_aircraft: number;
  total_positions: number;
  active_last_hour: number;
  countries_covered: number;
  timestamp: string;
}