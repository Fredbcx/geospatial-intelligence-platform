from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from datetime import datetime, timezone  

Base = declarative_base()

class Aircraft(Base):
    """Aircraft entity - stores latest position"""
    __tablename__ = 'aircraft'
    
    id = Column(Integer, primary_key=True, index=True)
    icao24 = Column(String(20), unique=True, nullable=False, index=True)
    callsign = Column(String(50))
    aircraft_type = Column(String(100))
    origin_country = Column(String(100))
    last_position = Column(Geography('POINT', srid=4326))
    last_update = Column(DateTime(timezone=True))
    altitude_meters = Column(Float)
    velocity_mps = Column(Float)
    heading = Column(Float)
    vertical_rate = Column(Float)
    on_ground = Column(Boolean)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))  # FIX
    
    positions = relationship("AircraftPosition", back_populates="aircraft", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Aircraft {self.icao24} - {self.callsign}>"

class AircraftPosition(Base):
    """Aircraft position history - time series data"""
    __tablename__ = 'aircraft_positions'
    
    id = Column(Integer, primary_key=True, index=True)
    aircraft_id = Column(Integer, ForeignKey('aircraft.id', ondelete='CASCADE'), nullable=False)
    position = Column(Geography('POINT', srid=4326), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    altitude_meters = Column(Float)
    velocity_mps = Column(Float)
    heading = Column(Float)
    h3_cell_id = Column(String(20), index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))  # FIX
    
    aircraft = relationship("Aircraft", back_populates="positions")
    
    def __repr__(self):
        return f"<AircraftPosition {self.aircraft_id} at {self.timestamp}>"

class Vessel(Base):
    """Vessel entity - stores latest position"""
    __tablename__ = 'vessels'
    
    id = Column(Integer, primary_key=True, index=True)
    mmsi = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255))
    vessel_type = Column(String(100))
    flag_country = Column(String(10))
    last_position = Column(Geography('POINT', srid=4326))
    last_update = Column(DateTime(timezone=True))
    speed_knots = Column(Float)
    heading = Column(Float)
    destination = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))  # FIX
    
    positions = relationship("VesselPosition", back_populates="vessel", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Vessel {self.mmsi} - {self.name}>"

class VesselPosition(Base):
    """Vessel position history"""
    __tablename__ = 'vessel_positions'
    
    id = Column(Integer, primary_key=True, index=True)
    vessel_id = Column(Integer, ForeignKey('vessels.id', ondelete='CASCADE'), nullable=False)
    position = Column(Geography('POINT', srid=4326), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    speed_knots = Column(Float)
    heading = Column(Float)
    h3_cell_id = Column(String(20), index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))  # FIX
    
    vessel = relationship("Vessel", back_populates="positions")

class Event(Base):
    """Geospatial events (GDELT, earthquakes, etc)"""
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    title = Column(String(500))
    description = Column(Text)
    position = Column(Geography('POINT', srid=4326), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    severity = Column(String(50))
    source = Column(String(100))
    source_url = Column(Text)
    event_metadata = Column("metadata", JSON)
    h3_cell_id = Column(String(20), index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))  # FIX
    
    def __repr__(self):
        return f"<Event {self.event_type} - {self.title}>"
        
        
class Alert(Base):
    """Anomaly alerts detected by the system"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    aircraft_icao24 = Column(String(20), index=True)
    aircraft_callsign = Column(String(50))
    aircraft_id = Column(Integer, ForeignKey('aircraft.id', ondelete='SET NULL'), nullable=True)
    position = Column(Geography('POINT', srid=4326), nullable=False)
    detected_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_acknowledged = Column(Boolean, default=False)
    details = Column(JSON)
    priority = Column(Integer, default=50)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<Alert {self.alert_type} - {self.severity} - {self.aircraft_callsign}>"