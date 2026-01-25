from database import SessionLocal
from models import Aircraft, AircraftPosition

db = SessionLocal()
try:
    aircraft_count = db.query(Aircraft).count()
    positions_count = db.query(AircraftPosition).count()
    print(f'📊 Before: {aircraft_count} aircraft, {positions_count} positions')
    
    db.query(AircraftPosition).delete()
    db.query(Aircraft).delete()
    db.commit()
    
    print('✅ Database cleared!')
    
    aircraft_count = db.query(Aircraft).count()
    positions_count = db.query(AircraftPosition).count()
    print(f'📊 After: {aircraft_count} aircraft, {positions_count} positions')
finally:
    db.close()