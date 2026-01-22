from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_Point, ST_Distance, ST_DWithin
from geoalchemy2.elements import WKTElement
import h3
from datetime import datetime
from typing import List, Optional
from models import Aircraft, AircraftPosition, Vessel, VesselPosition, Event

# ============= AIRCRAFT OPERATIONS =============

def get_or_create_aircraft(db: Session, icao24: str, data: dict) -> Aircraft:
    """
    Get existing aircraft or create new one
    Updates last_position if aircraft exists
    """
    aircraft = db.query(Aircraft).filter(Aircraft.icao24 == icao24).first()
    
    if aircraft:
        # Update existing aircraft
        aircraft.callsign = data.get('callsign')
        aircraft.origin_country = data.get('origin_country')
        aircraft.last_update = data.get('last_update')
        aircraft.altitude_meters = data.get('altitude')
        aircraft.velocity_mps = data.get('velocity')
        aircraft.heading = data.get('heading')
        aircraft.on_ground = data.get('on_ground')
        
        # Update position using PostGIS
        if data.get('longitude') and data.get('latitude'):
            point = f"POINT({data['longitude']} {data['latitude']})"
            aircraft.last_position = WKTElement(point, srid=4326)
    else:
        # Create new aircraft
        point = f"POINT({data['longitude']} {data['latitude']})"
        aircraft = Aircraft(
            icao24=icao24,
            callsign=data.get('callsign'),
            origin_country=data.get('origin_country'),
            last_position=WKTElement(point, srid=4326),
            last_update=data.get('last_update'),
            altitude_meters=data.get('altitude'),
            velocity_mps=data.get('velocity'),
            heading=data.get('heading'),
            on_ground=data.get('on_ground')
        )
        db.add(aircraft)
    
    db.commit()
    db.refresh(aircraft)
    return aircraft

def create_aircraft_position(db: Session, aircraft_id: int, data: dict) -> AircraftPosition:
    """
    Record aircraft position in history
    Calculates H3 cell ID for spatial indexing
    """
    lon, lat = data['longitude'], data['latitude']
    
    # Calculate H3 cell (resolution 7 ≈ 5km hexagons)
    h3_cell = h3.geo_to_h3(lat, lon, resolution=7)
    
    point = f"POINT({lon} {lat})"
    position = AircraftPosition(
        aircraft_id=aircraft_id,
        position=WKTElement(point, srid=4326),
        timestamp=data.get('timestamp', datetime.utcnow()),
        altitude_meters=data.get('altitude'),
        velocity_mps=data.get('velocity'),
        heading=data.get('heading'),
        h3_cell_id=h3_cell
    )
    
    db.add(position)
    db.commit()
    db.refresh(position)
    return position

def get_aircraft_in_bbox(db: Session, min_lon: float, min_lat: float, 
                         max_lon: float, max_lat: float, limit: int = 1000) -> List[Aircraft]:
    """
    Get all aircraft within bounding box
    Uses PostGIS spatial query
    """
    # Create bounding box polygon
    bbox = f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, " \
           f"{max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
    
    aircraft = db.query(Aircraft).filter(
        Aircraft.last_position.ST_Within(WKTElement(bbox, srid=4326))
    ).limit(limit).all()
    
    return aircraft

def get_aircraft_near_point(db: Session, lon: float, lat: float, 
                            radius_km: float, limit: int = 100) -> List[Aircraft]:
    """
    Get aircraft within radius of a point
    radius_km: search radius in kilometers
    """
    point = WKTElement(f"POINT({lon} {lat})", srid=4326)
    radius_meters = radius_km * 1000
    
    aircraft = db.query(Aircraft).filter(
        ST_DWithin(Aircraft.last_position, point, radius_meters)
    ).limit(limit).all()
    
    return aircraft

def get_aircraft_trajectory(db: Session, aircraft_id: int, 
                           start_time: datetime, end_time: datetime) -> List[AircraftPosition]:
    """Get aircraft position history for time range"""
    positions = db.query(AircraftPosition).filter(
        AircraftPosition.aircraft_id == aircraft_id,
        AircraftPosition.timestamp >= start_time,
        AircraftPosition.timestamp <= end_time
    ).order_by(AircraftPosition.timestamp).all()
    
    return positions

# ============= UTILITY FUNCTIONS =============

def get_stats(db: Session) -> dict:
    """Get platform statistics"""
    total_aircraft = db.query(Aircraft).count()
    total_vessels = db.query(Vessel).count()
    total_events = db.query(Event).count()
    total_aircraft_positions = db.query(AircraftPosition).count()
    
    return {
        "total_aircraft": total_aircraft,
        "total_vessels": total_vessels,
        "total_events": total_events,
        "total_aircraft_positions": total_aircraft_positions
    }