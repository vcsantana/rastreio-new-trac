"""
OsmAnd Protocol Implementation for Traccar Python API

This module implements the OsmAnd mobile protocol for Android/iOS devices,
supporting both query string and JSON payload formats.

Based on the original Java implementation from Traccar.
Port: 5055 (HTTP)
"""
import asyncio
import json
import re
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import parse_qs, urlparse
import structlog

from app.protocols.base import BaseProtocolHandler, ProtocolMessage
from app.models.position import Position
from app.models.device import Device
from app.schemas.position import PositionCreate
from app.utils.geo_utils import is_valid_coordinates
from app.utils.date_utils import parse_date_time

logger = structlog.get_logger(__name__)


class OsmAndProtocolHandler(BaseProtocolHandler):
    """
    OsmAnd protocol handler for mobile devices (Android/iOS)
    Supports both query string and JSON payload formats
    """
    
    PROTOCOL_NAME = "osmand"
    SUPPORTED_MESSAGE_TYPES = ["location", "event", "heartbeat"]
    
    def __init__(self):
        super().__init__()
        self.content_type = None
    
    async def parse_message(self, data: bytes, client_address: Tuple[str, int]) -> Optional[ProtocolMessage]:
        """
        Parse incoming HTTP message from mobile device
        
        Args:
            data: Raw HTTP request data
            client_address: Client address tuple (host, port)
            
        Returns:
            Parsed ProtocolMessage or None if invalid
        """
        try:
            # Decode HTTP request
            request_str = data.decode('utf-8', errors='ignore')
            lines = request_str.split('\r\n')
            
            if not lines:
                return None
            
            # Parse HTTP headers
            request_line = lines[0]
            headers = {}
            body_start = 0
            
            for i, line in enumerate(lines[1:], 1):
                if line == '':
                    body_start = i + 1
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()
            
            # Extract body
            body = '\r\n'.join(lines[body_start:]) if body_start < len(lines) else ''
            
            # Determine content type
            self.content_type = headers.get('content-type', '')
            
            # Parse based on content type
            if 'application/json' in self.content_type:
                return await self._parse_json_message(body, client_address, headers)
            else:
                return await self._parse_query_message(request_line, body, client_address, headers)
                
        except Exception as e:
            logger.error("Failed to parse OsmAnd message", error=str(e), client=client_address)
            return None
    
    async def _parse_query_message(self, request_line: str, body: str, 
                                 client_address: Tuple[str, int], headers: Dict[str, str]) -> Optional[ProtocolMessage]:
        """Parse query string format message"""
        try:
            # Extract URL from request line
            parts = request_line.split(' ')
            if len(parts) < 2:
                return None
            
            url = parts[1]
            parsed_url = urlparse(url)
            
            # Parse query parameters
            query_params = parse_qs(parsed_url.query)
            
            # If no query params in URL, try body
            if not query_params and body:
                query_params = parse_qs(body)
            
            if not query_params:
                return None
            
            # Extract device ID
            device_id = None
            for key in ['id', 'deviceid', 'device_id']:
                if key in query_params and query_params[key]:
                    device_id = query_params[key][0]
                    break
            
            if not device_id:
                logger.warning("No device ID found in OsmAnd query message", client=client_address)
                return None
            
            # Create protocol message
            message_data = {
                'device_id': device_id,
                'query_params': query_params,
                'headers': headers,
                'client_address': client_address
            }
            
            return ProtocolMessage(
                device_id=device_id,
                message_type="location",
                data=message_data,
                timestamp=datetime.utcnow(),
                raw_data=json.dumps(query_params).encode(),
                valid=True
            )
            
        except Exception as e:
            logger.error("Failed to parse OsmAnd query message", error=str(e))
            return None
    
    async def _parse_json_message(self, body: str, client_address: Tuple[str, int], 
                                headers: Dict[str, str]) -> Optional[ProtocolMessage]:
        """Parse JSON format message"""
        try:
            if not body:
                return None
            
            json_data = json.loads(body)
            
            # Extract device ID
            device_id = json_data.get('device_id') or json_data.get('deviceid') or json_data.get('id')
            
            if not device_id:
                logger.warning("No device ID found in OsmAnd JSON message", client=client_address)
                return None
            
            # Create protocol message
            message_data = {
                'device_id': device_id,
                'json_data': json_data,
                'headers': headers,
                'client_address': client_address
            }
            
            return ProtocolMessage(
                device_id=device_id,
                message_type="location",
                data=message_data,
                timestamp=datetime.utcnow(),
                raw_data=body.encode(),
                valid=True
            )
            
        except Exception as e:
            logger.error("Failed to parse OsmAnd JSON message", error=str(e))
            return None
    
    async def create_position(self, message: ProtocolMessage) -> Optional[Dict[str, Any]]:
        """
        Create position data from parsed OsmAnd message
        
        Args:
            message: Parsed protocol message
            
        Returns:
            Position data dictionary or None
        """
        try:
            data = message.data
            
            if 'query_params' in data:
                return await self._create_position_from_query(data['query_params'], message.device_id)
            elif 'json_data' in data:
                return await self._create_position_from_json(data['json_data'], message.device_id)
            else:
                return None
                
        except Exception as e:
            logger.error("Failed to create position from OsmAnd message", error=str(e))
            return None
    
    async def _create_position_from_query(self, params: Dict[str, List[str]], device_id: str) -> Optional[Dict[str, Any]]:
        """Create position from query parameters"""
        try:
            position_data = {
                'device_id': device_id,  # Add device_id for PositionCreate
                'protocol': self.PROTOCOL_NAME,
                'valid': True,
                'attributes': {}
            }
            
            # Helper function to get first value
            def get_param(key: str, default=None):
                return params.get(key, [default])[0] if params.get(key) else default
            
            # Parse coordinates
            lat = get_param('lat')
            lon = get_param('lon')
            
            if lat and lon:
                try:
                    position_data['latitude'] = float(lat)
                    position_data['longitude'] = float(lon)
                    
                    if not is_valid_coordinates(position_data['latitude'], position_data['longitude']):
                        position_data['valid'] = False
                except ValueError:
                    position_data['valid'] = False
            
            # Parse timestamp
            timestamp = get_param('timestamp')
            if timestamp:
                try:
                    # Try different timestamp formats
                    if timestamp.isdigit():
                        # Unix timestamp
                        if len(timestamp) == 10:
                            position_data['device_time'] = datetime.fromtimestamp(int(timestamp))
                        elif len(timestamp) == 13:
                            position_data['device_time'] = datetime.fromtimestamp(int(timestamp) / 1000)
                    else:
                        # ISO format
                        position_data['device_time'] = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except (ValueError, OSError):
                    pass
            
            # Parse speed
            speed = get_param('speed')
            if speed:
                try:
                    position_data['speed'] = float(speed) * 1.94384  # Convert m/s to knots
                except ValueError:
                    pass
            
            # Parse course
            course = get_param('course') or get_param('heading')
            if course:
                try:
                    position_data['course'] = float(course)
                except ValueError:
                    pass
            
            # Parse altitude
            altitude = get_param('altitude') or get_param('alt')
            if altitude:
                try:
                    position_data['altitude'] = float(altitude)
                except ValueError:
                    pass
            
            # Parse accuracy
            accuracy = get_param('accuracy') or get_param('acc')
            if accuracy:
                try:
                    position_data['attributes']['accuracy'] = float(accuracy)
                except ValueError:
                    pass
            
            # Parse battery
            battery = get_param('battery')
            if battery:
                try:
                    position_data['attributes']['battery'] = float(battery)
                except ValueError:
                    pass
            
            # Parse valid flag
            valid = get_param('valid')
            if valid:
                position_data['valid'] = valid.lower() in ['true', '1', 'yes']
            
            # Parse motion
            motion = get_param('motion') or get_param('is_moving')
            if motion:
                position_data['attributes']['motion'] = motion.lower() in ['true', '1', 'yes']
            
            # Parse event
            event = get_param('event')
            if event:
                position_data['attributes']['event'] = event
            
            # Parse network info
            network_info = {}
            
            # WiFi info
            wifi = get_param('wifi')
            if wifi:
                network_info['wifi'] = wifi
            
            # Cell info
            cell = get_param('cell')
            if cell:
                network_info['cell'] = cell
            
            if network_info:
                position_data['attributes']['network'] = network_info
            
            return position_data
            
        except Exception as e:
            logger.error("Failed to create position from query params", error=str(e))
            return None
    
    async def _create_position_from_json(self, json_data: Dict[str, Any], device_id: str) -> Optional[Dict[str, Any]]:
        """Create position from JSON data"""
        try:
            position_data = {
                'device_id': device_id,  # Add device_id for PositionCreate
                'protocol': self.PROTOCOL_NAME,
                'valid': True,
                'attributes': {}
            }
            
            # Parse location data
            location = json_data.get('location', {})
            if location:
                coords = location.get('coords', {})
                
                # Parse coordinates
                if 'latitude' in coords and 'longitude' in coords:
                    position_data['latitude'] = float(coords['latitude'])
                    position_data['longitude'] = float(coords['longitude'])
                    
                    if not is_valid_coordinates(position_data['latitude'], position_data['longitude']):
                        position_data['valid'] = False
                
                # Parse timestamp
                timestamp = location.get('timestamp')
                if timestamp:
                    try:
                        position_data['device_time'] = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except ValueError:
                        pass
                
                # Parse speed
                if 'speed' in coords:
                    try:
                        position_data['speed'] = float(coords['speed']) * 1.94384  # Convert m/s to knots
                    except (ValueError, TypeError):
                        pass
                
                # Parse heading
                if 'heading' in coords:
                    try:
                        position_data['course'] = float(coords['heading'])
                    except (ValueError, TypeError):
                        pass
                
                # Parse altitude
                if 'altitude' in coords:
                    try:
                        position_data['altitude'] = float(coords['altitude'])
                    except (ValueError, TypeError):
                        pass
                
                # Parse accuracy
                if 'accuracy' in coords:
                    try:
                        position_data['attributes']['accuracy'] = float(coords['accuracy'])
                    except (ValueError, TypeError):
                        pass
                
                # Parse event
                if 'event' in location:
                    position_data['attributes']['event'] = location['event']
                
                # Parse motion
                if 'is_moving' in location:
                    position_data['attributes']['motion'] = location['is_moving']
            
            # Parse battery info
            if 'battery' in json_data:
                try:
                    position_data['attributes']['battery'] = float(json_data['battery'])
                except (ValueError, TypeError):
                    pass
            
            # Parse network info
            if 'network' in json_data:
                position_data['attributes']['network'] = json_data['network']
            
            return position_data
            
        except Exception as e:
            logger.error("Failed to create position from JSON data", error=str(e))
            return None
    
    async def create_events(self, message: ProtocolMessage) -> List[Dict[str, Any]]:
        """
        Create events from parsed OsmAnd message
        
        Args:
            message: Parsed protocol message
            
        Returns:
            List of event data dictionaries
        """
        events = []
        
        try:
            data = message.data
            event_type = None
            event_data = {}
            
            # Check for event in query params
            if 'query_params' in data:
                params = data['query_params']
                event = params.get('event', [None])[0]
                if event:
                    event_type = event
                    event_data = {'source': 'query'}
            
            # Check for event in JSON data
            elif 'json_data' in data:
                json_data = data['json_data']
                location = json_data.get('location', {})
                event = location.get('event')
                if event:
                    event_type = event
                    event_data = {'source': 'json'}
            
            # Create event if found
            if event_type:
                events.append({
                    'type': event_type,
                    'device_id': message.device_id,
                    'protocol': self.PROTOCOL_NAME,
                    'timestamp': message.timestamp,
                    'attributes': event_data
                })
            
            # Check for motion events
            motion = None
            if 'query_params' in data:
                motion = data['query_params'].get('motion', [None])[0]
            elif 'json_data' in data:
                location = data['json_data'].get('location', {})
                motion = location.get('is_moving')
            
            if motion is not None:
                motion_event = 'deviceMoving' if motion else 'deviceStopped'
                events.append({
                    'type': motion_event,
                    'device_id': message.device_id,
                    'protocol': self.PROTOCOL_NAME,
                    'timestamp': message.timestamp,
                    'attributes': {'motion': motion}
                })
            
        except Exception as e:
            logger.error("Failed to create events from OsmAnd message", error=str(e))
        
        return events
    
    def validate_device_id(self, device_id: str) -> bool:
        """Validate OsmAnd device ID format"""
        if not device_id:
            return False
        
        # OsmAnd device IDs can be various formats
        # Allow alphanumeric, UUIDs, and common mobile identifiers
        return len(device_id.strip()) >= 3 and len(device_id.strip()) <= 100
    
    def log_message(self, message: ProtocolMessage, client_address: Tuple[str, int]):
        """Log OsmAnd protocol message"""
        logger.info(
            "OsmAnd message received",
            device_id=message.device_id,
            message_type=message.message_type,
            client=client_address,
            valid=message.valid,
            protocol=self.PROTOCOL_NAME
        )
