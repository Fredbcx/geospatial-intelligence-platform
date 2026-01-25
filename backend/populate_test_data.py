"""
Populate database with fake aircraft data for testing
Run this when OpenSky is down
"""

import random
from datetime import datetime, timezone
from database import SessionLocal
import crud
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_test_aircraft(count=500):
    """Generate fake but realistic aircraft data"""
    aircraft = []
    
    regions = [
        # Italia
        {"min_lat": 36.0, "max_lat": 47.0, "min_lon": 6.0, "max_lon": 19.0, "weight": 0.3},
        # Francia
        {"min_lat": 42.0, "max_lat": 51.0, "min_lon": -5.0, "max_lon": 8.0, "weight": 0.2},
        # Germania
        {"min_lat": 47.0, "max_lat": 55.0, "min_lon": 6.0, "max_lon": 15.0, "weight": 0.2},
        # Spagna
        {"min_lat": 36.0, "max_lat": 44.0, "min_lon": -9.0, "max_lon": 3.0, "weight": 0.15},
        # UK
        {"min_lat": 50.0, "max_lat": 59.0, "min_lon": -8.0, "max_lon": 2.0, "weight": 0.15},
    ]
    
    countries = ["Italy", "France", "Germany", "Spain", "United Kingdom", 
                 "Netherlands", "Belgium", "Switzerland", "Austria", "Poland"]
    
    airlines = ["AZA", "AFR", "DLH", "IBE", "BAW", "RYR", "EZY", "WZZ", "VLG", "UAE"]
    
    for i in range(count):
        region = random.choices(regions, weights=[r["weight"] for r in regions])[0]
        
        on_ground = random.random() < 0.08  
        altitude = 0 if on_ground else random.uniform(1000, 12000)
        
        aircraft.append({
            'icao24': f"{random.randint(0, 0xffffff):06x}",
            'callsign': f"{random.choice(airlines)}{random.randint(100, 9999)}",
            'origin_country': random.choice(countries),
            'longitude': random.uniform(region["min_lon"], region["max_lon"]),
            'latitude': random.uniform(region["min_lat"], region["max_lat"]),
            'altitude': altitude,
            'velocity': 0 if on_ground else random.uniform(200, 900),
            'heading': random.uniform(0, 360),
            'vertical_rate': random.uniform(-8, 8) if not on_ground else 0,
            'on_ground': on_ground,
            'last_update': datetime.now(timezone.utc),
            'timestamp': datetime.now(timezone.utc)
        })
    
    return aircraft

def populate_database(count=500):
    """Populate database with test data"""
    logger.info(f"Generating {count} test aircraft...")
    aircraft_list = generate_test_aircraft(count)
    
    db = SessionLocal()
    try:
        stored_aircraft = 0
        stored_positions = 0
        errors = 0
        
        for data in aircraft_list:
            try:
                # Create/update aircraft
                aircraft = crud.get_or_create_aircraft(db, data['icao24'], data)
                stored_aircraft += 1
                
                # Store position
                crud.create_aircraft_position(db, aircraft.id, data)
                stored_positions += 1
                
            except Exception as e:
                logger.error(f"Error storing aircraft: {e}")
                errors += 1
                continue
        
        logger.info("=" * 60)
        logger.info(f"✅ Stored {stored_aircraft} aircraft")
        logger.info(f"✅ Stored {stored_positions} positions")
        if errors > 0:
            logger.warning(f"⚠️  {errors} errors")
        logger.info("=" * 60)
        
        # Verify database stats
        stats = crud.get_stats(db)
        logger.info(f"📊 Total in database:")
        logger.info(f"   Aircraft: {stats['total_aircraft']}")
        logger.info(f"   Positions: {stats['total_aircraft_positions']}")
        
        return {
            'stored_aircraft': stored_aircraft,
            'stored_positions': stored_positions,
            'errors': errors
        }
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🧪 POPULATING DATABASE WITH TEST DATA")
    logger.info("=" * 60)
    result = populate_database(500)
    
    if result:
        logger.info("✅ Test data population completed successfully!")
    else:
        logger.error("❌ Test data population failed!")