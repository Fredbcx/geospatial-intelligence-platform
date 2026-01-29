"""
Clean database - Remove all aircraft, positions, and alerts
Preserves schema and indexes
"""
from database import SessionLocal
from models import Aircraft, AircraftPosition, Alert
import sys

def clean_database():
    """Remove all data from tables"""
    db = SessionLocal()
    try:
        # Count before
        aircraft_count = db.query(Aircraft).count()
        positions_count = db.query(AircraftPosition).count()
        alerts_count = db.query(Alert).count()
        
        print('=' * 60)
        print('📊 BEFORE CLEANUP:')
        print(f'   Aircraft: {aircraft_count}')
        print(f'   Positions: {positions_count}')
        print(f'   Alerts: {alerts_count}')
        print('=' * 60)
        
        if aircraft_count == 0 and positions_count == 0 and alerts_count == 0:
            print('✅ Database already empty!')
            return
        
        # Delete in correct order (foreign keys)
        print('\n🗑️  Deleting data...')
        
        deleted_positions = db.query(AircraftPosition).delete()
        print(f'   ✓ Deleted {deleted_positions} positions')
        
        deleted_alerts = db.query(Alert).delete()
        print(f'   ✓ Deleted {deleted_alerts} alerts')
        
        deleted_aircraft = db.query(Aircraft).delete()
        print(f'   ✓ Deleted {deleted_aircraft} aircraft')
        
        db.commit()
        print('\n✅ Database cleared successfully!')
        
        # Count after
        aircraft_count = db.query(Aircraft).count()
        positions_count = db.query(AircraftPosition).count()
        alerts_count = db.query(Alert).count()
        
        print('\n📊 AFTER CLEANUP:')
        print(f'   Aircraft: {aircraft_count}')
        print(f'   Positions: {positions_count}')
        print(f'   Alerts: {alerts_count}')
        print('=' * 60)
        
    except Exception as e:
        print(f'\n❌ Error cleaning database: {e}')
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    print('⚠️  WARNING: This will delete ALL data from the database!')
    response = input('Are you sure? (yes/no): ')
    
    if response.lower() == 'yes':
        clean_database()
    else:
        print('❌ Aborted.')