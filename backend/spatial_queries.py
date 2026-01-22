"""
Advanced geospatial query functions using PostGIS
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, func
from geoalchemy2.functions import ST_AsGeoJSON, ST_MakeLine, ST_Transform
from geoalchemy2.elements import WKTElement
from datetime import datetime, timedelta, timezone  # AGGIUNTO timezone qui
from typing import List, Dict, Optional, Tuple
import json

from models import Aircraft, AircraftPosition, Vessel, Event

import logging
logger = logging.getLogger(__name__)

# ============= BOUNDING BOX QUERIES =============

def get_aircraft_in_viewport(
    db: Session,
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    limit: int = 1000
) -> List[Dict]:
    """
    Get all aircraft visible in map viewport
    Returns GeoJSON-like format for easy frontend rendering
    """
    bbox_wkt = f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, " \
               f"{max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
    
    aircraft_list = db.query(Aircraft).filter(
        func.ST_Intersects(
            Aircraft.last_position,
            func.ST_GeogFromText(bbox_wkt)
        ),
        Aircraft.last_update >= datetime.now(timezone.utc) - timedelta(minutes=30)
    ).limit(limit).all()
    
    result = []
    for aircraft in aircraft_list:
        if aircraft.last_position:
            geojson = db.scalar(ST_AsGeoJSON(aircraft.last_position))
            coords = json.loads(geojson)['coordinates']
            
            result.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": coords  # [lon, lat]
                },
                "properties": {
                    "icao24": aircraft.icao24,
                    "callsign": aircraft.callsign,
                    "origin_country": aircraft.origin_country,
                    "altitude": aircraft.altitude_meters,
                    "velocity": aircraft.velocity_mps,
                    "heading": aircraft.heading,
                    "on_ground": aircraft.on_ground,
                    "last_update": aircraft.last_update.isoformat() if aircraft.last_update else None
                }
            })
    
    return result

# ============= RADIUS QUERIES =============

def get_aircraft_near_point(
    db: Session,
    lon: float,
    lat: float,
    radius_km: float,
    limit: int = 100
) -> List[Dict]:
    """
    Find aircraft within radius of a point
    Returns aircraft with distance from center point
    """
    point_wkt = f"POINT({lon} {lat})"
    radius_meters = radius_km * 1000
    
    # Query with distance calculation 
    query = db.query(
        Aircraft,
        func.ST_Distance(
            Aircraft.last_position,
            func.ST_GeogFromText(point_wkt)
        ).label('distance_meters')
    ).filter(
        func.ST_DWithin(
            Aircraft.last_position,
            func.ST_GeogFromText(point_wkt),
            radius_meters
        ),
        Aircraft.last_update >= datetime.now(timezone.utc) - timedelta(minutes=30)
    ).order_by('distance_meters').limit(limit)
    
    result = []
    for aircraft, distance in query.all():
        if aircraft.last_position:
            geojson = db.scalar(ST_AsGeoJSON(aircraft.last_position))
            coords = json.loads(geojson)['coordinates']
            
            result.append({
                "icao24": aircraft.icao24,
                "callsign": aircraft.callsign,
                "coordinates": coords,
                "distance_km": round(distance / 1000, 2),
                "altitude": aircraft.altitude_meters,
                "velocity": aircraft.velocity_mps,
                "heading": aircraft.heading,
                "last_update": aircraft.last_update.isoformat() if aircraft.last_update else None
            })
    
    return result

# ============= TRAJECTORY QUERIES =============

def get_aircraft_trajectory(
    db: Session,
    icao24: str,
    hours_back: int = 24
) -> Dict:
    """
    Get aircraft movement trajectory for last N hours
    Returns GeoJSON LineString
    """
    start_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    
    aircraft = db.query(Aircraft).filter(Aircraft.icao24 == icao24).first()
    if not aircraft:
        return None
    
    positions = db.query(AircraftPosition).filter(
        AircraftPosition.aircraft_id == aircraft.id,
        AircraftPosition.timestamp >= start_time
    ).order_by(AircraftPosition.timestamp).all()
    
    if not positions:
        return None
    
    # Build GeoJSON LineString
    coordinates = []
    timestamps = []
    altitudes = []
    
    for pos in positions:
        geojson = db.scalar(ST_AsGeoJSON(pos.position))
        coords = json.loads(geojson)['coordinates']
        coordinates.append(coords)
        timestamps.append(pos.timestamp.isoformat())
        altitudes.append(pos.altitude_meters)
    
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": coordinates
        },
        "properties": {
            "icao24": icao24,
            "callsign": aircraft.callsign,
            "origin_country": aircraft.origin_country,
            "point_count": len(coordinates),
            "start_time": timestamps[0] if timestamps else None,
            "end_time": timestamps[-1] if timestamps else None,
            "timestamps": timestamps,
            "altitudes": altitudes
        }
    }

# ============= DENSITY ANALYSIS =============

def get_density_heatmap(
    db: Session,
    h3_resolution: int = 7,
    min_count: int = 5
) -> List[Dict]:
    """
    Get aircraft density by H3 hexagons
    Perfect for heatmap visualization
    """
    query = text("""
        SELECT 
            h3_cell_id,
            COUNT(*) as aircraft_count,
            AVG(altitude_meters) as avg_altitude,
            AVG(velocity_mps) as avg_velocity
        FROM aircraft_positions
        WHERE timestamp >= NOW() - INTERVAL '1 hour'
          AND h3_cell_id IS NOT NULL
        GROUP BY h3_cell_id
        HAVING COUNT(*) >= :min_count
        ORDER BY aircraft_count DESC
        LIMIT 1000
    """)
    
    result = db.execute(query, {"min_count": min_count})
    
    heatmap_data = []
    for row in result:
        heatmap_data.append({
            "h3_cell": row.h3_cell_id,
            "count": row.aircraft_count,
            "avg_altitude": round(row.avg_altitude, 2) if row.avg_altitude else None,
            "avg_velocity": round(row.avg_velocity, 2) if row.avg_velocity else None
        })
    
    return heatmap_data

# ============= STATISTICS =============

def get_spatial_stats(db: Session) -> Dict:
    """
    Get comprehensive spatial statistics
    """
    # Total counts
    total_aircraft = db.query(Aircraft).count()
    total_positions = db.query(AircraftPosition).count()
    
    # Recent activity (last hour)
    recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    recent_aircraft = db.query(Aircraft).filter(
        Aircraft.last_update >= recent_cutoff
    ).count()
    
    # Geographic coverage 
    coverage_query = text("""
        SELECT 
            COUNT(DISTINCT origin_country) as countries_covered,
            MIN(ST_Y(last_position::geometry)) as min_lat,
            MAX(ST_Y(last_position::geometry)) as max_lat,
            MIN(ST_X(last_position::geometry)) as min_lon,
            MAX(ST_X(last_position::geometry)) as max_lon
        FROM aircraft
        WHERE last_position IS NOT NULL
    """)
    
    coverage = db.execute(coverage_query).first()
    
    return {
        "total_aircraft": total_aircraft,
        "total_positions": total_positions,
        "active_last_hour": recent_aircraft,
        "countries_covered": coverage.countries_covered if coverage else 0,
        "geographic_bounds": {
            "min_lat": float(coverage.min_lat) if coverage and coverage.min_lat else None,
            "max_lat": float(coverage.max_lat) if coverage and coverage.max_lat else None,
            "min_lon": float(coverage.min_lon) if coverage and coverage.min_lon else None,
            "max_lon": float(coverage.max_lon) if coverage and coverage.max_lon else None
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ============= TOP N QUERIES =============

def get_busiest_routes(db: Session, limit: int = 10) -> List[Dict]:
    """
    Find most frequently flown routes (by callsign pattern)
    """
    query = text("""
        SELECT 
            SUBSTRING(callsign FROM 1 FOR 3) as airline_code,
            COUNT(DISTINCT icao24) as aircraft_count,
            COUNT(*) as total_flights,
            ARRAY_AGG(DISTINCT origin_country) as countries
        FROM aircraft
        WHERE callsign IS NOT NULL
          AND callsign != ''
          AND LENGTH(callsign) >= 3
        GROUP BY airline_code
        ORDER BY aircraft_count DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {"limit": limit})
    
    routes = []
    for row in result:
        routes.append({
            "airline_code": row.airline_code,
            "aircraft_count": row.aircraft_count,
            "total_flights": row.total_flights,
            "countries": row.countries
        })
    
    return routes