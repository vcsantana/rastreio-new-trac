"""
Position attribute constants
Based on Traccar Java original implementation
"""
from typing import Dict, Any

class PositionKeys:
    """
    Constants for position attributes
    Based on org.traccar.model.Position from Java implementation
    """
    
    # GPS and Satellite Information
    HDOP = "hdop"                    # Horizontal Dilution of Precision
    VDOP = "vdop"                    # Vertical Dilution of Precision
    PDOP = "pdop"                    # Position Dilution of Precision
    SATELLITES = "sat"               # Number of satellites in use
    SATELLITES_VISIBLE = "satVisible"  # Number of visible satellites
    
    # Network and Communication
    RSSI = "rssi"                    # Received Signal Strength Indicator
    ROAMING = "roaming"              # Roaming status
    NETWORK_TYPE = "networkType"     # Network type (2G, 3G, 4G, etc.)
    CELL_ID = "cellId"               # Cell tower ID
    LAC = "lac"                      # Location Area Code
    MNC = "mnc"                      # Mobile Network Code
    MCC = "mcc"                      # Mobile Country Code
    
    # Fuel and Engine
    FUEL_LEVEL = "fuel"              # Fuel level percentage
    FUEL_USED = "fuelUsed"           # Fuel used in liters
    FUEL_CONSUMPTION = "fuelConsumption"  # Fuel consumption rate
    RPM = "rpm"                      # Engine RPM
    ENGINE_LOAD = "engineLoad"       # Engine load percentage
    ENGINE_TEMP = "engineTemp"       # Engine temperature
    THROTTLE = "throttle"            # Throttle position
    COOLANT_TEMP = "coolantTemp"     # Coolant temperature
    
    # Battery and Power
    BATTERY = "battery"              # Battery voltage
    BATTERY_LEVEL = "batteryLevel"   # Battery level percentage
    POWER = "power"                  # Power supply voltage
    CHARGE = "charge"                # Charging status
    EXTERNAL_POWER = "externalPower" # External power status
    
    # Odometer and Distance
    ODOMETER = "odometer"            # Total odometer reading
    ODOMETER_SERVICE = "serviceOdometer"  # Service odometer
    ODOMETER_TRIP = "tripOdometer"   # Trip odometer
    TOTAL_DISTANCE = "totalDistance" # Total distance traveled
    DISTANCE = "distance"            # Distance from previous position
    TRIP_DISTANCE = "tripDistance"   # Distance in current trip
    
    # Control and Status
    IGNITION = "ignition"            # Ignition status
    MOTION = "motion"                # Motion status
    ARMED = "armed"                  # Armed status
    BLOCKED = "blocked"              # Blocked status
    LOCK = "lock"                    # Lock status
    DOOR = "door"                    # Door status
    HOURS = "hours"                  # Engine hours
    DRIVER_UNIQUE_ID = "driverUniqueId"  # Driver ID
    
    # Alarms and Events
    ALARM = "alarm"                  # Alarm type
    EVENT = "event"                  # Event type
    STATUS = "status"                # Device status
    ALARM_TYPE = "alarmType"         # Specific alarm type
    EVENT_TYPE = "eventType"         # Specific event type
    
    # Geofences
    GEOFENCE_IDS = "geofenceIds"     # List of geofence IDs
    GEOFENCE = "geofence"            # Geofence name
    GEOFENCE_ID = "geofenceId"       # Single geofence ID
    
    # Additional Sensors
    TEMPERATURE = "temperature"      # Temperature sensor
    HUMIDITY = "humidity"            # Humidity sensor
    PRESSURE = "pressure"            # Pressure sensor
    LIGHT = "light"                  # Light sensor
    PROXIMITY = "proximity"          # Proximity sensor
    ACCELERATION = "acceleration"    # Acceleration sensor
    GYROSCOPE = "gyroscope"          # Gyroscope sensor
    MAGNETOMETER = "magnetometer"    # Magnetometer sensor
    
    # CAN Bus Data
    CAN_DATA = "canData"             # CAN bus data
    OBD_SPEED = "obdSpeed"           # OBD speed reading
    OBD_RPM = "obdRpm"               # OBD RPM reading
    OBD_FUEL = "obdFuel"             # OBD fuel level
    OBD_TEMP = "obdTemp"             # OBD temperature
    
    # Maintenance
    MAINTENANCE = "maintenance"      # Maintenance status
    SERVICE_DUE = "serviceDue"       # Service due date
    OIL_LEVEL = "oilLevel"           # Oil level
    TIRE_PRESSURE = "tirePressure"   # Tire pressure
    
    # Driver Behavior
    HARD_ACCELERATION = "hardAcceleration"  # Hard acceleration event
    HARD_BRAKING = "hardBraking"     # Hard braking event
    HARD_TURNING = "hardTurning"     # Hard turning event
    IDLING = "idling"                # Idling status
    OVERSPEED = "overspeed"          # Overspeed event
    
    # Location Quality
    LOCATION_ACCURACY = "locationAccuracy"  # Location accuracy
    GPS_ACCURACY = "gpsAccuracy"     # GPS accuracy
    NETWORK_ACCURACY = "networkAccuracy"  # Network accuracy
    
    # Protocol Specific
    PROTOCOL_VERSION = "protocolVersion"  # Protocol version
    FIRMWARE_VERSION = "firmwareVersion"  # Firmware version
    HARDWARE_VERSION = "hardwareVersion"  # Hardware version
    
    # Time and Status
    OUTDATED = "outdated"            # Position outdated status
    VALID = "valid"                  # Position validity
    FIX_TIME = "fixTime"             # GPS fix time
    DEVICE_TIME = "deviceTime"       # Device time
    SERVER_TIME = "serverTime"       # Server time
    
    # Custom Attributes
    CUSTOM_1 = "custom1"             # Custom attribute 1
    CUSTOM_2 = "custom2"             # Custom attribute 2
    CUSTOM_3 = "custom3"             # Custom attribute 3
    CUSTOM_4 = "custom4"             # Custom attribute 4
    CUSTOM_5 = "custom5"             # Custom attribute 5
    
    @classmethod
    def get_all_keys(cls) -> Dict[str, str]:
        """Get all position keys as a dictionary"""
        return {key: value for key, value in cls.__dict__.items() 
                if not key.startswith('_') and isinstance(value, str)}
    
    @classmethod
    def get_gps_keys(cls) -> Dict[str, str]:
        """Get GPS and satellite related keys"""
        return {
            cls.HDOP: cls.HDOP,
            cls.VDOP: cls.VDOP,
            cls.PDOP: cls.PDOP,
            cls.SATELLITES: cls.SATELLITES,
            cls.SATELLITES_VISIBLE: cls.SATELLITES_VISIBLE,
            cls.LOCATION_ACCURACY: cls.LOCATION_ACCURACY,
            cls.GPS_ACCURACY: cls.GPS_ACCURACY
        }
    
    @classmethod
    def get_network_keys(cls) -> Dict[str, str]:
        """Get network and communication related keys"""
        return {
            cls.RSSI: cls.RSSI,
            cls.ROAMING: cls.ROAMING,
            cls.NETWORK_TYPE: cls.NETWORK_TYPE,
            cls.CELL_ID: cls.CELL_ID,
            cls.LAC: cls.LAC,
            cls.MNC: cls.MNC,
            cls.MCC: cls.MCC,
            cls.NETWORK_ACCURACY: cls.NETWORK_ACCURACY
        }
    
    @classmethod
    def get_fuel_keys(cls) -> Dict[str, str]:
        """Get fuel and engine related keys"""
        return {
            cls.FUEL_LEVEL: cls.FUEL_LEVEL,
            cls.FUEL_USED: cls.FUEL_USED,
            cls.FUEL_CONSUMPTION: cls.FUEL_CONSUMPTION,
            cls.RPM: cls.RPM,
            cls.ENGINE_LOAD: cls.ENGINE_LOAD,
            cls.ENGINE_TEMP: cls.ENGINE_TEMP,
            cls.THROTTLE: cls.THROTTLE,
            cls.COOLANT_TEMP: cls.COOLANT_TEMP,
            cls.HOURS: cls.HOURS
        }
    
    @classmethod
    def get_battery_keys(cls) -> Dict[str, str]:
        """Get battery and power related keys"""
        return {
            cls.BATTERY: cls.BATTERY,
            cls.BATTERY_LEVEL: cls.BATTERY_LEVEL,
            cls.POWER: cls.POWER,
            cls.CHARGE: cls.CHARGE,
            cls.EXTERNAL_POWER: cls.EXTERNAL_POWER
        }
    
    @classmethod
    def get_odometer_keys(cls) -> Dict[str, str]:
        """Get odometer and distance related keys"""
        return {
            cls.ODOMETER: cls.ODOMETER,
            cls.ODOMETER_SERVICE: cls.ODOMETER_SERVICE,
            cls.ODOMETER_TRIP: cls.ODOMETER_TRIP,
            cls.TOTAL_DISTANCE: cls.TOTAL_DISTANCE,
            cls.DISTANCE: cls.DISTANCE,
            cls.TRIP_DISTANCE: cls.TRIP_DISTANCE
        }
    
    @classmethod
    def get_control_keys(cls) -> Dict[str, str]:
        """Get control and status related keys"""
        return {
            cls.IGNITION: cls.IGNITION,
            cls.MOTION: cls.MOTION,
            cls.ARMED: cls.ARMED,
            cls.BLOCKED: cls.BLOCKED,
            cls.LOCK: cls.LOCK,
            cls.DOOR: cls.DOOR,
            cls.DRIVER_UNIQUE_ID: cls.DRIVER_UNIQUE_ID
        }
    
    @classmethod
    def get_alarm_keys(cls) -> Dict[str, str]:
        """Get alarm and event related keys"""
        return {
            cls.ALARM: cls.ALARM,
            cls.EVENT: cls.EVENT,
            cls.STATUS: cls.STATUS,
            cls.ALARM_TYPE: cls.ALARM_TYPE,
            cls.EVENT_TYPE: cls.EVENT_TYPE
        }
    
    @classmethod
    def get_geofence_keys(cls) -> Dict[str, str]:
        """Get geofence related keys"""
        return {
            cls.GEOFENCE_IDS: cls.GEOFENCE_IDS,
            cls.GEOFENCE: cls.GEOFENCE,
            cls.GEOFENCE_ID: cls.GEOFENCE_ID
        }
    
    @classmethod
    def get_sensor_keys(cls) -> Dict[str, str]:
        """Get sensor related keys"""
        return {
            cls.TEMPERATURE: cls.TEMPERATURE,
            cls.HUMIDITY: cls.HUMIDITY,
            cls.PRESSURE: cls.PRESSURE,
            cls.LIGHT: cls.LIGHT,
            cls.PROXIMITY: cls.PROXIMITY,
            cls.ACCELERATION: cls.ACCELERATION,
            cls.GYROSCOPE: cls.GYROSCOPE,
            cls.MAGNETOMETER: cls.MAGNETOMETER
        }
    
    @classmethod
    def get_can_keys(cls) -> Dict[str, str]:
        """Get CAN bus related keys"""
        return {
            cls.CAN_DATA: cls.CAN_DATA,
            cls.OBD_SPEED: cls.OBD_SPEED,
            cls.OBD_RPM: cls.OBD_RPM,
            cls.OBD_FUEL: cls.OBD_FUEL,
            cls.OBD_TEMP: cls.OBD_TEMP
        }
    
    @classmethod
    def get_maintenance_keys(cls) -> Dict[str, str]:
        """Get maintenance related keys"""
        return {
            cls.MAINTENANCE: cls.MAINTENANCE,
            cls.SERVICE_DUE: cls.SERVICE_DUE,
            cls.OIL_LEVEL: cls.OIL_LEVEL,
            cls.TIRE_PRESSURE: cls.TIRE_PRESSURE
        }
    
    @classmethod
    def get_behavior_keys(cls) -> Dict[str, str]:
        """Get driver behavior related keys"""
        return {
            cls.HARD_ACCELERATION: cls.HARD_ACCELERATION,
            cls.HARD_BRAKING: cls.HARD_BRAKING,
            cls.HARD_TURNING: cls.HARD_TURNING,
            cls.IDLING: cls.IDLING,
            cls.OVERSPEED: cls.OVERSPEED
        }
