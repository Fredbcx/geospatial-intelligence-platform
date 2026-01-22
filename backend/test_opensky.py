import requests
import json
from datetime import datetime

def test_opensky_api():
    """
    Test fetching live aircraft data from OpenSky Network
    FREE API - no key required!
    Rate limit: reasonable for demo use
    """
    print("🛩️  Testing OpenSky Network API...\n")
    
    url = "https://opensky-network.org/api/states/all"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        total_aircraft = len(data['states'])
        print(f"✅ Total aircraft tracked: {total_aircraft}")
        
        # Filter aircraft with valid positions
        valid_aircraft = [
            state for state in data['states'] 
            if state[5] is not None and state[6] is not None  # Has lat/lon
        ]
        
        print(f"✅ Aircraft with valid positions: {len(valid_aircraft)}")
        
        # Sample aircraft
        if valid_aircraft:
            sample = valid_aircraft[0]
            print(f"\n📍 Sample Aircraft:")
            print(f"  ICAO24: {sample[0]}")
            print(f"  Callsign: {sample[1].strip() if sample[1] else 'Unknown'}")
            print(f"  Origin: {sample[2]}")
            print(f"  Longitude: {sample[5]}")
            print(f"  Latitude: {sample[6]}")
            print(f"  Altitude: {sample[7]} meters")
            print(f"  Velocity: {sample[9]} m/s")
            print(f"  Heading: {sample[10]} degrees")
            
            # Show raw data structure
            print(f"\n📋 Raw data structure (first aircraft):")
            print(json.dumps(sample, indent=2))
            
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data: {e}")
        return False

if __name__ == "__main__":
    test_opensky_api()