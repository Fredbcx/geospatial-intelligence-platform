"""
Populate database with fake aircraft data INCLUDING historical positions
This creates realistic trajectories for testing
"""

import random
from datetime import datetime, timezone, timedelta
from database import SessionLocal
import crud
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_realistic_trajectory(start_lat, start_lon, steps=30):
    """
    Generate a realistic flight path
    
    Returns list of position dicts with all required fields
    """
    trajectory = []
    
    # Random direction (heading)
    heading = random.uniform(0, 360)
    
    # Speed (km/h to degrees per minute)
    speed_kmh = random.uniform(400, 900)
    speed_deg_per_min = speed_kmh / 111  # Rough approximation
    
    # Starting altitude
    altitude = random.uniform(8000, 12000)
    
    current_lat = start_lat
    current_lon = start_lon
    current_time = datetime.now(timezone.utc) - timedelta(hours=1)
    
    for i in range(steps):
        # Small random variations in heading
        heading += random.uniform(-5, 5)
        heading = heading % 360  # Keep in 0-360 range
        
        # Move aircraft (convert heading to movement)
        import math
        heading_rad = math.radians(heading)
        lat_change = speed_deg_per_min * 2 * math.cos(heading_rad) * random.uniform(0.8, 1.2)
        lon_change = speed_deg_per_min * 2 * math.sin(heading_rad) * random.uniform(0.8, 1.2)
        
        current_lat += lat_change
        current_lon += lon_change
        
        # ✅ Bounce at bounds instead of clamping
        if current_lat > 60:
            current_lat = 60 - (current_lat - 60)
            heading = 360 - heading  # Reverse direction
        elif current_lat < 35:
            current_lat = 35 + (35 - current_lat)
            heading = 360 - heading
            
        if current_lon > 30:
            current_lon = 30 - (current_lon - 30)
            heading = 180 - heading
        elif current_lon < -10:
            current_lon = -10 + (-10 - current_lon)
            heading = 180 - heading
        
        # Small altitude variations
        altitude += random.uniform(-200, 200)
        altitude = max(5000, min(12000, altitude))
        
        # Time progression (2 minutes between points)
        current_time += timedelta(minutes=2)
        
        trajectory.append({
            'latitude': current_lat,
            'longitude': current_lon,  # ✅ CRITICAL: Must include longitude!
            'altitude': altitude,
            'timestamp': current_time,
            'velocity': speed_kmh / 3.6,  # Convert to m/s
            'heading': heading,
            'vertical_rate': random.uniform(-2, 2),
            'on_ground': False
        })
    
    return trajectory

def generate_test_aircraft_with_trajectories(count=100):
    """Generate fake aircraft with realistic trajectories"""
    aircraft_list = []
    
    # Europa bounds
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
    
    countries = ["Italy", "France", "Germany", "Spain", "United Kingdom"]
    airlines = ["AZA", "AFR", "DLH", "IBE", "BAW", "RYR", "EZY"]
    
    for i in range(count):
        region = random.choices(regions, weights=[r["weight"] for r in regions])[0]
        
        # Starting position
        start_lat = random.uniform(region["min_lat"], region["max_lat"])
        start_lon = random.uniform(region["min_lon"], region["max_lon"])
        
        # Generate trajectory (30 points over 1 hour)
        trajectory = generate_realistic_trajectory(start_lat, start_lon, steps=30)
        
        aircraft_data = {
            'icao24': f"{random.randint(0, 0xffffff):06x}",
            'callsign': f"{random.choice(airlines)}{random.randint(100, 9999)}",
            'origin_country': random.choice(countries),
            'on_ground': False,
            'trajectory': trajectory
        }
        
        aircraft_list.append(aircraft_data)
    
    return aircraft_list

def populate_database_with_trajectories(count=100):
    """Populate database with aircraft + their trajectories"""
    logger.info(f"🛫 Generating {count} aircraft with trajectories...")
    aircraft_list = generate_test_aircraft_with_trajectories(count)
    
    db = SessionLocal()
    try:
        stored_aircraft = 0
        stored_positions = 0
        errors = 0
        
        for aircraft_data in aircraft_list:
            try:
                # Get latest position for aircraft creation
                latest = aircraft_data['trajectory'][-1]
                
                # Get/create aircraft with complete data
                aircraft = crud.get_or_create_aircraft(
                    db, 
                    aircraft_data['icao24'],
                    {
                        'callsign': aircraft_data['callsign'],
                        'origin_country': aircraft_data['origin_country'],
                        'on_ground': False,
                        'latitude': latest['latitude'],
                        'longitude': latest['longitude'],
                        'altitude': latest['altitude'],
                        'velocity': latest['velocity'],
                        'heading': latest['heading'],
                        'vertical_rate': latest.get('vertical_rate', 0),
                        'last_update': latest['timestamp'],
                        'timestamp': latest['timestamp']
                    }
                )
                stored_aircraft += 1
                
                # Store all trajectory points
                for point in aircraft_data['trajectory']:
                    # Include ALL required fields
                    position_data = {
                        'latitude': point['latitude'],
                        'longitude': point['longitude'],  # ✅ WAS MISSING!
                        'altitude': point['altitude'],
                        'velocity': point['velocity'],
                        'heading': point['heading'],
                        'vertical_rate': point['vertical_rate'],
                        'on_ground': point['on_ground'],
                        'timestamp': point['timestamp']
                    }
                    
                    crud.create_aircraft_position(db, aircraft.id, position_data)
                    stored_positions += 1
                
                # Update aircraft with latest position
                latest = aircraft_data['trajectory'][-1]
                aircraft.latitude = latest['latitude']
                aircraft.longitude = latest['longitude']
                aircraft.altitude_meters = latest['altitude']
                aircraft.velocity_mps = latest['velocity']
                aircraft.heading = latest['heading']
                aircraft.last_update = latest['timestamp']
                db.commit()
                
            except Exception as e:
                logger.error(f"❌ Error storing aircraft {aircraft_data['icao24']}: {e}")
                import traceback
                traceback.print_exc()
                db.rollback()
                errors += 1
                continue
        
        logger.info("=" * 60)
        logger.info(f"✅ Stored {stored_aircraft} aircraft")
        logger.info(f"✅ Stored {stored_positions} positions")
        if stored_aircraft > 0:
            logger.info(f"   Average: {stored_positions // stored_aircraft} points per aircraft")
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
    logger.info("🧪 POPULATING DATABASE WITH TRAJECTORY DATA")
    logger.info("=" * 60)
    
    # Generate 100 aircraft with 30 points each = 3,000 positions
    result = populate_database_with_trajectories(100)
    
    if result:
        logger.info("✅ Trajectory data population completed!")
        logger.info(f"   You now have {result['stored_aircraft']} aircraft")
        logger.info(f"   Each with ~30 historical positions")
        logger.info(f"   Total positions: {result['stored_positions']}")
    else:
        logger.error("❌ Trajectory data population failed!")