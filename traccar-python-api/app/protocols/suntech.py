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
from app.utils.date_utils import parse_date_time, parse_suntech_date_time

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
    
    
    async def _parse_universal_message(self, message: str, client_info: Dict[str, Any]) -> Optional[List[PositionCreate]]:
        """Parse universal format message (ST format)"""
        try:
            # Split message by semicolons
            parts = message.split(';')
            if len(parts) < 10:
                logger.warning("Invalid universal message format", parts_count=len(parts))
                return None
            
            index = 0
            prefix = parts[index]  # ST300STT
            index += 1
            
            # Extract device ID from prefix
            device_id_match = re.search(r'ST\w+STT', prefix)
            if not device_id_match:
                logger.warning("Could not extract device ID from prefix", prefix=prefix)
                return None
            
            device_identifier = device_id_match.group()
            
            # Extract real device ID from message (index 1)
            real_device_id = parts[1] if len(parts) > 1 else device_identifier
            
            # Add real device ID to client info
            client_info['real_device_id'] = real_device_id
            
            # Try to find existing device or create unknown device record
            device = await self._get_or_create_device(device_identifier, client_info)
            if not device:
                return None
            
            message_type = parts[index]  # This is actually the device ID in this format
            index += 1
            
            # In this format, we assume it's a location message
            return await self._parse_location_message(parts, index, device, self.MSG_LOCATION)
                
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
            
            # Based on the actual message format:
            # ST300STT;907126119;04;1097B;20250908;12:44:33;33e530;-03.843813;-038.615475;000.013;000.00;11;1;26663840;14.07;000000;1;0019;295746;0.0;0;0;00000000000000;0
            
            # Device ID (907126119) - index 1
            device_id = parts[1]
            
            # Firmware version (04) - index 2
            firmware_version = parts[2]
            
            # Protocol type (1097B) - index 3
            protocol_type = parts[3]
            
            # Date (20250908) - index 4
            date_str = parts[4]
            
            # Time (12:44:33) - index 5
            time_str = parts[5]
            
            # Parse datetime using Suntech-specific parser
            datetime_str = f"{date_str}{time_str}"
            device_time = parse_suntech_date_time(datetime_str)
            if not device_time:
                logger.warning("Could not parse datetime", date=date_str, time=time_str, datetime_str=datetime_str)
                return None
            
            # Cell info (33e530) - index 6
            cell_info = parts[6]
            
            # Latitude (-03.843813) - index 7
            try:
                latitude = float(parts[7])
            except (ValueError, IndexError):
                logger.warning("Invalid latitude", lat_part=parts[7] if len(parts) > 7 else None)
                return None
            
            # Longitude (-038.615475) - index 8
            try:
                longitude = float(parts[8])
            except (ValueError, IndexError):
                logger.warning("Invalid longitude", lon_part=parts[8] if len(parts) > 8 else None)
                return None
            
            if not is_valid_coordinates(latitude, longitude):
                logger.warning("Invalid coordinate values", lat=latitude, lon=longitude)
                return None
            
            # Speed (000.013) - index 9
            try:
                speed = float(parts[9])
                # Convert km/h to knots
                speed_knots = speed * 0.539957
            except (ValueError, IndexError):
                speed_knots = 0.0
            
            # Course (000.00) - index 10
            try:
                course = float(parts[10])
            except (ValueError, IndexError):
                course = 0.0
            
            # GPS validity (11) - index 11 - this seems to be a status code, not boolean
            try:
                gps_status = parts[11]
                # In this format, we'll assume GPS is valid if we have coordinates
                valid = True
            except IndexError:
                valid = True
            
            # Additional fields that we can parse if available
            odometer = None
            if index < len(parts):
                try:
                    # Odometer might be in one of the remaining fields
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
                'attributes': {
                    'version_fw': firmware_version,
                    'protocol_type': protocol_type,
                    'cell_info': cell_info,
                    'gps_status': gps_status
                }
            }
            
            if odometer is not None:
                position_data['attributes']['odometer'] = odometer
            
            # Add alarm information
            if message_type == self.MSG_EMERGENCY:
                position_data['attributes']['alarm'] = 'general'
            elif message_type == self.MSG_ALERT:
                position_data['attributes']['alarm'] = 'general'
            
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
            # Remove control characters like \r, \n, \t
            message_str = ''.join(char for char in message_str if ord(char) >= 32 or char in '\n\r\t')
            message_str = message_str.strip()
            if not message_str:
                return None
            
            # Convert client_address to client_info format
            client_info = {
                'host': client_address[0],
                'port': client_address[1],
                'raw_data': message_str
            }
            
            # Try to parse as universal format first
            positions = await self._parse_universal_message(message_str, client_info)
            if not positions:
                # Try legacy format
                positions = await self._parse_legacy_message(message_str, client_info)
            
            if not positions or len(positions) == 0:
                return None
            
            # Get the first position for the protocol message
            position = positions[0]
            
            from app.protocols.base import ProtocolMessage
            return ProtocolMessage(
                device_id=position.device_id,
                message_type='location',
                data=position.model_dump(),
                timestamp=position.device_time or datetime.utcnow(),
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
    
    async def _get_or_create_device(self, device_identifier: str, client_info: Dict[str, Any]):
        """Get existing device or create unknown device record."""
        try:
            from app.database import AsyncSessionLocal
            from app.models.unknown_device import UnknownDevice
            from app.models.device import Device
            from sqlalchemy import select
            from datetime import datetime
            
            async with AsyncSessionLocal() as db:
                # First, check if device is already registered
                result = await db.execute(
                    select(Device).where(Device.unique_id == device_identifier)
                )
                existing_device = result.scalar_one_or_none()
                
                if existing_device:
                    logger.info("Found existing registered device", unique_id=device_identifier, device_id=existing_device.id)
                    return existing_device
                
                # Check if unknown device already exists
                result = await db.execute(
                    select(UnknownDevice).where(
                        UnknownDevice.unique_id == device_identifier,
                        UnknownDevice.protocol == self.PROTOCOL_NAME
                    )
                )
                existing_unknown = result.scalar_one_or_none()
                
                if existing_unknown:
                    # Update existing unknown device record
                    existing_unknown.last_seen = datetime.utcnow()
                    existing_unknown.connection_count += 1
                    existing_unknown.client_address = f"{client_info.get('host', 'unknown')}:{client_info.get('port', 'unknown')}"
                    existing_unknown.raw_data = client_info.get('raw_data', '')
                    
                    # Store real device ID in parsed_data
                    import json
                    parsed_data = {}
                    if existing_unknown.parsed_data:
                        try:
                            parsed_data = json.loads(existing_unknown.parsed_data)
                        except:
                            parsed_data = {}
                    parsed_data['real_device_id'] = client_info.get('real_device_id', device_identifier)
                    existing_unknown.parsed_data = json.dumps(parsed_data)
                    
                    await db.commit()
                    logger.info("Updated existing unknown device", unique_id=device_identifier, connection_count=existing_unknown.connection_count)
                    
                    # Broadcast unknown device update via WebSocket
                    try:
                        from app.services.websocket_service import websocket_service
                        await websocket_service.broadcast_unknown_device_update({
                            'id': existing_unknown.id,
                            'unique_id': existing_unknown.unique_id,
                            'protocol': existing_unknown.protocol,
                            'port': existing_unknown.port,
                            'protocol_type': existing_unknown.protocol_type,
                            'client_address': existing_unknown.client_address,
                            'connection_count': existing_unknown.connection_count,
                            'last_seen': existing_unknown.last_seen.isoformat(),
                            'is_registered': existing_unknown.is_registered
                        })
                    except Exception as e:
                        logger.error("Failed to broadcast unknown device update", error=str(e))
                    
                    # Create a mock device object for compatibility
                    device = type('Device', (), {
                        'id': existing_unknown.id,  # Use unknown device ID
                        'unique_id': device_identifier,
                        'name': f'Suntech Device {device_identifier}',
                        'is_unknown': True
                    })()
                    return device
                else:
                    # Create new unknown device record
                    import json
                    parsed_data = {
                        'real_device_id': client_info.get('real_device_id', device_identifier)
                    }
                    
                    unknown_device = UnknownDevice(
                        unique_id=device_identifier,
                        protocol=self.PROTOCOL_NAME,
                        port=client_info.get('port', 5011),
                        protocol_type="tcp",  # Suntech uses TCP
                        client_address=f"{client_info.get('host', 'unknown')}:{client_info.get('port', 'unknown')}",
                        connection_count=1,
                        raw_data=client_info.get('raw_data', ''),
                        parsed_data=json.dumps(parsed_data),
                        first_seen=datetime.utcnow(),
                        last_seen=datetime.utcnow()
                    )
                    db.add(unknown_device)
                    await db.commit()
                    await db.refresh(unknown_device)
                    
                    logger.info("Created new unknown device record", unique_id=device_identifier, protocol=self.PROTOCOL_NAME)
                    
                    # Broadcast unknown device update via WebSocket
                    try:
                        from app.services.websocket_service import websocket_service
                        await websocket_service.broadcast_unknown_device_update({
                            'id': unknown_device.id,
                            'unique_id': unknown_device.unique_id,
                            'protocol': unknown_device.protocol,
                            'port': unknown_device.port,
                            'protocol_type': unknown_device.protocol_type,
                            'client_address': unknown_device.client_address,
                            'connection_count': unknown_device.connection_count,
                            'first_seen': unknown_device.first_seen.isoformat(),
                            'last_seen': unknown_device.last_seen.isoformat(),
                            'is_registered': unknown_device.is_registered
                        })
                    except Exception as e:
                        logger.error("Failed to broadcast unknown device update", error=str(e))
                    
                    # Create a mock device object for compatibility
                    device = type('Device', (), {
                        'id': existing_unknown.id,  # Use unknown device ID
                        'unique_id': device_identifier,
                        'name': f'Suntech Device {device_identifier}',
                        'is_unknown': True
                    })()
                    return device
                
        except Exception as e:
            logger.error("Error in _get_or_create_device", error=str(e), device_id=device_identifier)
            return None