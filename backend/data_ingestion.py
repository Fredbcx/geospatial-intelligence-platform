"""
Data Ingestion Pipeline - Fetches data from external APIs and stores in database
Runs scheduled jobs in background
"""

import requests
import asyncio
from datetime import datetime, timezone  
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
import logging

from database import SessionLocal
import crud

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============= OPENSKY NETWORK =============

class OpenSkyFetcher:
    """Fetches aircraft data from OpenSky Network"""
    
    BASE_URL = "https://opensky-network.org/api/states/all"
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize fetcher
        Optional: username/password for authenticated requests (higher rate limits)
        """
        self.auth = (username, password) if username and password else None
        self.last_fetch_time = None
        self.fetch_count = 0
    
    def fetch_aircraft_data(self) -> Optional[Dict]:
        """
        Fetch current aircraft states from OpenSky
        Returns raw API response or None if error
        """
        try:
            logger.info("Fetching aircraft data from OpenSky Network...")
            
            response = requests.get(
                self.BASE_URL,
                auth=self.auth,
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            self.last_fetch_time = datetime.now(timezone.utc)  # FIX
            self.fetch_count += 1
            
            total_states = len(data.get('states', []))
            logger.info(f"✅ Fetched {total_states} aircraft states")
            
            return data
            
        except requests.exceptions.Timeout:
            logger.error("❌ OpenSky API timeout")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ OpenSky API error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching data: {e}")
            return None
    
    def parse_aircraft_state(self, state: List) -> Optional[Dict]:
        """
        Parse OpenSky state vector into our format
        state format: [icao24, callsign, origin_country, time_position, 
                       last_contact, longitude, latitude, baro_altitude, 
                       on_ground, velocity, true_track, vertical_rate, ...]
        """
        try:
            # Skip if no position data
            if state[5] is None or state[6] is None:
                return None
            
            return {
                'icao24': state[0],
                'callsign': state[1].strip() if state[1] else None,
                'origin_country': state[2],
                'longitude': float(state[5]),
                'latitude': float(state[6]),
                'altitude': float(state[7]) if state[7] is not None else None,
                'velocity': float(state[9]) if state[9] is not None else None,
                'heading': float(state[10]) if state[10] is not None else None,
                'vertical_rate': float(state[11]) if state[11] is not None else None,
                'on_ground': bool(state[8]) if state[8] is not None else False,
                'last_update': datetime.now(timezone.utc),  
                'timestamp': datetime.now(timezone.utc)     
            }
        except (IndexError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse state {state[0]}: {e}")
            return None
    
    def store_aircraft_data(self, data: Dict, db: Session) -> Dict:
        """
        Store aircraft data in database
        Returns statistics about what was stored
        """
        states = data.get('states', [])
        
        stored_aircraft = 0
        stored_positions = 0
        skipped = 0
        errors = 0
        
        for state in states:
            try:
                parsed = self.parse_aircraft_state(state)
                
                if parsed is None:
                    skipped += 1
                    continue
                
                # Update or create aircraft
                aircraft = crud.get_or_create_aircraft(
                    db, 
                    parsed['icao24'], 
                    parsed
                )
                stored_aircraft += 1
                
                # Store position history
                crud.create_aircraft_position(
                    db,
                    aircraft.id,
                    parsed
                )
                stored_positions += 1
                
            except Exception as e:
                logger.error(f"Error storing aircraft {state[0]}: {e}")
                errors += 1
                continue
        
        stats = {
            'fetched': len(states),
            'stored_aircraft': stored_aircraft,
            'stored_positions': stored_positions,
            'skipped': skipped,
            'errors': errors,
            'timestamp': datetime.now(timezone.utc).isoformat()  # FIX
        }
        
        logger.info(
            f"📊 Storage stats: {stored_aircraft} aircraft, "
            f"{stored_positions} positions, {skipped} skipped, {errors} errors"
        )
        
        return stats

# ============= SCHEDULED JOB =============

def fetch_and_store_aircraft_job():
    """
    Job function that runs on schedule
    Fetches aircraft data and stores in database
    """
    logger.info("=" * 60)
    logger.info("🚀 Starting scheduled aircraft fetch job")
    logger.info("=" * 60)
    
    db = SessionLocal()
    fetcher = OpenSkyFetcher()
    
    try:
        # Fetch data
        data = fetcher.fetch_aircraft_data()
        
        if data is None:
            logger.warning("⚠️  No data fetched, skipping storage")
            return
        
        # Store in database
        stats = fetcher.store_aircraft_data(data, db)
        
        # Get overall stats
        db_stats = crud.get_stats(db)
        
        logger.info("=" * 60)
        logger.info("✅ Job completed successfully")
        logger.info(f"📈 Total in database: {db_stats['total_aircraft']} aircraft, "
                   f"{db_stats['total_aircraft_positions']} positions")
        logger.info("=" * 60)
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Job failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        db.close()

# ============= TEST FUNCTION =============

def test_ingestion():
    """Test function - run manually to verify ingestion works"""
    logger.info("Testing data ingestion pipeline...")
    result = fetch_and_store_aircraft_job()
    
    if result:
        logger.info("✅ Test successful!")
        logger.info(f"Stats: {result}")
    else:
        logger.error("❌ Test failed")

if __name__ == "__main__":
    # Run test when script is executed directly
    test_ingestion()