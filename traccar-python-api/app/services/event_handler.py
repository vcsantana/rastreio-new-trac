"""
Event handler system for automatic event generation
"""
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable
from sqlalchemy.orm import Session

from app.models import Event, Device, Position, Geofence
from app.services.event_service import EventService
from app.services.event_notification_service import EventNotificationService


class EventRule:
    """Rule for automatic event generation"""
    
    def __init__(self, name: str, condition: Callable, action: Callable, enabled: bool = True):
        self.name = name
        self.condition = condition
        self.action = action
        self.enabled = enabled
        self.last_triggered = None
        self.trigger_count = 0

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate if rule condition is met"""
        if not self.enabled:
            return False
        
        try:
            return self.condition(context)
        except Exception as e:
            print(f"Error evaluating rule {self.name}: {e}")
            return False

    def execute(self, context: Dict[str, Any]) -> Optional[Event]:
        """Execute rule action"""
        if not self.enabled:
            return None
        
        try:
            result = self.action(context)
            self.last_triggered = datetime.utcnow()
            self.trigger_count += 1
            return result
        except Exception as e:
            print(f"Error executing rule {self.name}: {e}")
            return None


class EventHandler:
    """Handler for automatic event generation based on rules"""
    
    def __init__(self, db: Session):
        self.db = db
        self.event_service = EventService(db)
        self.notification_service = EventNotificationService(db)
        self.rules: List[EventRule] = []
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Setup default event generation rules"""
        
        # Device status rules
        self.add_rule(EventRule(
            name="device_online",
            condition=self._is_device_online,
            action=self._create_device_online_event
        ))
        
        self.add_rule(EventRule(
            name="device_offline",
            condition=self._is_device_offline,
            action=self._create_device_offline_event
        ))
        
        # Motion rules
        self.add_rule(EventRule(
            name="device_moving",
            condition=self._is_device_moving,
            action=self._create_motion_event
        ))
        
        self.add_rule(EventRule(
            name="device_stopped",
            condition=self._is_device_stopped,
            action=self._create_stopped_event
        ))
        
        # Speed rules
        self.add_rule(EventRule(
            name="overspeed",
            condition=self._is_overspeed,
            action=self._create_overspeed_event
        ))
        
        # Geofence rules
        self.add_rule(EventRule(
            name="geofence_enter",
            condition=self._is_geofence_enter,
            action=self._create_geofence_enter_event
        ))
        
        self.add_rule(EventRule(
            name="geofence_exit",
            condition=self._is_geofence_exit,
            action=self._create_geofence_exit_event
        ))
        
        # Ignition rules
        self.add_rule(EventRule(
            name="ignition_on",
            condition=self._is_ignition_on,
            action=self._create_ignition_on_event
        ))
        
        self.add_rule(EventRule(
            name="ignition_off",
            condition=self._is_ignition_off,
            action=self._create_ignition_off_event
        ))

    def add_rule(self, rule: EventRule):
        """Add a new event rule"""
        self.rules.append(rule)

    def remove_rule(self, name: str):
        """Remove event rule by name"""
        self.rules = [rule for rule in self.rules if rule.name != name]

    def enable_rule(self, name: str):
        """Enable event rule"""
        for rule in self.rules:
            if rule.name == name:
                rule.enabled = True
                break

    def disable_rule(self, name: str):
        """Disable event rule"""
        for rule in self.rules:
            if rule.name == name:
                rule.enabled = False
                break

    def process_position(self, position: Position) -> List[Event]:
        """Process position and generate events based on rules"""
        events = []
        
        # Get device and previous position
        device = self.db.query(Device).filter(Device.id == position.device_id).first()
        if not device:
            return events
        
        # Get previous position for comparison
        previous_position = self.db.query(Position).filter(
            Position.device_id == position.device_id,
            Position.id < position.id
        ).order_by(Position.id.desc()).first()
        
        # Create context for rule evaluation
        context = {
            "position": position,
            "device": device,
            "previous_position": previous_position,
            "db": self.db
        }
        
        # Evaluate all rules
        for rule in self.rules:
            if rule.evaluate(context):
                event = rule.execute(context)
                if event:
                    events.append(event)
        
        return events

    def process_device_status(self, device: Device, status: str) -> Optional[Event]:
        """Process device status change and generate event"""
        context = {
            "device": device,
            "status": status,
            "db": self.db
        }
        
        # Find appropriate rule
        rule_name = f"device_{status.lower()}"
        for rule in self.rules:
            if rule.name == rule_name and rule.evaluate(context):
                return rule.execute(context)
        
        return None

    # Rule conditions
    def _is_device_online(self, context: Dict[str, Any]) -> bool:
        """Check if device came online"""
        device = context["device"]
        # Simple check - if device has recent position, it's online
        recent_position = self.db.query(Position).filter(
            Position.device_id == device.id,
            Position.device_time >= datetime.utcnow() - timedelta(minutes=5)
        ).first()
        return recent_position is not None

    def _is_device_offline(self, context: Dict[str, Any]) -> bool:
        """Check if device went offline"""
        device = context["device"]
        # Check if no recent position
        recent_position = self.db.query(Position).filter(
            Position.device_id == device.id,
            Position.device_time >= datetime.utcnow() - timedelta(minutes=10)
        ).first()
        return recent_position is None

    def _is_device_moving(self, context: Dict[str, Any]) -> bool:
        """Check if device started moving"""
        position = context["position"]
        previous_position = context["previous_position"]
        
        if not previous_position:
            return False
        
        # Check if speed increased from 0 to > 0
        return (previous_position.speed or 0) == 0 and (position.speed or 0) > 0

    def _is_device_stopped(self, context: Dict[str, Any]) -> bool:
        """Check if device stopped moving"""
        position = context["position"]
        previous_position = context["previous_position"]
        
        if not previous_position:
            return False
        
        # Check if speed decreased from > 0 to 0
        return (previous_position.speed or 0) > 0 and (position.speed or 0) == 0

    def _is_overspeed(self, context: Dict[str, Any]) -> bool:
        """Check if device exceeded speed limit"""
        position = context["position"]
        device = context["device"]
        
        # Get speed limit from device attributes or default
        speed_limit = device.get_double_attribute("speedLimit", 80.0)  # Default 80 km/h
        
        return (position.speed or 0) > speed_limit

    def _is_geofence_enter(self, context: Dict[str, Any]) -> bool:
        """Check if device entered geofence"""
        # Geofence detection is now handled by GeofenceDetectionService
        # This method is kept for compatibility but returns False
        # The actual geofence detection happens in the position processing pipeline
        return False

    def _is_geofence_exit(self, context: Dict[str, Any]) -> bool:
        """Check if device exited geofence"""
        # Geofence detection is now handled by GeofenceDetectionService
        # This method is kept for compatibility but returns False
        # The actual geofence detection happens in the position processing pipeline
        return False

    def _is_ignition_on(self, context: Dict[str, Any]) -> bool:
        """Check if ignition turned on"""
        position = context["position"]
        previous_position = context["previous_position"]
        
        if not previous_position:
            return False
        
        # Check ignition status from attributes
        current_ignition = position.get_boolean_attribute("ignition", False)
        previous_ignition = previous_position.get_boolean_attribute("ignition", False)
        
        return not previous_ignition and current_ignition

    def _is_ignition_off(self, context: Dict[str, Any]) -> bool:
        """Check if ignition turned off"""
        position = context["position"]
        previous_position = context["previous_position"]
        
        if not previous_position:
            return False
        
        # Check ignition status from attributes
        current_ignition = position.get_boolean_attribute("ignition", False)
        previous_ignition = previous_position.get_boolean_attribute("ignition", False)
        
        return previous_ignition and not current_ignition

    # Rule actions
    def _create_device_online_event(self, context: Dict[str, Any]) -> Event:
        """Create device online event"""
        device = context["device"]
        return self.event_service.create_device_status_event(device.id, "online")

    def _create_device_offline_event(self, context: Dict[str, Any]) -> Event:
        """Create device offline event"""
        device = context["device"]
        return self.event_service.create_device_status_event(device.id, "offline")

    def _create_motion_event(self, context: Dict[str, Any]) -> Event:
        """Create device moving event"""
        position = context["position"]
        return self.event_service.create_motion_event(position, True)

    def _create_stopped_event(self, context: Dict[str, Any]) -> Event:
        """Create device stopped event"""
        position = context["position"]
        return self.event_service.create_motion_event(position, False)

    def _create_overspeed_event(self, context: Dict[str, Any]) -> Event:
        """Create overspeed event"""
        position = context["position"]
        device = context["device"]
        speed_limit = device.get_double_attribute("speedLimit", 80.0)
        return self.event_service.create_overspeed_event(position, speed_limit)

    def _create_geofence_enter_event(self, context: Dict[str, Any]) -> Event:
        """Create geofence enter event"""
        position = context["position"]
        # In real implementation, you'd determine which geofence was entered
        geofence_id = 1  # Placeholder
        return self.event_service.create_geofence_event(position, geofence_id, True)

    def _create_geofence_exit_event(self, context: Dict[str, Any]) -> Event:
        """Create geofence exit event"""
        position = context["position"]
        # In real implementation, you'd determine which geofence was exited
        geofence_id = 1  # Placeholder
        return self.event_service.create_geofence_event(position, geofence_id, False)

    def _create_ignition_on_event(self, context: Dict[str, Any]) -> Event:
        """Create ignition on event"""
        position = context["position"]
        return self.event_service.create_ignition_event(position, True)

    def _create_ignition_off_event(self, context: Dict[str, Any]) -> Event:
        """Create ignition off event"""
        position = context["position"]
        return self.event_service.create_ignition_event(position, False)

    def get_rule_stats(self) -> Dict[str, Any]:
        """Get statistics about rule execution"""
        stats = {}
        for rule in self.rules:
            stats[rule.name] = {
                "enabled": rule.enabled,
                "trigger_count": rule.trigger_count,
                "last_triggered": rule.last_triggered.isoformat() if rule.last_triggered else None
            }
        return stats
