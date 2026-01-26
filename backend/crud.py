from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_Point, ST_Distance, ST_DWithin
from geoalchemy2.elements import WKTElement
import h3  
from datetime import datetime, timezone
from typing import List, Optional
from models import Aircraft, AircraftPosition, Vessel, VesselPosition, Event, Alert  
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from models import Alert 
from anomaly_detection import AnomalyDetector

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
    from geoalchemy2.shape import from_shape
    from shapely.geometry import Point
    
    lon, lat = data['longitude'], data['latitude']
    
    # Calculate H3 cell
    try:
        h3_cell = h3.latlng_to_cell(lat, lon, res=7)
    except AttributeError:
        h3_cell = h3.geo_to_h3(lat, lon, resolution=7)
    
    shapely_point = Point(lon, lat)  # Create Shapely Point
    geog_point = from_shape(shapely_point, srid=4326)  # Convert to Geography
    
    position = AircraftPosition(
        aircraft_id=aircraft_id,
        position=geog_point,  
        timestamp=data.get('timestamp', datetime.now(timezone.utc)),
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



def get_aircraft_by_icao24(db: Session, icao24: str):
    """Get aircraft by ICAO24 identifier"""
    return db.query(Aircraft).filter(Aircraft.icao24 == icao24).first()

def get_aircraft_positions_since(db: Session, aircraft_id: int, since: datetime, limit: int = 1000):
    """Get aircraft positions since specific time"""
    return (
        db.query(AircraftPosition)
        .filter(
            AircraftPosition.aircraft_id == aircraft_id,
            AircraftPosition.timestamp >= since
        )
        .order_by(AircraftPosition.timestamp.asc())
        .limit(limit)
        .all()
    )
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
    
    
# ============= ALERT CRUD OPERATIONS =============

def create_alert(db: Session, alert_data: dict):
    """Create new alert in database"""
    point = f"POINT({alert_data['longitude']} {alert_data['latitude']})"
    priority = calculate_alert_priority(alert_data)
    
    alert = Alert(
        alert_type=alert_data['type'],
        severity=alert_data['severity'],
        reason=alert_data['reason'],
        aircraft_icao24=alert_data['aircraft_icao24'],
        aircraft_callsign=alert_data['aircraft_callsign'],
        position=WKTElement(point, srid=4326),
        detected_at=datetime.now(timezone.utc),
        is_active=True,
        is_acknowledged=False,
        details=alert_data.get('details', {}),
        priority=priority
    )
    
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

def get_active_alerts(db: Session, limit: int = 100):
    """Get all active alerts"""
    return (
        db.query(Alert)
        .filter(Alert.is_active == True)
        .order_by(Alert.priority.desc(), Alert.detected_at.desc())
        .limit(limit)
        .all()
    )

def get_alerts_by_severity(db: Session, severity: str, limit: int = 100):
    """Get alerts by severity level"""
    return (
        db.query(Alert)
        .filter(Alert.severity == severity, Alert.is_active == True)
        .order_by(Alert.detected_at.desc())
        .limit(limit)
        .all()
    )

def get_alerts_for_aircraft(db: Session, icao24: str, limit: int = 50):
    """Get all alerts for specific aircraft"""
    return (
        db.query(Alert)
        .filter(Alert.aircraft_icao24 == icao24)
        .order_by(Alert.detected_at.desc())
        .limit(limit)
        .all()
    )

def acknowledge_alert(db: Session, alert_id: int):
    """Mark alert as acknowledged"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.is_acknowledged = True
        db.commit()
        db.refresh(alert)
    return alert

def resolve_alert(db: Session, alert_id: int):
    """Mark alert as resolved"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.is_active = False
        alert.resolved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(alert)
    return alert

def run_anomaly_detection_on_all_aircraft(db: Session):
    """
    Run anomaly detection on all aircraft and create alerts
    Includes intelligent deduplication to avoid duplicate alerts
    
    Returns:
        list[Alert]: List of newly created alerts (excludes updated existing ones)
    """
    # ============= STEP 1: Get all aircraft with positions =============
    aircraft = db.query(Aircraft).filter(Aircraft.last_position.isnot(None)).all()
    
    if not aircraft:
        return []
    
    # ============= STEP 2: Prepare data for detector =============
    aircraft_data = []
    for a in aircraft:
        if a.last_position:
            # Extract lat/lon from Geography field
            point = to_shape(a.last_position)
            
            aircraft_data.append({
                'icao24': a.icao24,
                'callsign': a.callsign,
                'latitude': point.y,   # point.y = latitude
                'longitude': point.x,  # point.x = longitude
                'altitude': a.altitude_meters if a.altitude_meters else 0,
                'velocity': a.velocity_mps if a.velocity_mps else 0,
                'vertical_rate': a.vertical_rate if hasattr(a, 'vertical_rate') else 0,
                'heading': a.heading if a.heading else 0
            })
    
    if not aircraft_data:
        return []
    
    # ============= STEP 3: Run anomaly detection =============
    detector = AnomalyDetector()
    detected_anomalies = detector.detect_all(aircraft_data)
    
    # ============= STEP 4: Create/update alerts with deduplication =============
    new_alerts = []
    updated_count = 0
    
    for anomaly in detected_anomalies:
        # CHECK if alert already exists (same aircraft + same type + still active)
        existing_alert = db.query(Alert).filter(
            Alert.aircraft_icao24 == anomaly['icao24'],
            Alert.alert_type == anomaly['type'],
            Alert.is_active == True,
            Alert.is_acknowledged == False
        ).first()
        
        if existing_alert:
            # UPDATE existing alert timestamp (anomaly still ongoing)
            existing_alert.detected_at = datetime.now(timezone.utc)
            # Optionally update position if aircraft moved
            existing_alert.position = f"POINT({anomaly['longitude']} {anomaly['latitude']})"
            updated_count += 1
        else:
            # CREATE new alert only if doesn't exist
            alert = Alert(
                alert_type=anomaly['type'],
                severity=anomaly['severity'],
                reason=anomaly['reason'],
                aircraft_icao24=anomaly['icao24'],
                aircraft_callsign=anomaly['callsign'],
                position=f"POINT({anomaly['longitude']} {anomaly['latitude']})",
                detected_at=datetime.now(timezone.utc),
                is_active=True,
                is_acknowledged=False,
                priority=anomaly['priority'],
                details=anomaly.get('details', {})
            )
            db.add(alert)
            new_alerts.append(alert)
    
    db.commit()
    
    # Log summary
    if new_alerts or updated_count > 0:
        print(f"   ✅ Created {len(new_alerts)} new alerts, updated {updated_count} existing")
    
    return new_alerts


# ============= Auto-resolve alerts =============

def auto_resolve_old_alerts(db: Session, max_age_minutes=30):
    """
    Automatically resolve alerts that haven't been updated in N minutes
    (means aircraft left restricted zone or anomaly stopped)
    
    Call this periodically or at the end of detection run
    """
    from datetime import timedelta
    
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
    
    old_alerts = db.query(Alert).filter(
        Alert.is_active == True,
        Alert.detected_at < cutoff_time
    ).all()
    
    for alert in old_alerts:
        alert.is_active = False
        alert.resolved_at = datetime.now(timezone.utc)
    
    db.commit()
    
    if old_alerts:
        print(f"   🔄 Auto-resolved {len(old_alerts)} old alerts")
    
    return len(old_alerts)

  
def get_alert_statistics(db: Session):
    """Get alert stats for dashboard"""
    return {
        'total_alerts': db.query(Alert).count(),
        'active_alerts': db.query(Alert).filter(Alert.is_active == True).count(),
        'by_severity': {
            'HIGH': db.query(Alert).filter(Alert.severity == 'HIGH', Alert.is_active == True).count(),
            'MEDIUM': db.query(Alert).filter(Alert.severity == 'MEDIUM', Alert.is_active == True).count(),
            'LOW': db.query(Alert).filter(Alert.severity == 'LOW', Alert.is_active == True).count()
        },
        'by_type': {
            'SPEED_ANOMALY': db.query(Alert).filter(Alert.alert_type == 'SPEED_ANOMALY', Alert.is_active == True).count(),
            'ALTITUDE_ANOMALY': db.query(Alert).filter(Alert.alert_type == 'ALTITUDE_ANOMALY', Alert.is_active == True).count(),
            'GEOFENCE_VIOLATION': db.query(Alert).filter(Alert.alert_type == 'GEOFENCE_VIOLATION', Alert.is_active == True).count(),
        }
    }