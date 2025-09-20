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
            
            # The real device identifier is in parts[1] (907126119), not the prefix
            if len(parts) > 1:
                device_identifier = parts[1]  # Use the numeric device ID from the message
                logger.info("Using device ID from message", device_id=device_identifier, prefix=prefix)
            else:
                # Fallback to prefix parsing if needed
                device_id_match = re.search(r'ST\w+STT', prefix)
                if device_id_match:
                    device_identifier = device_id_match.group()
                elif prefix.isdigit():
                    device_identifier = prefix
                else:
                    logger.warning("Could not extract device ID from message", prefix=prefix, parts=parts)
                    return None
            
            # Add device info to client info
            client_info['real_device_id'] = device_identifier
            client_info['device_prefix'] = prefix
            
            # Try to find existing device or create unknown device record
            device = await self._get_or_create_device(device_identifier, client_info)
            if not device:
                return None
            
            # Skip the device ID part since we already used it
            # index is already 1 at this point
            
            # In this format, we assume it's a location message
            return await self._parse_location_message(parts, index, device, self.MSG_LOCATION, client_info)
                
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
            
            # Parse latitude and longitude from the message
            # Based on the message format: LOGTEST9;111222333;04;1097B;20250908;12:44:33;33e530;-03.843813;-038.615475;...
            try:
                if len(parts) >= 8:
                    latitude = float(parts[7])
                    longitude = float(parts[8])
                    position_data['latitude'] = latitude
                    position_data['longitude'] = longitude
                    logger.info("Legacy parser: parsed coordinates", lat=latitude, lon=longitude)
                else:
                    logger.warning("Legacy parser: insufficient parts for coordinates", parts_count=len(parts))
                    return None
            except (ValueError, IndexError) as e:
                logger.error("Legacy parser: failed to parse coordinates", error=str(e), parts=parts)
                return None
            
            return [PositionCreate(**position_data)]
            
        except Exception as e:
            logger.error("Error parsing legacy message", error=str(e), message=message)
            return None
    
    async def _parse_location_message(self, parts: List[str], start_index: int, device: Device, message_type: str, client_info: Dict[str, Any] = None) -> Optional[List[PositionCreate]]:
        """Parse location-type message"""
        try:
            # Based on the actual message format:
            # ST300STT;907126119;04;1097B;20250908;12:44:33;33e530;-03.843813;-038.615475;000.013;000.00;11;1;26663840;14.07;000000;1;0019;295746;0.0;0;0;00000000000000;0
            # Indexes:  0       1        2  3    4        5        6      7          8           9       10     11 12 13      14   15     16 17   18     19  20 21 22             23
            
            # Device ID (907126119) - already processed in start_index-1
            device_id = parts[1]
            
            # Firmware version (04) - index 2
            firmware_version = parts[2]
            
            # Protocol type (1097B) - index 3
            protocol_type = parts[3]
            
            # Date (20250908) - index 4
            date_str = parts[4]
            
            # Time (12:44:33) - index 5
            time_str = parts[5]
            
            # Parse datetime
            datetime_str = f"{date_str}{time_str}"
            try:
                from datetime import datetime
                device_time = datetime.strptime(datetime_str, "%Y%m%d%H:%M:%S")
            except ValueError:
                logger.warning("Could not parse datetime", date=date_str, time=time_str, datetime_str=datetime_str)
                return None
            
            # Cell info (33e530) - index 6
            cell_info = parts[6]
            
            # Latitude (-03.843813) - index 7
            try:
                latitude = float(parts[7])
                logger.info("Parsed latitude", latitude=latitude, raw=parts[7])
            except (ValueError, IndexError):
                logger.warning("Invalid latitude", lat_part=parts[7] if len(parts) > 7 else None)
                return None
            
            # Longitude (-038.615475) - index 8
            try:
                longitude = float(parts[8])
                logger.info("Parsed longitude", longitude=longitude, raw=parts[8])
            except (ValueError, IndexError):
                logger.warning("Invalid longitude", lon_part=parts[8] if len(parts) > 8 else None)
                return None
            
            # Validate coordinates
            if latitude == 0.0 and longitude == 0.0:
                logger.warning("Invalid coordinate values (0,0)", lat=latitude, lon=longitude)
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
            
            # GPS validity and satellites (11) - index 11
            try:
                satellites = int(parts[11])
                valid = satellites > 0  # GPS is valid if we have satellites
            except (ValueError, IndexError):
                satellites = 0
                valid = True  # Assume valid if we have coordinates
            
            # GPS status (1) - index 12
            try:
                gps_fix = int(parts[12])
                if gps_fix == 0:
                    valid = False  # No GPS fix
            except (ValueError, IndexError):
                gps_fix = 1
            
            # Odometer (26663840) - index 13
            try:
                odometer = int(parts[13])
            except (ValueError, IndexError):
                odometer = None
            
            # Power voltage (14.07) - index 14
            try:
                power_voltage = float(parts[14])
            except (ValueError, IndexError):
                power_voltage = None
            
            # IO Status (000000) - index 15
            # This contains ignition and other digital inputs/outputs
            io_status = None
            ignition = None
            try:
                io_status = parts[15]
                if len(io_status) >= 1:
                    # First bit is typically ignition
                    ignition = io_status[0] == '1'
            except (ValueError, IndexError):
                pass
            
            # Mode (1) - index 16
            try:
                mode = int(parts[16])
            except (ValueError, IndexError):
                mode = None
            
            # Message number (0019) - index 17
            try:
                message_number = int(parts[17])
            except (ValueError, IndexError):
                message_number = None
            
            # Create position object
            position_data = {
                'device_id': device.unique_id if hasattr(device, 'unique_id') else device.id,
                'protocol': self.PROTOCOL_NAME,
                'server_time': datetime.utcnow(),
                'device_time': device_time,
                'fix_time': device_time,  # Use device time as fix time
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
                    'satellites': satellites,
                    'gps_fix': gps_fix,
                    'real_device_id': client_info.get('real_device_id', device.unique_id) if client_info else device.unique_id,
                    'device_prefix': client_info.get('device_prefix', 'ST300STT') if client_info else 'ST300STT'
                }
            }
            
            # Add optional attributes
            if odometer is not None:
                position_data['attributes']['odometer'] = odometer
                
            if power_voltage is not None:
                position_data['attributes']['power'] = power_voltage
                position_data['attributes']['battery'] = power_voltage  # Same as power for now
                
            if io_status is not None:
                position_data['attributes']['io'] = io_status
                
            if ignition is not None:
                position_data['attributes']['ignition'] = ignition
                
            if mode is not None:
                position_data['attributes']['mode'] = mode
                
            if message_number is not None:
                position_data['attributes']['message_number'] = message_number
            
            # Add alarm information
            if message_type == self.MSG_EMERGENCY:
                position_data['attributes']['alarm'] = 'general'
            elif message_type == self.MSG_ALERT:
                position_data['attributes']['alarm'] = 'general'
            
            logger.info("Position data created", 
                       device_id=device.id, 
                       lat=latitude, 
                       lon=longitude, 
                       ignition=ignition,
                       valid=valid,
                       satellites=satellites,
                       power=power_voltage,
                       odometer=odometer,
                       attributes=position_data['attributes'])
            
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
    
    async def parse_message(self, data: bytes, client_address: Tuple[str, int]) -> Optional[Any]:
        """
        Parse incoming Suntech message data.
        
        Args:
            data: Raw message data
            client_address: Client address tuple (host, port)
            
        Returns:
            Parsed ProtocolMessage or None if invalid
        """
        try:
            logger.info("Suntech protocol received data", 
                       client_address=client_address, 
                       data_length=len(data),
                       raw_data=data[:100],  # First 100 bytes for debugging
                       raw_hex=data[:100].hex())  # Hex representation for debugging
            
            message_str = data.decode('utf-8', errors='ignore').strip()
            
            # Log original message before cleaning
            logger.info("Suntech protocol original message", 
                       client_address=client_address,
                       original_message=repr(message_str))
            
            # Remove control characters like \r, \n, \t
            message_str = ''.join(char for char in message_str if ord(char) >= 32 or char in '\n\r\t')
            message_str = message_str.strip()
            
            logger.info("Suntech protocol cleaned message", 
                       client_address=client_address,
                       cleaned_message=message_str,
                       message_length=len(message_str))
            
            if not message_str:
                logger.warning("Suntech protocol: empty message after decoding")
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
                data=position.dict(),
                timestamp=position.device_time or datetime.utcnow(),
                raw_data=data,
                valid=True
            )
            
        except Exception as e:
            logger.error("Error parsing Suntech message", error=str(e), data=data)
            return None
    
    async def create_position(self, message: Any) -> Optional[Dict[str, Any]]:
        """
        Create position data from parsed Suntech message.
        
        Args:
            message: Parsed protocol message containing position data
            
        Returns:
            Position data dictionary or None
        """
        try:
            if not hasattr(message, 'data') or not message.data:
                logger.warning("Message has no data attribute")
                return None
                
            data = message.data
            
            # Extract position data from the parsed message
            position_data = {
                'device_id': message.device_id,
                'protocol': self.PROTOCOL_NAME,
                'server_time': datetime.utcnow(),
                'device_time': data.get('device_time'),
                'fix_time': data.get('fix_time'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'altitude': data.get('altitude', 0.0),
                'speed': data.get('speed', 0.0),
                'course': data.get('course', 0.0),
                'valid': data.get('valid', True),
                'attributes': data.get('attributes', {})
            }
            
            logger.info("Position data created from message", 
                       device_id=message.device_id,
                       attributes=position_data['attributes'])
            
            return position_data
            
        except Exception as e:
            logger.error("Error creating position from Suntech message", error=str(e))
            return None
    
    async def create_events(self, message: Any) -> List[Dict[str, Any]]:
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
                        'id': existing_unknown.id,  # Use existing unknown device ID
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
                        'id': unknown_device.id,  # Use new unknown device ID
                        'unique_id': device_identifier,
                        'name': f'Suntech Device {device_identifier}',
                        'is_unknown': True
                    })()
                    return device
                
        except Exception as e:
            logger.error("Error in _get_or_create_device", error=str(e), device_id=device_identifier)
            return None