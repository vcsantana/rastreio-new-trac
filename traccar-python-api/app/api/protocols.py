"""
Protocol server management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import asyncio

from app.database import get_db
from app.models import User
from app.api.auth import get_current_user
from app.protocols.protocol_server import (
    protocol_server_manager,
    start_protocol_servers,
    stop_protocol_servers,
    get_protocol_server_status
)

router = APIRouter()


@router.get("/status")
async def get_protocol_servers_status(
    current_user: User = Depends(get_current_user)
):
    """Get status of all protocol servers."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    status_info = get_protocol_server_status()
    total_servers = 0
    available_protocols = []
    
    if protocol_server_manager:
        total_servers = len(protocol_server_manager.protocol_servers)
        available_protocols = list(protocol_server_manager.protocol_handlers.keys())
    
    return {
        "servers": status_info,
        "total_servers": total_servers,
        "available_protocols": available_protocols
    }


@router.post("/start")
async def start_protocol_servers_endpoint(
    current_user: User = Depends(get_current_user)
):
    """Start all protocol servers."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        await start_protocol_servers()
        return {
            "message": "Protocol servers started successfully",
            "status": "running",
            "servers": get_protocol_server_status()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start protocol servers: {str(e)}"
        )


@router.post("/stop")
async def stop_protocol_servers_endpoint(
    current_user: User = Depends(get_current_user)
):
    """Stop all protocol servers."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        await stop_protocol_servers()
        return {
            "message": "Protocol servers stopped successfully",
            "status": "stopped"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop protocol servers: {str(e)}"
        )


@router.post("/start/{protocol_name}")
async def start_specific_protocol_server(
    protocol_name: str,
    host: str = "0.0.0.0",
    port: Optional[int] = None,
    protocol_type: str = "tcp",
    current_user: User = Depends(get_current_user)
):
    """Start a specific protocol server."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if protocol_name not in protocol_server_manager.protocol_handlers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protocol '{protocol_name}' not found"
        )
    
    try:
        await protocol_server_manager.start_protocol_server(
            protocol_name, host, port, protocol_type
        )
        
        return {
            "message": f"Protocol server '{protocol_name}' started successfully",
            "protocol": protocol_name,
            "host": host,
            "port": port or protocol_server_manager._get_default_port(protocol_name),
            "type": protocol_type
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start protocol server '{protocol_name}': {str(e)}"
        )


@router.post("/stop/{protocol_name}")
async def stop_specific_protocol_server(
    protocol_name: str,
    current_user: User = Depends(get_current_user)
):
    """Stop a specific protocol server."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if protocol_name not in protocol_server_manager.protocol_servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protocol server '{protocol_name}' is not running"
        )
    
    try:
        server = protocol_server_manager.protocol_servers[protocol_name]
        await server.stop()
        del protocol_server_manager.protocol_servers[protocol_name]
        
        return {
            "message": f"Protocol server '{protocol_name}' stopped successfully",
            "protocol": protocol_name
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop protocol server '{protocol_name}': {str(e)}"
        )


@router.get("/available")
async def get_available_protocols(
    current_user: User = Depends(get_current_user)
):
    """Get list of available protocol handlers."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    protocols = []
    for name, handler in protocol_server_manager.protocol_handlers.items():
        protocols.append({
            "name": name,
            "protocol_name": handler.PROTOCOL_NAME,
            "supported_message_types": handler.SUPPORTED_MESSAGE_TYPES,
            "default_port": protocol_server_manager._get_default_port(name)
        })
    
    return {
        "protocols": protocols,
        "total": len(protocols)
    }


@router.get("/test/{protocol_name}")
async def test_protocol_connection(
    protocol_name: str,
    current_user: User = Depends(get_current_user)
):
    """Test connection to a specific protocol server."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if protocol_name not in protocol_server_manager.protocol_servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protocol server '{protocol_name}' is not running"
        )
    
    server = protocol_server_manager.protocol_servers[protocol_name]
    
    try:
        # Test if server is responding
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((server.host, server.port))
        sock.close()
        
        if result == 0:
            return {
                "protocol": protocol_name,
                "status": "connected",
                "host": server.host,
                "port": server.port,
                "message": "Server is accepting connections"
            }
        else:
            return {
                "protocol": protocol_name,
                "status": "disconnected",
                "host": server.host,
                "port": server.port,
                "message": "Server is not accepting connections"
            }
    except Exception as e:
        return {
            "protocol": protocol_name,
            "status": "error",
            "host": server.host,
            "port": server.port,
            "message": f"Connection test failed: {str(e)}"
        }


@router.get("/logs/{protocol_name}")
async def get_protocol_logs(
    protocol_name: str,
    lines: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get logs for a specific protocol server."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if protocol_name not in protocol_server_manager.protocol_handlers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Protocol '{protocol_name}' not found"
        )
    
    # In a real implementation, this would read from log files
    # For now, return mock logs
    mock_logs = [
        f"2024-01-01 12:00:00 INFO: Protocol server '{protocol_name}' started",
        f"2024-01-01 12:00:01 INFO: Listening on 0.0.0.0:{protocol_server_manager._get_default_port(protocol_name)}",
        f"2024-01-01 12:00:02 INFO: Client connected from 192.168.1.100:12345",
        f"2024-01-01 12:00:03 INFO: Received message from device 123456789",
        f"2024-01-01 12:00:04 INFO: Position created for device 123456789",
    ]
    
    return {
        "protocol": protocol_name,
        "logs": mock_logs[:lines],
        "total_lines": len(mock_logs)
    }


@router.post("/servers/start")
async def start_protocol_servers_endpoint():
    """Start all protocol servers."""
    try:
        from app.protocols import start_protocol_servers
        await start_protocol_servers()
        return {"message": "Protocol servers started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start protocol servers: {str(e)}")


@router.post("/servers/stop")
async def stop_protocol_servers_endpoint():
    """Stop all protocol servers."""
    try:
        from app.protocols import stop_protocol_servers
        await stop_protocol_servers()
        return {"message": "Protocol servers stopped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop protocol servers: {str(e)}")


@router.get("/servers/status")
async def get_protocol_servers_status():
    """Get status of all protocol servers."""
    try:
        from app.protocols import get_protocol_server_status
        status = get_protocol_server_status()
        return {
            "servers": status,
            "total_servers": len(status),
            "active_servers": sum(1 for server in status.values() if server.get("running", False))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get server status: {str(e)}")


@router.post("/servers/{protocol_name}/start")
async def start_specific_protocol_server(
    protocol_name: str,
    host: str = "0.0.0.0",
    port: int = None,
    protocol_type: str = "tcp"
):
    """Start a specific protocol server."""
    try:
        from app.protocols import protocol_server_manager
        await protocol_server_manager.start_protocol_server(protocol_name, host, port, protocol_type)
        return {
            "message": f"Protocol server {protocol_name} started successfully",
            "protocol": protocol_name,
            "host": host,
            "port": port,
            "type": protocol_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start {protocol_name} server: {str(e)}")


@router.post("/servers/{protocol_name}/stop")
async def stop_specific_protocol_server(protocol_name: str):
    """Stop a specific protocol server."""
    try:
        from app.protocols import protocol_server_manager
        if protocol_name in protocol_server_manager.protocol_servers:
            await protocol_server_manager.protocol_servers[protocol_name].stop()
            del protocol_server_manager.protocol_servers[protocol_name]
            return {"message": f"Protocol server {protocol_name} stopped successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Protocol server {protocol_name} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop {protocol_name} server: {str(e)}")

