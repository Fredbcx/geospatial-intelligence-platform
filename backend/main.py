from database import get_db, SessionLocal 
import crud
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
import requests
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager 
from apscheduler.schedulers.asyncio import AsyncIOScheduler  
from scheduler import start_scheduler, stop_scheduler, get_scheduler_status, trigger_job_now
from spatial_queries import (
    get_aircraft_in_viewport,
    get_aircraft_near_point,
    get_density_heatmap,
    get_spatial_stats,
    get_busiest_routes
)
import logging
from geoalchemy2.shape import to_shape
from models import Alert
from fastapi.middleware.cors import CORSMiddleware


logger = logging.getLogger(__name__)

load_dotenv()

# ============= CREATE SCHEDULER (BEFORE FastAPI app) =============
scheduler = AsyncIOScheduler()  

# ============= BACKGROUND JOBS =============

def run_periodic_anomaly_detection():
    """Run anomaly detection every 5 minutes"""
    db = SessionLocal()  
    try:
        logger.info("🔍 Running anomaly detection...")
        new_alerts = crud.run_anomaly_detection_on_all_aircraft(db)
        
        if new_alerts:
            logger.warning(f"⚠️  Detected {len(new_alerts)} new anomalies!")
            for alert in new_alerts[:5]:
                logger.warning(f"   [{alert.severity}] {alert.alert_type}: {alert.reason}")
        else:
            logger.info("✅ No anomalies detected")
    except Exception as e:
        logger.error(f"❌ Error in anomaly detection: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

# ============= LIFESPAN CONTEXT MANAGER =============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown"""
    
    # STARTUP
    print("=" * 50)
    print("🚀 STARTUP EVENT TRIGGERED")
    print("=" * 50)
    
    try:
        print("📦 Attempting to import database modules...")
        from database import test_connection, init_db
        print("✅ Database modules imported successfully")
        
        print("🔄 Testing database connection...")
        
        if test_connection():
            print("✅ Database connection successful!")
            print("🔄 Initializing database tables...")
            init_db()
            print("✅ Database initialized successfully")
            
            # START ANOMALY DETECTION SCHEDULER
            print("🔄 Starting anomaly detection scheduler...")
            scheduler.start()
            print("✅ Scheduler started")
            
            scheduler.add_job(
                run_periodic_anomaly_detection,
                'interval',
                minutes=5,
                id='anomaly_detection'
            )
            print("✅ Anomaly detection scheduled (every 5 minutes)")
            
        else:
            print("⚠️  Database connection failed - running in API-only mode")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("⚠️  Running in API-only mode")
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        import traceback
        traceback.print_exc()
        print("⚠️  Running in API-only mode")
    
    print("=" * 50)
    
    yield  # Application runs here
    
    # SHUTDOWN
    print("🛑 Shutting down...")
    scheduler.shutdown()
    stop_scheduler()  
    print("✅ Shutdown complete")

# ============= CREATE FASTAPI APP =============

app = FastAPI(
    title="Geospatial Intelligence Platform API",
    description="Real-time tracking and analysis of global assets",
    version="0.2.0",
    lifespan=lifespan  
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class AircraftPosition(BaseModel):
    icao24: str
    callsign: Optional[str]
    origin_country: str
    longitude: float
    latitude: float
    altitude: Optional[float]
    velocity: Optional[float]
    heading: Optional[float]
    on_ground: bool
    last_update: datetime

# ============ SCHEDULER ENDPOINTS ============

@app.get("/api/scheduler/status")
async def scheduler_status():
    """Get scheduler status"""
    return get_scheduler_status()

@app.post("/api/scheduler/trigger")
async def trigger_fetch_now():
    """Manually trigger data fetch immediately"""
    success = trigger_job_now()
    
    if success:
        return {
            "status": "triggered",
            "message": "Data fetch job triggered, check logs for progress"
        }
    else:
        raise HTTPException(status_code=503, detail="Scheduler not running")

# ============ BASIC ENDPOINTS (no database) ============

@app.get("/")
def read_root():
    return {
        "status": "operational",
        "service": "Geospatial Intelligence Platform",
        "version": "0.2.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/aircraft/live")
async def get_aircraft_live(limit: int = 100):
    """
    Fetch live aircraft from OpenSky (no database)
    """
    try:
        url = "https://opensky-network.org/api/states/all"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        aircraft_list = []
        for state in data['states'][:limit]:
            if state[5] is not None and state[6] is not None:
                aircraft = AircraftPosition(
                    icao24=state[0],
                    callsign=state[1].strip() if state[1] else None,
                    origin_country=state[2],
                    longitude=state[5],
                    latitude=state[6],
                    altitude=state[7],
                    velocity=state[9],
                    heading=state[10],
                    on_ground=state[8] if state[8] is not None else False,
                    last_update=datetime.utcnow()
                )
                aircraft_list.append(aircraft.dict())
        
        return {
            "count": len(aircraft_list),
            "total_tracked": len(data['states']),
            "aircraft": aircraft_list,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"OpenSky API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

# ============ DATABASE ENDPOINTS ============

@app.get("/api/aircraft/fetch-and-store")
async def fetch_and_store_aircraft(limit: int = 100):
    """
    Fetch from OpenSky and store in database
    """
    try:
        from database import get_db
        import crud
        
        # Fetch from OpenSky
        url = "https://opensky-network.org/api/states/all"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Get database session
        db = next(get_db())
        
        stored_count = 0
        try:
            for state in data['states'][:limit]:
                if state[5] is not None and state[6] is not None:
                    aircraft_data = {
                        'callsign': state[1].strip() if state[1] else None,
                        'origin_country': state[2],
                        'longitude': state[5],
                        'latitude': state[6],
                        'altitude': state[7],
                        'velocity': state[9],
                        'heading': state[10],
                        'on_ground': state[8] if state[8] is not None else False,
                        'last_update': datetime.utcnow(),
                        'timestamp': datetime.utcnow()
                    }
                    
                    aircraft = crud.get_or_create_aircraft(db, state[0], aircraft_data)
                    crud.create_aircraft_position(db, aircraft.id, aircraft_data)
                    stored_count += 1
            
            stats = crud.get_stats(db)
            
            return {
                "status": "success",
                "fetched": len(data['states']),
                "stored": stored_count,
                "stats": stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            db.close()
            
    except ImportError:
        raise HTTPException(status_code=503, detail="Database not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/aircraft")
async def get_aircraft_from_db(bbox: Optional[str] = None, limit: int = 1000):
    """
    Get aircraft from database
    Falls back to live API if database not available
    """
    try:
        from database import get_db
        import crud
        from models import Aircraft
        
        db = next(get_db())
        
        try:
            if bbox:
                coords = [float(x) for x in bbox.split(',')]
                if len(coords) != 4:
                    raise HTTPException(status_code=400, detail="bbox format: min_lon,min_lat,max_lon,max_lat")
                
                min_lon, min_lat, max_lon, max_lat = coords
                aircraft_list = crud.get_aircraft_in_bbox(db, min_lon, min_lat, max_lon, max_lat, limit)
            else:
                aircraft_list = db.query(Aircraft).limit(limit).all()
            
            result = []
            for aircraft in aircraft_list:
                if aircraft.last_position:
                    point = to_shape(aircraft.last_position)
                    result.append({
                        "icao24": aircraft.icao24,
                        "callsign": aircraft.callsign,
                        "origin_country": aircraft.origin_country,
                        "longitude": point.x,
                        "latitude": point.y,
                        "altitude": aircraft.altitude_meters,
                        "velocity": aircraft.velocity_mps,
                        "heading": aircraft.heading,
                        "on_ground": aircraft.on_ground,
                        "last_update": aircraft.last_update.isoformat() if aircraft.last_update else None
                    })
            
            return {
                "count": len(result),
                "aircraft": result,
                "source": "database",
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            db.close()
            
    except ImportError:
        # Fallback to live API if database not available
        return await get_aircraft_live(limit)
    except Exception as e:
        print(f"Database error: {e}, falling back to live API")
        return await get_aircraft_live(limit)

@app.get("/api/stats")
async def get_stats():
    """Get database statistics"""
    try:
        from database import get_db
        import crud
        
        db = next(get_db())
        try:
            stats = crud.get_stats(db)
            return {**stats, "timestamp": datetime.utcnow().isoformat()}
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database not available: {str(e)}")

@app.get("/health")
def health_check():
    """Detailed health check"""
    try:
        from database import test_connection
        db_status = "healthy" if test_connection() else "error"
    except:
        db_status = "not_available"
    
    return {
        "api": "healthy",
        "database": db_status,
        "external_apis": {
            "opensky": "operational"
        }
    }

@app.get("/api/aircraft/viewport")
async def aircraft_in_viewport(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    limit: int = 1000
):
    """
    Get aircraft in map viewport (bounding box)
    
    Example: /api/aircraft/viewport?min_lon=-10&min_lat=35&max_lon=20&max_lat=55
    """
    try:
        from database import get_db
        db = next(get_db())
        
        try:
            aircraft = get_aircraft_in_viewport(
                db, min_lon, min_lat, max_lon, max_lat, limit
            )
            
            return {
                "type": "FeatureCollection",
                "features": aircraft,
                "count": len(aircraft),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/aircraft/near")
async def aircraft_near_point(
    lon: float,
    lat: float,
    radius_km: float = 50,
    limit: int = 100
):
    """
    Get aircraft within radius of a point
    
    Example: /api/aircraft/near?lon=12.5&lat=41.9&radius_km=100
    """
    try:
        from database import get_db
        db = next(get_db())
        
        try:
            aircraft = get_aircraft_near_point(db, lon, lat, radius_km, limit)
            
            return {
                "center": {"lon": lon, "lat": lat},
                "radius_km": radius_km,
                "aircraft": aircraft,
                "count": len(aircraft),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/aircraft/{icao24}/trajectory")
async def get_trajectory_endpoint(
    icao24: str,
    hours: int = 1
):
    """Get trajectory (historical path) for specific aircraft"""
    from datetime import timedelta
    from database import get_db
    from geoalchemy2.shape import to_shape 
    
    db = next(get_db())
    
    try:
        # Get aircraft
        aircraft = crud.get_aircraft_by_icao24(db, icao24)
        if not aircraft:
            raise HTTPException(status_code=404, detail="Aircraft not found")
        
        # Get positions from last N hours
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        positions = crud.get_aircraft_positions_since(db, aircraft.id, since)
        
        if not positions:
            return {
                "type": "Feature",
                "properties": {
                    "icao24": icao24,
                    "callsign": aircraft.callsign,
                    "count": 0
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": []
                }
            }
        
        # Extract coordinates from Geography POINT field
        coordinates = []
        for pos in positions:
            if pos.position:  # Geography field
                point = to_shape(pos.position)
                # point.x = longitude, point.y = latitude
                altitude = pos.altitude_meters if pos.altitude_meters else 0
                coordinates.append([point.x, point.y, altitude])
        
        return {
            "type": "Feature",
            "properties": {
                "icao24": icao24,
                "callsign": aircraft.callsign,
                "origin_country": aircraft.origin_country,
                "count": len(coordinates)
            },
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trajectory: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/heatmap/density")
async def density_heatmap(resolution: int = 7, min_count: int = 5):
    """
    Get aircraft density heatmap by H3 hexagons
    
    Example: /api/heatmap/density?resolution=7&min_count=10
    """
    try:
        from database import get_db
        db = next(get_db())
        
        try:
            heatmap = get_density_heatmap(db, resolution, min_count)
            
            return {
                "h3_resolution": resolution,
                "cells": heatmap,
                "count": len(heatmap),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/spatial")
async def spatial_statistics():
    """Get comprehensive spatial statistics"""
    try:
        from database import get_db
        db = next(get_db())
        
        try:
            stats = get_spatial_stats(db)
            return stats
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/routes")
async def busiest_routes(limit: int = 20):
    """Get busiest flight routes/airlines"""
    try:
        from database import get_db
        db = next(get_db())
        
        try:
            routes = get_busiest_routes(db, limit)
            return {
                "routes": routes,
                "count": len(routes),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
# ============= ALERT ENDPOINTS =============
        
@app.get("/api/alerts")
async def get_alerts(
    severity: Optional[str] = None,
    active_only: bool = True,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get alerts with filtering"""
    if severity:
        alerts = crud.get_alerts_by_severity(db, severity, limit=limit)
    else:
        alerts = crud.get_active_alerts(db, limit=limit)
    
    # Convert to GeoJSON
    result = []
    for alert in alerts:
        shape = to_shape(alert.position)
        result.append({
            "id": alert.id,
            "type": alert.alert_type,
            "severity": alert.severity,
            "reason": alert.reason,
            "aircraft_icao24": alert.aircraft_icao24,
            "aircraft_callsign": alert.aircraft_callsign,
            "latitude": shape.y,
            "longitude": shape.x,
            "detected_at": alert.detected_at.isoformat(),
            "is_active": alert.is_active,
            "is_acknowledged": alert.is_acknowledged,
            "priority": alert.priority,
            "details": alert.details or {}
        })
    
    return {"alerts": result, "count": len(result)}

@app.get("/api/alerts/aircraft/{icao24}")
async def get_aircraft_alerts(icao24: str, db: Session = Depends(get_db)):
    """Get alerts for specific aircraft"""
    alerts = crud.get_alerts_for_aircraft(db, icao24, limit=50)
    
    result = []
    for alert in alerts:
        shape = to_shape(alert.position)
        result.append({
            "id": alert.id,
            "type": alert.alert_type,
            "severity": alert.severity,
            "reason": alert.reason,
            "detected_at": alert.detected_at.isoformat(),
            "latitude": shape.y,
            "longitude": shape.x,
            "details": alert.details
        })
    
    return {"alerts": result}

@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert_endpoint(alert_id: int, db: Session = Depends(get_db)):
    """Mark alert as acknowledged"""
    alert = crud.acknowledge_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "acknowledged"}

@app.post("/api/alerts/{alert_id}/resolve")
async def resolve_alert_endpoint(alert_id: int, db: Session = Depends(get_db)):
    """Mark alert as resolved"""
    alert = crud.resolve_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "resolved"}

@app.get("/api/alerts/stats")
async def get_alert_stats(db: Session = Depends(get_db)):
    """Get alert statistics"""
    return crud.get_alert_statistics(db)

@app.post("/api/alerts/detect")
async def run_detection(db: Session = Depends(get_db)):
    """Manually trigger anomaly detection"""
    new_alerts = crud.run_anomaly_detection_on_all_aircraft(db)
    return {"alerts_created": len(new_alerts)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)