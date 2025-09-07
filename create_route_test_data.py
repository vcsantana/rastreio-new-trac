#!/usr/bin/env python3
"""
Create test route data for a device to demonstrate replay functionality
"""
import asyncio
import asyncpg
import json
from datetime import datetime, timedelta
import random

async def create_route_data():
    """Create a realistic route with multiple positions"""
    
    # Database connection
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="traccar",
        password="traccar",
        database="traccar"
    )
    
    try:
        # Get device ID 12 (iPhone)
        device_id = 12
        
        # Create a route from São Paulo to Santos (realistic coordinates)
        # Starting point: São Paulo center
        start_lat = -23.5505
        start_lon = -46.6333
        
        # Ending point: Santos port
        end_lat = -23.9618
        end_lon = -46.3322
        
        # Create intermediate points for a realistic route
        route_points = [
            (-23.5505, -46.6333, "São Paulo Centro"),  # Start
            (-23.5600, -46.6400, "Vila Madalena"),
            (-23.5700, -46.6500, "Pinheiros"),
            (-23.5800, -46.6600, "Vila Olímpia"),
            (-23.5900, -46.6700, "Brooklin"),
            (-23.6000, -46.6800, "Campo Belo"),
            (-23.6100, -46.6900, "Santo Amaro"),
            (-23.6200, -46.7000, "Interlagos"),
            (-23.6300, -46.7100, "Capão Redondo"),
            (-23.6400, -46.7200, "Grajaú"),
            (-23.6500, -46.7300, "Parelheiros"),
            (-23.6600, -46.7400, "Marsilac"),
            (-23.6700, -46.7500, "Embu das Artes"),
            (-23.6800, -46.7600, "Taboão da Serra"),
            (-23.6900, -46.7700, "Embu-Guaçu"),
            (-23.7000, -46.7800, "Itapecerica da Serra"),
            (-23.7100, -46.7900, "São Lourenço da Serra"),
            (-23.7200, -46.8000, "Juquitiba"),
            (-23.7300, -46.8100, "Mogi das Cruzes"),
            (-23.7400, -46.8200, "Suzano"),
            (-23.7500, -46.8300, "Poá"),
            (-23.7600, -46.8400, "Ferraz de Vasconcelos"),
            (-23.7700, -46.8500, "Itaquaquecetuba"),
            (-23.7800, -46.8600, "Arujá"),
            (-23.7900, -46.8700, "Santa Isabel"),
            (-23.8000, -46.8800, "Guarulhos"),
            (-23.8100, -46.8900, "São Bernardo do Campo"),
            (-23.8200, -46.9000, "Santo André"),
            (-23.8300, -46.9100, "Mauá"),
            (-23.8400, -46.9200, "Ribeirão Pires"),
            (-23.8500, -46.9300, "Rio Grande da Serra"),
            (-23.8600, -46.9400, "Diadema"),
            (-23.8700, -46.9500, "São Caetano do Sul"),
            (-23.8800, -46.9600, "Cubatão"),
            (-23.8900, -46.9700, "Praia Grande"),
            (-23.9000, -46.9800, "Mongaguá"),
            (-23.9100, -46.9900, "Itanhaém"),
            (-23.9200, -47.0000, "Peruíbe"),
            (-23.9300, -47.0100, "Iguape"),
            (-23.9400, -47.0200, "Cananéia"),
            (-23.9500, -47.0300, "Ilha Comprida"),
            (-23.9600, -47.0400, "Registro"),
            (-23.9618, -46.3322, "Santos Porto"),  # End
        ]
        
        # Start time (1 hour ago)
        start_time = datetime.utcnow() - timedelta(hours=1)
        
        print(f"🗺️ Creating route with {len(route_points)} points...")
        
        # Insert positions
        for i, (lat, lon, address) in enumerate(route_points):
            # Calculate time for this position (spread over 1 hour)
            position_time = start_time + timedelta(minutes=i * 1.5)
            
            # Calculate speed based on position (faster in some segments)
            if i < 10:  # City driving
                speed = random.uniform(20, 40)
            elif i < 20:  # Highway
                speed = random.uniform(60, 100)
            else:  # Approaching destination
                speed = random.uniform(30, 60)
            
            # Calculate course (direction)
            if i < len(route_points) - 1:
                next_lat, next_lon, _ = route_points[i + 1]
                course = random.uniform(0, 360)  # Simplified course calculation
            else:
                course = 0
            
            # Create position data
            position_data = {
                'device_id': device_id,
                'protocol': 'osmand',
                'valid': True,
                'latitude': lat,
                'longitude': lon,
                'altitude': random.uniform(700, 800),
                'speed': speed,
                'course': course,
                'server_time': position_time,
                'device_time': position_time,
                'fix_time': position_time,
                'address': address,
                'accuracy': random.uniform(5, 15),
                'attributes': json.dumps({
                    'battery': random.randint(70, 100),
                    'signal': random.randint(3, 5),
                    'engine': 'on' if speed > 0 else 'off',
                    'odometer': i * 1000,  # Simulate odometer
                })
            }
            
            # Insert position
            await conn.execute("""
                INSERT INTO positions (
                    device_id, protocol, valid, latitude, longitude, altitude,
                    speed, course, server_time, device_time, fix_time,
                    address, accuracy, attributes
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
                )
            """, 
                position_data['device_id'],
                position_data['protocol'],
                position_data['valid'],
                position_data['latitude'],
                position_data['longitude'],
                position_data['altitude'],
                position_data['speed'],
                position_data['course'],
                position_data['server_time'],
                position_data['device_time'],
                position_data['fix_time'],
                position_data['address'],
                position_data['accuracy'],
                position_data['attributes']
            )
            
            print(f"📍 Position {i+1}/{len(route_points)}: {address} ({lat:.4f}, {lon:.4f}) - {speed:.1f} km/h")
        
        print(f"✅ Route created successfully with {len(route_points)} positions!")
        print(f"🕐 Route spans from {start_time.strftime('%H:%M')} to {(start_time + timedelta(minutes=len(route_points) * 1.5)).strftime('%H:%M')}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_route_data())
