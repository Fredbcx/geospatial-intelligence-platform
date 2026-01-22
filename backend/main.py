from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Geospatial Intelligence Platform API",
    description="Real-time tracking and analysis of global assets",
    version="0.2.0"
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

# ============ DATABASE STARTUP EVENT ============
# Questo viene eseguito SOLO quando FastAPI parte, non all'import!

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
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
        else:
            print("⚠️  Database connection failed - running in API-only mode")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("⚠️  Running in API-only mode (database modules not available)")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        print("⚠️  Running in API-only mode (no persistence)")
    
    print("=" * 50)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)