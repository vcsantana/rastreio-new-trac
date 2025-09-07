# Exemplos Práticos - Sistema de Dispositivos

## 🚗 Cenários de Uso Comuns

### 1. Gerenciamento de Frota de Veículos

#### Cenário: Empresa de Logística
Uma empresa de logística precisa gerenciar 50 veículos com diferentes tipos e responsáveis.

#### Configuração Recomendada:
```json
{
  "grupos": [
    {
      "name": "Frota Principal",
      "description": "Veículos principais da empresa"
    },
    {
      "name": "Frota Reserva", 
      "description": "Veículos de backup"
    }
  ],
  "pessoas": [
    {
      "name": "João Silva",
      "person_type": "physical",
      "cpf": "123.456.789-00"
    },
    {
      "name": "Maria Santos",
      "person_type": "physical", 
      "cpf": "987.654.321-00"
    }
  ],
  "dispositivos": [
    {
      "name": "Caminhão 01",
      "unique_id": "CAM001",
      "category": "truck",
      "license_plate": "ABC-1234",
      "protocol": "teltonika",
      "group_id": 1,
      "person_id": 1
    },
    {
      "name": "Van Entrega",
      "unique_id": "VAN001", 
      "category": "van",
      "license_plate": "XYZ-9876",
      "protocol": "gt06",
      "group_id": 1,
      "person_id": 2
    }
  ]
}
```

### 2. Rastreamento de Smartphones

#### Cenário: Empresa com Funcionários Remotos
Uma empresa precisa rastrear smartphones de funcionários que trabalham em campo.

#### Configuração:
```json
{
  "dispositivos": [
    {
      "name": "iPhone João",
      "unique_id": "IPHONE_001",
      "category": "iphone",
      "phone": "+5511999999999",
      "protocol": "osmand",
      "person_id": 1
    },
    {
      "name": "Android Maria",
      "unique_id": "ANDROID_001", 
      "category": "android",
      "phone": "+5511888888888",
      "protocol": "osmand",
      "person_id": 2
    }
  ]
}
```

### 3. Monitoramento de Embarcações

#### Cenário: Empresa de Pesca
Uma empresa de pesca precisa monitorar suas embarcações.

#### Configuração:
```json
{
  "dispositivos": [
    {
      "name": "Barco Pescador 01",
      "unique_id": "BOAT001",
      "category": "boat",
      "license_plate": "BR-1234",
      "protocol": "nmea",
      "contact": "Capitão Silva",
      "phone": "+5511777777777"
    }
  ]
}
```

## 🔧 Comandos Úteis

### 1. Criar Dispositivo via API

```bash
#!/bin/bash
# Script para criar dispositivo

TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@traccar.com", "password": "admin123"}' \
  | jq -r '.access_token')

curl -X POST "http://localhost:8000/api/devices/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Novo Veículo",
    "unique_id": "VEICULO_'$(date +%s)'",
    "category": "car",
    "license_plate": "ABC-1234",
    "protocol": "gt06",
    "phone": "+5511999999999"
  }'
```

### 2. Listar Dispositivos por Categoria

```bash
#!/bin/bash
# Listar apenas dispositivos iPhone

TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@traccar.com", "password": "admin123"}' \
  | jq -r '.access_token')

curl -X GET "http://localhost:8000/api/devices/" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.[] | select(.category == "iphone")'
```

### 3. Atualizar Placa de Múltiplos Dispositivos

```bash
#!/bin/bash
# Script para atualizar placas

TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@traccar.com", "password": "admin123"}' \
  | jq -r '.access_token')

# Lista de dispositivos e novas placas
declare -A placas=(
  ["1"]="NOVA-1234"
  ["2"]="NOVA-5678" 
  ["3"]="NOVA-9012"
)

for device_id in "${!placas[@]}"; do
  curl -X PUT "http://localhost:8000/api/devices/$device_id" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"license_plate\": \"${placas[$device_id]}\"}"
done
```

## 📊 Queries SQL Úteis

### 1. Relatório de Dispositivos por Categoria

```sql
SELECT 
    category,
    COUNT(*) as total,
    COUNT(CASE WHEN disabled = false THEN 1 END) as ativos,
    COUNT(CASE WHEN disabled = true THEN 1 END) as inativos
FROM devices 
GROUP BY category 
ORDER BY total DESC;
```

### 2. Dispositivos sem Placa

```sql
SELECT 
    id,
    name,
    unique_id,
    category
FROM devices 
WHERE license_plate IS NULL OR license_plate = '';
```

### 3. Dispositivos por Pessoa

```sql
SELECT 
    p.name as pessoa,
    COUNT(d.id) as total_dispositivos,
    STRING_AGG(d.name, ', ') as dispositivos
FROM persons p
LEFT JOIN devices d ON p.id = d.person_id
GROUP BY p.id, p.name
ORDER BY total_dispositivos DESC;
```

### 4. Dispositivos por Grupo

```sql
SELECT 
    g.name as grupo,
    COUNT(d.id) as total_dispositivos,
    COUNT(CASE WHEN d.disabled = false THEN 1 END) as ativos
FROM groups g
LEFT JOIN devices d ON g.id = d.group_id
GROUP BY g.id, g.name
ORDER BY total_dispositivos DESC;
```

## 🎯 Casos de Uso Avançados

### 1. Migração de Dispositivos

#### Cenário: Migrar dispositivos de um grupo para outro

```python
# Script Python para migração
import asyncio
from sqlalchemy import text
from app.database import get_db

async def migrate_devices():
    async for db in get_db():
        # Mover todos os dispositivos do grupo 1 para o grupo 2
        await db.execute(text("""
            UPDATE devices 
            SET group_id = 2 
            WHERE group_id = 1
        """))
        await db.commit()
        print("Migração concluída!")

asyncio.run(migrate_devices())
```

### 2. Backup de Configurações

```sql
-- Exportar configurações de dispositivos
COPY (
    SELECT 
        name,
        unique_id,
        category,
        license_plate,
        phone,
        model,
        contact,
        protocol,
        disabled,
        g.name as group_name,
        p.name as person_name
    FROM devices d
    LEFT JOIN groups g ON d.group_id = g.id
    LEFT JOIN persons p ON d.person_id = p.id
) TO '/tmp/devices_backup.csv' WITH CSV HEADER;
```

### 3. Validação de Dados

```sql
-- Verificar dispositivos com dados inconsistentes
SELECT 
    id,
    name,
    unique_id,
    CASE 
        WHEN unique_id IS NULL OR unique_id = '' THEN 'Unique ID vazio'
        WHEN name IS NULL OR name = '' THEN 'Nome vazio'
        WHEN category = 'car' AND (license_plate IS NULL OR license_plate = '') THEN 'Carro sem placa'
        ELSE 'OK'
    END as problema
FROM devices
WHERE 
    unique_id IS NULL OR unique_id = '' OR
    name IS NULL OR name = '' OR
    (category = 'car' AND (license_plate IS NULL OR license_plate = ''))
ORDER BY problema;
```

## 🔍 Monitoramento e Alertas

### 1. Dispositivos Offline há Mais de 24h

```sql
SELECT 
    id,
    name,
    unique_id,
    last_update,
    EXTRACT(EPOCH FROM (NOW() - last_update))/3600 as horas_offline
FROM devices 
WHERE 
    disabled = false AND
    (last_update IS NULL OR last_update < NOW() - INTERVAL '24 hours')
ORDER BY horas_offline DESC;
```

### 2. Dispositivos sem Atividade Recente

```sql
SELECT 
    d.id,
    d.name,
    d.unique_id,
    d.last_update,
    p.name as pessoa_responsavel,
    g.name as grupo
FROM devices d
LEFT JOIN persons p ON d.person_id = p.id
LEFT JOIN groups g ON d.group_id = g.id
WHERE 
    d.disabled = false AND
    (d.last_update IS NULL OR d.last_update < NOW() - INTERVAL '7 days')
ORDER BY d.last_update ASC;
```

## 🚀 Automações

### 1. Script de Limpeza Automática

```bash
#!/bin/bash
# Script para desativar dispositivos inativos

TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@traccar.com", "password": "admin123"}' \
  | jq -r '.access_token')

# Obter dispositivos offline há mais de 30 dias
DEVICES=$(curl -s -X GET "http://localhost:8000/api/devices/" \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.[] | select(.last_update == null or (.last_update | strptime("%Y-%m-%dT%H:%M:%S.%fZ") | mktime) < (now - 2592000)) | .id')

# Desativar dispositivos inativos
for device_id in $DEVICES; do
  curl -X PUT "http://localhost:8000/api/devices/$device_id" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"disabled": true}'
  echo "Dispositivo $device_id desativado por inatividade"
done
```

### 2. Relatório Semanal Automático

```python
# Script Python para relatório semanal
import asyncio
from sqlalchemy import text
from app.database import get_db
from datetime import datetime, timedelta

async def weekly_report():
    async for db in get_db():
        # Estatísticas da semana
        result = await db.execute(text("""
            SELECT 
                COUNT(*) as total_devices,
                COUNT(CASE WHEN disabled = false THEN 1 END) as active_devices,
                COUNT(CASE WHEN last_update > NOW() - INTERVAL '7 days' THEN 1 END) as active_last_week,
                COUNT(CASE WHEN category = 'iphone' THEN 1 END) as iphones,
                COUNT(CASE WHEN category = 'android' THEN 1 END) as androids,
                COUNT(CASE WHEN category = 'car' THEN 1 END) as cars
            FROM devices
        """))
        
        stats = result.fetchone()
        
        report = f"""
        RELATÓRIO SEMANAL - {datetime.now().strftime('%d/%m/%Y')}
        
        Total de Dispositivos: {stats[0]}
        Dispositivos Ativos: {stats[1]}
        Atividade na Semana: {stats[2]}
        
        Por Categoria:
        - iPhones: {stats[3]}
        - Androids: {stats[4]}
        - Carros: {stats[5]}
        """
        
        print(report)
        # Aqui você pode enviar por email ou salvar em arquivo

asyncio.run(weekly_report())
```

## 📱 Integração com Aplicativos Mobile

### 1. Configuração para OsmAnd

```json
{
  "device": {
    "name": "Smartphone João",
    "unique_id": "OSMAND_001",
    "category": "android",
    "protocol": "osmand",
    "phone": "+5511999999999"
  },
  "osmand_config": {
    "server_url": "http://localhost:8080",
    "username": "joao@empresa.com",
    "password": "senha123",
    "device_id": "OSMAND_001"
  }
}
```

### 2. Configuração para Traccar Client

```json
{
  "device": {
    "name": "iPhone Maria",
    "unique_id": "IPHONE_001", 
    "category": "iphone",
    "protocol": "osmand"
  },
  "traccar_config": {
    "server": "localhost",
    "port": 8080,
    "device_id": "IPHONE_001"
  }
}
```

## 🔧 Manutenção e Troubleshooting

### 1. Verificar Conectividade

```bash
#!/bin/bash
# Script para verificar conectividade dos dispositivos

TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@traccar.com", "password": "admin123"}' \
  | jq -r '.access_token')

echo "Verificando conectividade dos dispositivos..."

curl -s -X GET "http://localhost:8000/api/devices/" \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.[] | "\(.name): \(.status) - Última atualização: \(.last_update // "Nunca")"'
```

### 2. Limpeza de Dados Antigos

```sql
-- Remover posições antigas (mais de 1 ano)
DELETE FROM positions 
WHERE fix_time < NOW() - INTERVAL '1 year';

-- Remover eventos antigos (mais de 6 meses)
DELETE FROM events 
WHERE event_time < NOW() - INTERVAL '6 months';

-- Atualizar estatísticas
ANALYZE devices;
ANALYZE positions;
ANALYZE events;
```

### 3. Backup e Restore

```bash
#!/bin/bash
# Script de backup completo

BACKUP_DIR="/backup/traccar/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup do banco de dados
pg_dump -h localhost -U traccar -d traccar > $BACKUP_DIR/database.sql

# Backup das configurações
cp -r /opt/traccar/conf $BACKUP_DIR/

# Backup dos logs
cp -r /opt/traccar/logs $BACKUP_DIR/

echo "Backup criado em: $BACKUP_DIR"
```

---

**Última Atualização**: 06 de Janeiro de 2025
**Versão**: 1.0.0
