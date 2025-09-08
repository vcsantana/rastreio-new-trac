"""
Migration: Add extended position fields
Adds all the new position fields from the Java implementation
"""
import asyncio
from sqlalchemy import text
from app.database import engine

async def upgrade():
    """Add new position fields"""
    async with engine.begin() as conn:
        # GPS and Satellite Information
        await conn.execute(text("""
            ALTER TABLE positions 
            ADD COLUMN IF NOT EXISTS hdop FLOAT,
            ADD COLUMN IF NOT EXISTS vdop FLOAT,
            ADD COLUMN IF NOT EXISTS pdop FLOAT,
            ADD COLUMN IF NOT EXISTS satellites INTEGER,
            ADD COLUMN IF NOT EXISTS satellites_visible INTEGER
        """))
        
        # Network and Communication
        await conn.execute(text("""
            ALTER TABLE positions 
            ADD COLUMN IF NOT EXISTS rssi INTEGER,
            ADD COLUMN IF NOT EXISTS roaming BOOLEAN,
            ADD COLUMN IF NOT EXISTS network_type VARCHAR(50),
            ADD COLUMN IF NOT EXISTS cell_id VARCHAR(50),
            ADD COLUMN IF NOT EXISTS lac VARCHAR(50),
            ADD COLUMN IF NOT EXISTS mnc VARCHAR(50),
            ADD COLUMN IF NOT EXISTS mcc VARCHAR(50)
        """))
        
        # Fuel and Engine
        await conn.execute(text("""
            ALTER TABLE positions 
            ADD COLUMN IF NOT EXISTS fuel_level FLOAT,
            ADD COLUMN IF NOT EXISTS fuel_used FLOAT,
            ADD COLUMN IF NOT EXISTS fuel_consumption FLOAT,
            ADD COLUMN IF NOT EXISTS rpm INTEGER,
            ADD COLUMN IF NOT EXISTS engine_load FLOAT,
            ADD COLUMN IF NOT EXISTS engine_temp FLOAT,
            ADD COLUMN IF NOT EXISTS throttle FLOAT,
            ADD COLUMN IF NOT EXISTS coolant_temp FLOAT,
            ADD COLUMN IF NOT EXISTS hours FLOAT
        """))
        
        # Battery and Power
        await conn.execute(text("""
            ALTER TABLE positions 
            ADD COLUMN IF NOT EXISTS battery FLOAT,
            ADD COLUMN IF NOT EXISTS battery_level INTEGER,
            ADD COLUMN IF NOT EXISTS power FLOAT,
            ADD COLUMN IF NOT EXISTS charge BOOLEAN,
            ADD COLUMN IF NOT EXISTS external_power BOOLEAN
        """))
        
        # Odometer and Distance
        await conn.execute(text("""
            ALTER TABLE positions 
            ADD COLUMN IF NOT EXISTS odometer FLOAT,
            ADD COLUMN IF NOT EXISTS odometer_service FLOAT,
            ADD COLUMN IF NOT EXISTS odometer_trip FLOAT,
            ADD COLUMN IF NOT EXISTS total_distance FLOAT,
            ADD COLUMN IF NOT EXISTS distance FLOAT,
            ADD COLUMN IF NOT EXISTS trip_distance FLOAT
        """))
        
        # Control and Status
        await conn.execute(text("""
            ALTER TABLE positions 
            ADD COLUMN IF NOT EXISTS ignition BOOLEAN,
            ADD COLUMN IF NOT EXISTS motion BOOLEAN,
            ADD COLUMN IF NOT EXISTS armed BOOLEAN,
            ADD COLUMN IF NOT EXISTS blocked BOOLEAN,
            ADD COLUMN IF NOT EXISTS lock BOOLEAN,
            ADD COLUMN IF NOT EXISTS door BOOLEAN,
            ADD COLUMN IF NOT EXISTS driver_unique_id VARCHAR(255)
        """))
        
        # Alarms and Events
        await conn.execute(text("""
            ALTER TABLE positions 
            ADD COLUMN IF NOT EXISTS alarm VARCHAR(255),
            ADD COLUMN IF NOT EXISTS event VARCHAR(255),
            ADD COLUMN IF NOT EXISTS status VARCHAR(255),
            ADD COLUMN IF NOT EXISTS alarm_type VARCHAR(255),
            ADD COLUMN IF NOT EXISTS event_type VARCHAR(255)
        """))
        
        # Geofences
        await conn.execute(text("""
            ALTER TABLE positions 
            ADD COLUMN IF NOT EXISTS geofence_ids TEXT,
            ADD COLUMN IF NOT EXISTS geofence VARCHAR(255),
            ADD COLUMN IF NOT EXISTS geofence_id INTEGER
        """))
        
        # Additional Sensors
        await conn.execute(text("""
            ALTER TABLE positions 
            ADD COLUMN IF NOT EXISTS temperature FLOAT,
            ADD COLUMN IF NOT EXISTS humidity FLOAT,
            ADD COLUMN IF NOT EXISTS pressure FLOAT,
            ADD COLUMN IF NOT EXISTS light FLOAT,
            ADD COLUMN IF NOT EXISTS proximity FLOAT,
            ADD COLUMN IF NOT EXISTS acceleration FLOAT,
            ADD COLUMN IF NOT EXISTS gyroscope FLOAT,
            ADD COLUMN IF NOT EXISTS magnetometer FLOAT
        """))
        
        # CAN Bus Data
        await conn.execute(text("""
            ALTER TABLE positions 
            ADD COLUMN IF NOT EXISTS can_data TEXT,
            ADD COLUMN IF NOT EXISTS obd_speed FLOAT,
            ADD COLUMN IF NOT EXISTS obd_rpm INTEGER,
            ADD COLUMN IF NOT EXISTS obd_fuel FLOAT,
            ADD COLUMN IF NOT EXISTS obd_temp FLOAT
        """))
        
        # Maintenance
        await conn.execute(text("""
            ALTER TABLE positions 
            ADD COLUMN IF NOT EXISTS maintenance BOOLEAN,
            ADD COLUMN IF NOT EXISTS service_due TIMESTAMP WITH TIME ZONE,
            ADD COLUMN IF NOT EXISTS oil_level FLOAT,
            ADD COLUMN IF NOT EXISTS tire_pressure FLOAT
        """))
        
        # Driver Behavior
        await conn.execute(text("""
            ALTER TABLE positions 
            ADD COLUMN IF NOT EXISTS hard_acceleration BOOLEAN,
            ADD COLUMN IF NOT EXISTS hard_braking BOOLEAN,
            ADD COLUMN IF NOT EXISTS hard_turning BOOLEAN,
            ADD COLUMN IF NOT EXISTS idling BOOLEAN,
            ADD COLUMN IF NOT EXISTS overspeed BOOLEAN
        """))
        
        # Location Quality
        await conn.execute(text("""
            ALTER TABLE positions 
            ADD COLUMN IF NOT EXISTS location_accuracy FLOAT,
            ADD COLUMN IF NOT EXISTS gps_accuracy FLOAT,
            ADD COLUMN IF NOT EXISTS network_accuracy FLOAT
        """))
        
        # Protocol Specific
        await conn.execute(text("""
            ALTER TABLE positions 
            ADD COLUMN IF NOT EXISTS protocol_version VARCHAR(50),
            ADD COLUMN IF NOT EXISTS firmware_version VARCHAR(50),
            ADD COLUMN IF NOT EXISTS hardware_version VARCHAR(50)
        """))
        
        # Time and Status
        await conn.execute(text("""
            ALTER TABLE positions 
            ADD COLUMN IF NOT EXISTS outdated BOOLEAN DEFAULT FALSE
        """))
        
        # Custom Attributes
        await conn.execute(text("""
            ALTER TABLE positions 
            ADD COLUMN IF NOT EXISTS custom1 VARCHAR(255),
            ADD COLUMN IF NOT EXISTS custom2 VARCHAR(255),
            ADD COLUMN IF NOT EXISTS custom3 VARCHAR(255),
            ADD COLUMN IF NOT EXISTS custom4 VARCHAR(255),
            ADD COLUMN IF NOT EXISTS custom5 VARCHAR(255)
        """))
        
        # Add performance indexes
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_position_device_time 
            ON positions (device_id, server_time)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_position_lat_lon 
            ON positions (latitude, longitude)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_position_protocol 
            ON positions (protocol)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_position_valid 
            ON positions (valid)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_position_fix_time 
            ON positions (fix_time)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_position_unknown_device 
            ON positions (unknown_device_id)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_position_ignition 
            ON positions (ignition)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_position_motion 
            ON positions (motion)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_position_alarm 
            ON positions (alarm)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_position_event 
            ON positions (event)
        """))

async def downgrade():
    """Remove new position fields"""
    async with engine.begin() as conn:
        # Remove indexes first
        indexes_to_drop = [
            "idx_position_device_time",
            "idx_position_lat_lon", 
            "idx_position_protocol",
            "idx_position_valid",
            "idx_position_fix_time",
            "idx_position_unknown_device",
            "idx_position_ignition",
            "idx_position_motion",
            "idx_position_alarm",
            "idx_position_event"
        ]
        
        for index in indexes_to_drop:
            await conn.execute(text(f"DROP INDEX IF EXISTS {index}"))
        
        # Remove columns
        columns_to_drop = [
            # GPS and Satellite Information
            "hdop", "vdop", "pdop", "satellites", "satellites_visible",
            # Network and Communication
            "rssi", "roaming", "network_type", "cell_id", "lac", "mnc", "mcc",
            # Fuel and Engine
            "fuel_level", "fuel_used", "fuel_consumption", "rpm", "engine_load", 
            "engine_temp", "throttle", "coolant_temp", "hours",
            # Battery and Power
            "battery", "battery_level", "power", "charge", "external_power",
            # Odometer and Distance
            "odometer", "odometer_service", "odometer_trip", "total_distance", 
            "distance", "trip_distance",
            # Control and Status
            "ignition", "motion", "armed", "blocked", "lock", "door", "driver_unique_id",
            # Alarms and Events
            "alarm", "event", "status", "alarm_type", "event_type",
            # Geofences
            "geofence_ids", "geofence", "geofence_id",
            # Additional Sensors
            "temperature", "humidity", "pressure", "light", "proximity", 
            "acceleration", "gyroscope", "magnetometer",
            # CAN Bus Data
            "can_data", "obd_speed", "obd_rpm", "obd_fuel", "obd_temp",
            # Maintenance
            "maintenance", "service_due", "oil_level", "tire_pressure",
            # Driver Behavior
            "hard_acceleration", "hard_braking", "hard_turning", "idling", "overspeed",
            # Location Quality
            "location_accuracy", "gps_accuracy", "network_accuracy",
            # Protocol Specific
            "protocol_version", "firmware_version", "hardware_version",
            # Time and Status
            "outdated",
            # Custom Attributes
            "custom1", "custom2", "custom3", "custom4", "custom5"
        ]
        
        for column in columns_to_drop:
            await conn.execute(text(f"ALTER TABLE positions DROP COLUMN IF EXISTS {column}"))

if __name__ == "__main__":
    asyncio.run(upgrade())
