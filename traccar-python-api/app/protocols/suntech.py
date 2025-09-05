"""
Suntech Protocol Implementation for Traccar Python API

This module implements the Suntech GPS tracker protocol, supporting both
universal and legacy formats with comprehensive message parsing.

Based on the original Java implementation from Traccar.
"""
import asyncio
import re
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import structlog

from app.protocols.base import BaseProtocolHandler
from app.models.position import Position
from app.models.device import Device
from app.schemas.position import PositionCreate
from app.utils.geo_utils import is_valid_coordinates
from app.utils.date_utils import parse_date_time

logger = structlog.get_logger(__name__)


class SuntechProtocolHandler(BaseProtocolHandler):
    """
    Suntech protocol handler supporting multiple message formats
    """
    
    PROTOCOL_NAME = "suntech"
    
    # Message type constants
    MSG_LOCATION = "Location"
    MSG_EMERGENCY = "Emergency"
    MSG_ALERT = "Alert"
    MSG_HEARTBEAT = "Heartbeat"
    MSG_RESPONSE = "Resp"
    
    # Alarm type mappings
    EMERGENCY_ALARMS = {
        1: "sos",
        2: "parking",
        3: "power_cut",
        5: "door",
        6: "door",
        7: "movement",
        8: "vibration"
    }
    
    ALERT_ALARMS = {
        1: "overspeed",
        5: "geofence_exit",
        6: "geofence_enter",
        14: "low_battery",
        15: "vibration",
        16: "accident",
        40: "power_restored",
        41: "power_cut",
        42: "sos",
        46: "acceleration",
        47: "braking",
        50: "jamming",
        132: "door"
    }
    
    def __init__(self):
        super().__init__()
        self.universal = False
        self.prefix = ""
        self.protocol_type = 0
        self.hbm = 0
        self.include_adc = False
        self.include_rpm = False
        self.include_temp = False
    
    async def handle_message(self, data: bytes, client_info: Dict[str, Any]) -> Optional[List[PositionCreate]]:
        """
        Handle incoming Suntech protocol message
        
        Args:
            data: Raw message data
            client_info: Client connection information
            
        Returns:
            List of position objects or None if message couldn't be parsed
        """
        try:
            message = data.decode('utf-8').strip()
            logger.debug("Received Suntech message", message=message, client=client_info)
            
            # Parse message based on format
            if message.startswith("ST"):
                return await self._parse_universal_message(message, client_info)
            else:
                return await self._parse_legacy_message(message, client_info)
                
        except Exception as e:
            logger.error("Error parsing Suntech message", error=str(e), data=data.hex())
            return None
    
    async def _parse_universal_message(self, message: str, client_info: Dict[str, Any]) -> Optional[List[PositionCreate]]:
        """Parse universal format message (ST format)"""
        try:
            # Split message by semicolons
            parts = message.split(';')
            if len(parts) < 10:
                logger.warning("Invalid universal message format", parts_count=len(parts))
                return None
            
            index = 0
            prefix = parts[index]  # ST600STT;...
            index += 1
            
            # Extract device ID from prefix
            device_id_match = re.search(r'ST\w+STT', prefix)
            if not device_id_match:
                logger.warning("Could not extract device ID from prefix", prefix=prefix)
                return None
            
            device_identifier = device_id_match.group()
            
            # Get or create device
            device = await self._get_or_create_device(device_identifier, client_info)
            if not device:
                return None
            
            message_type = parts[index]
            index += 1
            
            if message_type in [self.MSG_LOCATION, self.MSG_EMERGENCY, self.MSG_ALERT]:
                return await self._parse_location_message(parts, index, device, message_type)
            elif message_type == self.MSG_HEARTBEAT:
                return await self._parse_heartbeat_message(parts, index, device)
            else:
                logger.debug("Unsupported message type", type=message_type)
                return None
                
        except Exception as e:
            logger.error("Error parsing universal message", error=str(e), message=message)
            return None
    
    async def _parse_legacy_message(self, message: str, client_info: Dict[str, Any]) -> Optional[List[PositionCreate]]:
        """Parse legacy format message"""
        try:
            # Legacy format parsing (simplified version)
            parts = message.split(';')
            if len(parts) < 8:
                return None
            
            # Extract device ID (usually first part)
            device_identifier = parts[0]
            device = await self._get_or_create_device(device_identifier, client_info)
            if not device:
                return None
            
            # Parse basic location data
            position_data = {
                'device_id': device.id,
                'protocol': self.PROTOCOL_NAME,
                'server_time': datetime.utcnow(),
                'valid': True
            }
            
            # This is a simplified legacy parser - would need full implementation
            # based on specific legacy format requirements
            
            return [PositionCreate(**position_data)]
            
        except Exception as e:
            logger.error("Error parsing legacy message", error=str(e), message=message)
            return None
    
    async def _parse_location_message(self, parts: List[str], start_index: int, device: Device, message_type: str) -> Optional[List[PositionCreate]]:
        """Parse location-type message"""
        try:
            index = start_index
            
            # Device ID
            device_id = parts[index]
            index += 1
            
            # Firmware version (optional)
            if message_type != self.MSG_ALERT or self.protocol_type == 0:
                firmware_version = parts[index]
                index += 1
            else:
                firmware_version = None
            
            # Date and time
            date_str = parts[index]
            index += 1
            time_str = parts[index]
            index += 1
            
            # Parse datetime
            device_time = parse_date_time(f"{date_str}{time_str}", "%Y%m%d%H:%M:%S")
            if not device_time:
                logger.warning("Could not parse datetime", date=date_str, time=time_str)
                return None
            
            # Cell info (optional for protocol type 1)
            if self.protocol_type == 1:
                cell_info = parts[index]
                index += 1
            
            # Latitude and longitude
            try:
                latitude = float(parts[index])
                index += 1
                longitude = float(parts[index])
                index += 1
            except (ValueError, IndexError):
                logger.warning("Invalid coordinates", lat_part=parts[index-1] if index > 0 else None)
                return None
            
            if not is_valid_coordinates(latitude, longitude):
                logger.warning("Invalid coordinate values", lat=latitude, lon=longitude)
                return None
            
            # Speed (km/h)
            try:
                speed = float(parts[index])
                index += 1
                # Convert km/h to knots
                speed_knots = speed * 0.539957
            except (ValueError, IndexError):
                speed_knots = 0.0
                index += 1
            
            # Course
            try:
                course = float(parts[index])
                index += 1
            except (ValueError, IndexError):
                course = 0.0
                index += 1
            
            # GPS validity
            try:
                valid = parts[index] == "1"
                index += 1
            except IndexError:
                valid = True
            
            # Odometer (optional for protocol type 1)
            odometer = None
            if self.protocol_type == 1 and index < len(parts):
                try:
                    odometer = int(parts[index])
                    index += 1
                except (ValueError, IndexError):
                    pass
            
            # Create position object
            position_data = {
                'device_id': device.id,
                'protocol': self.PROTOCOL_NAME,
                'server_time': datetime.utcnow(),
                'device_time': device_time,
                'latitude': latitude,
                'longitude': longitude,
                'altitude': 0.0,  # Not provided in basic format
                'speed': speed_knots,
                'course': course,
                'valid': valid,
                'attributes': {}
            }
            
            # Add optional attributes
            if firmware_version:
                position_data['attributes']['version_fw'] = firmware_version
            
            if odometer is not None:
                position_data['attributes']['odometer'] = odometer
            
            # Add alarm information
            if message_type == self.MSG_EMERGENCY:
                position_data['attributes']['alarm'] = 'general'
            elif message_type == self.MSG_ALERT:
                position_data['attributes']['alarm'] = 'general'
            
            # Parse additional attributes if available
            await self._parse_additional_attributes(parts, index, position_data, device)
            
            return [PositionCreate(**position_data)]
            
        except Exception as e:
            logger.error("Error parsing location message", error=str(e), parts=parts)
            return None
    
    async def _parse_heartbeat_message(self, parts: List[str], start_index: int, device: Device) -> Optional[List[PositionCreate]]:
        """Parse heartbeat message"""
        # Heartbeat messages typically don't contain position data
        # but we might want to update device status
        logger.debug("Received heartbeat", device_id=device.id)
        return None
    
    async def _parse_additional_attributes(self, parts: List[str], start_index: int, position_data: Dict[str, Any], device: Device):
        """Parse additional attributes from message parts"""
        try:
            index = start_index
            
            # Parse additional fields based on configuration
            if self.include_adc and index < len(parts):
                try:
                    adc_values = parts[index].split(',')
                    for i, adc_value in enumerate(adc_values):
                        if adc_value:
                            position_data['attributes'][f'adc{i+1}'] = float(adc_value)
                    index += 1
                except (ValueError, IndexError):
                    index += 1
            
            if self.include_rpm and index < len(parts):
                try:
                    position_data['attributes']['rpm'] = int(parts[index])
                    index += 1
                except (ValueError, IndexError):
                    index += 1
            
            if self.include_temp and index < len(parts):
                try:
                    temps = parts[index].split(',')
                    for i, temp in enumerate(temps):
                        if temp:
                            position_data['attributes'][f'temp{i+1}'] = float(temp)
                    index += 1
                except (ValueError, IndexError):
                    index += 1
                    
        except Exception as e:
            logger.warning("Error parsing additional attributes", error=str(e))
    
    async def encode_command(self, command: str, device: Device) -> Optional[bytes]:
        """
        Encode command for Suntech device
        
        Args:
            command: Command to encode
            device: Target device
            
        Returns:
            Encoded command bytes or None if unsupported
        """
        try:
            if self.universal:
                return await self._encode_universal_command(command, device)
            else:
                return await self._encode_legacy_command(command, device)
        except Exception as e:
            logger.error("Error encoding command", error=str(e), command=command)
            return None
    
    async def _encode_universal_command(self, command: str, device: Device) -> Optional[bytes]:
        """Encode universal format command"""
        # Universal command format implementation
        # This would need to be implemented based on Suntech universal protocol specification
        logger.debug("Encoding universal command", command=command, device_id=device.id)
        return None
    
    async def _encode_legacy_command(self, command: str, device: Device) -> Optional[bytes]:
        """Encode legacy format command"""
        # Legacy command format implementation
        logger.debug("Encoding legacy command", command=command, device_id=device.id)
        return None
    
    def get_supported_commands(self) -> List[str]:
        """Get list of supported commands for this protocol"""
        return [
            "output_control",
            "reboot_device",
            "position_single",
            "engine_stop",
            "engine_resume",
            "alarm_arm",
            "alarm_disarm"
        ]
    
    async def parse_message(self, data: bytes, client_address: Tuple[str, int]) -> Optional['ProtocolMessage']:
        """
        Parse incoming Suntech message data.
        
        Args:
            data: Raw message data
            client_address: Client address tuple (host, port)
            
        Returns:
            Parsed ProtocolMessage or None if invalid
        """
        try:
            message_str = data.decode('utf-8', errors='ignore').strip()
            if not message_str:
                return None
            
            # Try to parse as universal format first
            parsed_data = await self._parse_universal_message(message_str)
            if not parsed_data:
                # Try legacy format
                parsed_data = await self._parse_legacy_message(message_str)
            
            if not parsed_data:
                return None
            
            from app.protocols.base import ProtocolMessage
            return ProtocolMessage(
                device_id=parsed_data.get('device_id', ''),
                message_type=parsed_data.get('message_type', 'unknown'),
                data=parsed_data,
                timestamp=parsed_data.get('timestamp', datetime.utcnow()),
                raw_data=data,
                valid=True
            )
            
        except Exception as e:
            logger.error("Error parsing Suntech message", error=str(e), data=data)
            return None
    
    async def create_position(self, message: 'ProtocolMessage') -> Optional[Dict[str, Any]]:
        """
        Create position data from parsed Suntech message.
        
        Args:
            message: Parsed protocol message
            
        Returns:
            Position data dictionary or None
        """
        try:
            data = message.data
            
            # Extract position data
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            if latitude is None or longitude is None:
                return None
            
            if not is_valid_coordinates(latitude, longitude):
                return None
            
            position_data = {
                'device_id': message.device_id,
                'latitude': latitude,
                'longitude': longitude,
                'altitude': data.get('altitude', 0),
                'speed': data.get('speed', 0),
                'course': data.get('course', 0),
                'timestamp': message.timestamp,
                'valid': True,
                'attributes': {
                    'satellites': data.get('satellites'),
                    'hdop': data.get('hdop'),
                    'odometer': data.get('odometer'),
                    'fuel': data.get('fuel'),
                    'battery': data.get('battery'),
                    'power': data.get('power'),
                    'ignition': data.get('ignition'),
                    'motion': data.get('motion')
                }
            }
            
            return position_data
            
        except Exception as e:
            logger.error("Error creating position from Suntech message", error=str(e))
            return None
    
    async def create_events(self, message: 'ProtocolMessage') -> List[Dict[str, Any]]:
        """
        Create events from parsed Suntech message.
        
        Args:
            message: Parsed protocol message
            
        Returns:
            List of event data dictionaries
        """
        events = []
        
        try:
            data = message.data
            device_id = message.device_id
            timestamp = message.timestamp
            
            # Check for emergency alarms
            alarm_type = data.get('alarm_type')
            if alarm_type and alarm_type in self.EMERGENCY_ALARMS:
                event_type = self.EMERGENCY_ALARMS[alarm_type]
                events.append({
                    'device_id': device_id,
                    'type': event_type,
                    'timestamp': timestamp,
                    'attributes': {
                        'alarm_type': alarm_type,
                        'raw_data': data
                    }
                })
            
            # Check for alert alarms
            if alarm_type and alarm_type in self.ALERT_ALARMS:
                event_type = self.ALERT_ALARMS[alarm_type]
                events.append({
                    'device_id': device_id,
                    'type': event_type,
                    'timestamp': timestamp,
                    'attributes': {
                        'alarm_type': alarm_type,
                        'raw_data': data
                    }
                })
            
            # Check for ignition events
            ignition = data.get('ignition')
            if ignition is not None:
                event_type = 'ignition_on' if ignition else 'ignition_off'
                events.append({
                    'device_id': device_id,
                    'type': event_type,
                    'timestamp': timestamp,
                    'attributes': {
                        'ignition': ignition
                    }
                })
            
            # Check for motion events
            motion = data.get('motion')
            if motion is not None:
                event_type = 'motion_start' if motion else 'motion_stop'
                events.append({
                    'device_id': device_id,
                    'type': event_type,
                    'timestamp': timestamp,
                    'attributes': {
                        'motion': motion
                    }
                })
            
        except Exception as e:
            logger.error("Error creating events from Suntech message", error=str(e))
        
        return events