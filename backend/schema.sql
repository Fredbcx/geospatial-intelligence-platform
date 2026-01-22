CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Vessels table
CREATE TABLE vessels (
    id SERIAL PRIMARY KEY,
    mmsi VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255),
    vessel_type VARCHAR(100),
    flag_country VARCHAR(10),
    last_position GEOGRAPHY(POINT, 4326),
    last_update TIMESTAMP WITH TIME ZONE,
    speed_knots FLOAT,
    heading FLOAT,
    destination VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Spatial index (CRITICAL for performance!)
CREATE INDEX idx_vessels_position ON vessels USING GIST(last_position);
CREATE INDEX idx_vessels_last_update ON vessels(last_update);

-- Vessel position history
CREATE TABLE vessel_positions (
    id SERIAL PRIMARY KEY,
    vessel_id INTEGER REFERENCES vessels(id) ON DELETE CASCADE,
    position GEOGRAPHY(POINT, 4326) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    speed_knots FLOAT,
    heading FLOAT,
    h3_cell_id VARCHAR(20),  -- For spatial indexing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_vessel_positions_vessel ON vessel_positions(vessel_id);
CREATE INDEX idx_vessel_positions_position ON vessel_positions USING GIST(position);
CREATE INDEX idx_vessel_positions_timestamp ON vessel_positions(timestamp);
CREATE INDEX idx_vessel_positions_h3 ON vessel_positions(h3_cell_id);

-- Aircraft table
CREATE TABLE aircraft (
    id SERIAL PRIMARY KEY,
    icao24 VARCHAR(20) UNIQUE NOT NULL,
    callsign VARCHAR(50),
    aircraft_type VARCHAR(100),
    origin_country VARCHAR(100),
    last_position GEOGRAPHY(POINT, 4326),
    last_update TIMESTAMP WITH TIME ZONE,
    altitude_meters FLOAT,
    velocity_mps FLOAT,
    heading FLOAT,
    vertical_rate FLOAT,
    on_ground BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_aircraft_position ON aircraft USING GIST(last_position);
CREATE INDEX idx_aircraft_last_update ON aircraft(last_update);

-- Aircraft position history
CREATE TABLE aircraft_positions (
    id SERIAL PRIMARY KEY,
    aircraft_id INTEGER REFERENCES aircraft(id) ON DELETE CASCADE,
    position GEOGRAPHY(POINT, 4326) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    altitude_meters FLOAT,
    velocity_mps FLOAT,
    heading FLOAT,
    h3_cell_id VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_aircraft_positions_aircraft ON aircraft_positions(aircraft_id);
CREATE INDEX idx_aircraft_positions_position ON aircraft_positions USING GIST(position);
CREATE INDEX idx_aircraft_positions_timestamp ON aircraft_positions(timestamp);

-- Events table (GDELT, earthquakes, etc)
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    title VARCHAR(500),
    description TEXT,
    position GEOGRAPHY(POINT, 4326) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    severity VARCHAR(50),
    source VARCHAR(100),
    source_url TEXT,
    metadata JSONB,
    h3_cell_id VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_events_position ON events USING GIST(position);
CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_h3 ON events(h3_cell_id);

-- Test PostGIS functionality
SELECT ST_Distance(
    ST_Point(-73.9, 40.7)::geography,  -- NYC
    ST_Point(-74.0, 40.8)::geography   -- Nearby point
) as distance_meters;