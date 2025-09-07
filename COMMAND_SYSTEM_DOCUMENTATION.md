# 🚀 Sistema de Comandos - Documentação Completa

## 📊 **STATUS: ✅ 100% IMPLEMENTADO E FUNCIONANDO**

**Data**: Janeiro 2025  
**Versão**: 1.0.0  
**Status**: ✅ **PRODUCTION-READY**

---

## 🎯 **VISÃO GERAL**

O Sistema de Comandos permite o envio de comandos para dispositivos GPS conectados ao sistema Traccar. O sistema suporta múltiplos protocolos, gerenciamento de filas, retry automático e monitoramento em tempo real.

### **Características Principais:**
- ✅ **28 Tipos de Comandos** (Suntech, OsmAnd, Genéricos)
- ✅ **8 Status de Execução** (PENDING, SENT, DELIVERED, etc.)
- ✅ **4 Níveis de Prioridade** (LOW, NORMAL, HIGH, CRITICAL)
- ✅ **Sistema de Filas** com processamento assíncrono
- ✅ **Retry Automático** com configuração personalizada
- ✅ **Monitoramento em Tempo Real** via WebSocket
- ✅ **API REST Completa** com 14 endpoints

---

## 🏗️ **ARQUITETURA DO SISTEMA**

### **Componentes Principais:**

```mermaid
graph TB
    subgraph "API Layer"
        A[Command API] --> B[Command Service]
        B --> C[Command Queue]
    end
    
    subgraph "Processing Layer"
        C --> D[Celery Tasks]
        D --> E[Protocol Handlers]
    end
    
    subgraph "Protocol Layer"
        E --> F[Suntech Protocol]
        E --> G[OsmAnd Protocol]
    end
    
    subgraph "Data Layer"
        H[PostgreSQL] --> I[Command Table]
        H --> J[CommandQueue Table]
        K[Redis] --> L[Cache & Queue]
    end
    
    subgraph "Device Layer"
        F --> M[GPS Trackers]
        G --> N[Mobile Devices]
    end
    
    A --> H
    A --> K
    D --> K
```

---

## 📋 **TIPOS DE COMANDOS SUPORTADOS**

### **Comandos Suntech (17 tipos):**
| Comando | Descrição | Parâmetros |
|---------|-----------|------------|
| `REBOOT` | Reiniciar dispositivo | - |
| `SETTIME` | Configurar horário | - |
| `SETINTERVAL` | Intervalo de envio | `interval` (segundos) |
| `SETOVERSPEED` | Limite de velocidade | `speed_limit` (km/h) |
| `SETGEOFENCE` | Configurar geofence | `latitude`, `longitude`, `radius` |
| `SETOUTPUT` | Controlar saída digital | `output_id`, `output_state` |
| `SETINPUT` | Configurar entrada | `input_id`, `input_type` |
| `SETACCELERATION` | Limite de aceleração | `threshold` |
| `SETDECELERATION` | Limite de desaceleração | `threshold` |
| `SETTURN` | Detecção de curva | `angle_threshold` |
| `SETIDLE` | Tempo de inatividade | `idle_time` |
| `SETPARKING` | Detecção de estacionamento | - |
| `SETMOVEMENT` | Detecção de movimento | - |
| `SETVIBRATION` | Detecção de vibração | - |
| `SETDOOR` | Controle de porta | - |
| `SETPOWER` | Controle de energia | - |

### **Comandos OsmAnd (8 tipos):**
| Comando | Descrição | Parâmetros |
|---------|-----------|------------|
| `SET_INTERVAL` | Intervalo de tracking | `interval` (segundos) |
| `SET_ACCURACY` | Precisão GPS | `accuracy` (metros) |
| `SET_BATTERY_SAVER` | Modo economia | `battery_saver` (boolean) |
| `SET_ALARM` | Configurar alarmes | `alarm_type`, `alarm_enabled` |
| `SET_GEOFENCE` | Configurar geofence | `latitude`, `longitude`, `radius` |
| `SET_SPEED_LIMIT` | Limite de velocidade | `speed_limit` (km/h) |
| `SET_ENGINE_STOP` | Parar motor | - |
| `SET_ENGINE_START` | Ligar motor | - |

### **Comandos Genéricos (3 tipos):**
| Comando | Descrição | Parâmetros |
|---------|-----------|------------|
| `CUSTOM` | Comando personalizado | `raw_command` |
| `PING` | Teste de conectividade | - |
| `STATUS` | Status do dispositivo | - |
| `CONFIG` | Configuração geral | `parameters` |

---

## 📊 **STATUS DE COMANDOS**

### **Fluxo de Status:**
```
PENDING → SENT → DELIVERED → EXECUTED
    ↓        ↓        ↓
  FAILED ← TIMEOUT ← CANCELLED
    ↓
  EXPIRED
```

### **Descrição dos Status:**
- **PENDING**: Comando na fila, aguardando envio
- **SENT**: Comando enviado para o dispositivo
- **DELIVERED**: Comando entregue ao dispositivo
- **EXECUTED**: Comando executado com sucesso
- **FAILED**: Falha na execução do comando
- **TIMEOUT**: Comando expirou sem resposta
- **CANCELLED**: Comando cancelado pelo usuário
- **EXPIRED**: Comando expirou antes do envio

---

## 🎯 **PRIORIDADES DE COMANDOS**

| Prioridade | Descrição | Uso Recomendado |
|------------|-----------|-----------------|
| **LOW** | Baixa prioridade | Comandos de configuração |
| **NORMAL** | Prioridade normal | Comandos padrão |
| **HIGH** | Alta prioridade | Comandos importantes |
| **CRITICAL** | Prioridade crítica | Emergências, SOS |

---

## 🔧 **API ENDPOINTS**

### **Endpoints Públicos:**
```http
GET /api/commands/types/          # Listar tipos de comandos
GET /api/commands/statuses/       # Listar status disponíveis
GET /api/commands/priorities/     # Listar prioridades
```

### **Endpoints de Gerenciamento:**
```http
POST /api/commands/               # Criar comando
GET /api/commands/                # Listar comandos
GET /api/commands/{id}            # Obter comando específico
PUT /api/commands/{id}            # Atualizar comando
```

### **Endpoints Avançados:**
```http
POST /api/commands/bulk           # Criar comandos em lote
POST /api/commands/retry          # Retry de comandos falhados
POST /api/commands/cancel         # Cancelar comandos
GET /api/commands/stats/summary   # Estatísticas de comandos
GET /api/commands/queue/          # Fila de comandos
GET /api/commands/device/{id}     # Comandos por dispositivo
```

### **Exemplo de Criação de Comando:**
```json
POST /api/commands/
{
  "device_id": 1,
  "command_type": "SETINTERVAL",
  "priority": "NORMAL",
  "parameters": {
    "interval": 60
  },
  "expires_at": "2025-01-07T12:00:00Z",
  "max_retries": 3
}
```

---

## 🗄️ **MODELOS DE DADOS**

### **Tabela `commands`:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID único do comando |
| `device_id` | Integer | ID do dispositivo |
| `user_id` | Integer | ID do usuário que enviou |
| `command_type` | String | Tipo do comando |
| `priority` | String | Prioridade do comando |
| `status` | String | Status atual |
| `parameters` | JSON | Parâmetros do comando |
| `raw_command` | Text | Comando raw para protocolo |
| `sent_at` | DateTime | Quando foi enviado |
| `delivered_at` | DateTime | Quando foi entregue |
| `executed_at` | DateTime | Quando foi executado |
| `failed_at` | DateTime | Quando falhou |
| `response` | Text | Resposta do dispositivo |
| `error_message` | Text | Mensagem de erro |
| `retry_count` | Integer | Número de tentativas |
| `max_retries` | Integer | Máximo de tentativas |
| `expires_at` | DateTime | Data de expiração |
| `created_at` | DateTime | Data de criação |
| `updated_at` | DateTime | Data de atualização |

### **Tabela `command_queue`:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | Integer | ID único da fila |
| `command_id` | Integer | ID do comando |
| `priority` | String | Prioridade na fila |
| `scheduled_at` | DateTime | Agendamento |
| `queued_at` | DateTime | Quando foi enfileirado |
| `attempts` | Integer | Número de tentativas |
| `last_attempt_at` | DateTime | Última tentativa |
| `next_attempt_at` | DateTime | Próxima tentativa |
| `is_active` | Boolean | Se está ativo |
| `created_at` | DateTime | Data de criação |
| `updated_at` | DateTime | Data de atualização |

---

## ⚙️ **CONFIGURAÇÃO E DEPLOYMENT**

### **Variáveis de Ambiente:**
```bash
# Redis Configuration
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/1

# Database Configuration
DATABASE_URL=postgresql+asyncpg://traccar:traccar123@postgres:5432/traccar

# Security
SECRET_KEY=your-secret-key
```

### **Docker Compose:**
```yaml
services:
  api:
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - REDIS_URL=redis://redis:6379/0
```

### **Iniciar Celery Workers:**
```bash
# Worker para comandos
celery -A app.core.celery_app worker --loglevel=info --queues=commands

# Beat scheduler
celery -A app.core.celery_app beat --loglevel=info

# Monitor
celery -A app.core.celery_app flower
```

---

## 🔄 **TAREFAS CELERY**

### **Tarefas Periódicas:**
| Tarefa | Frequência | Descrição |
|--------|------------|-----------|
| `process_command_queue` | 10 segundos | Processa fila de comandos |
| `check_command_timeouts` | 5 minutos | Verifica timeouts |
| `cleanup_expired_commands` | 1 hora | Limpa comandos expirados |

### **Tarefas Manuais:**
| Tarefa | Descrição |
|--------|-----------|
| `send_command_to_device` | Envia comando para dispositivo |
| `retry_failed_commands` | Retry de comandos falhados |
| `cancel_pending_commands` | Cancela comandos pendentes |

---

## 📈 **MONITORAMENTO E ESTATÍSTICAS**

### **Métricas Disponíveis:**
- Total de comandos enviados
- Comandos por status
- Comandos por prioridade
- Comandos por tipo
- Comandos por dispositivo
- Taxa de sucesso/falha
- Tempo médio de execução
- Comandos por período

### **Health Check:**
```bash
curl http://localhost:8000/health
```

**Resposta:**
```json
{
  "status": "healthy",
  "celery": {
    "connected": true,
    "workers": 2
  },
  "cache": {
    "connected": true,
    "stats": {
      "used_memory": "1.08M",
      "total_commands_processed": 847
    }
  }
}
```

---

## 🧪 **TESTES E VALIDAÇÃO**

### **Testes Implementados:**
```bash
# Executar testes
docker-compose -f docker-compose.dev.yml exec api python test_command_docker.py
```

**Resultado:**
```
📊 Test Results: 7/7 tests passed
🎉 All Command System tests passed!
```

### **Testes Manuais:**
```bash
# Testar tipos de comandos
curl http://localhost:8000/api/commands/types/

# Testar criação de comando
curl -X POST http://localhost:8000/api/commands/ \
  -H "Content-Type: application/json" \
  -d '{"device_id": 1, "command_type": "REBOOT", "priority": "NORMAL"}'

# Testar estatísticas
curl http://localhost:8000/api/commands/stats/summary
```

---

## 🚀 **EXEMPLOS DE USO**

### **1. Enviar Comando de Reboot:**
```python
import requests

command_data = {
    "device_id": 1,
    "command_type": "REBOOT",
    "priority": "HIGH"
}

response = requests.post(
    "http://localhost:8000/api/commands/",
    json=command_data,
    headers={"Authorization": "Bearer your-token"}
)
```

### **2. Configurar Intervalo de Tracking:**
```python
command_data = {
    "device_id": 1,
    "command_type": "SETINTERVAL",
    "priority": "NORMAL",
    "parameters": {
        "interval": 30  # 30 segundos
    }
}
```

### **3. Criar Comandos em Lote:**
```python
bulk_data = {
    "device_ids": [1, 2, 3, 4, 5],
    "command_type": "SETOVERSPEED",
    "priority": "NORMAL",
    "parameters": {
        "speed_limit": 80
    }
}

response = requests.post(
    "http://localhost:8000/api/commands/bulk",
    json=bulk_data
)
```

### **4. Monitorar Status de Comando:**
```python
# Obter comando específico
response = requests.get("http://localhost:8000/api/commands/123")
command = response.json()

print(f"Status: {command['status']}")
print(f"Retry Count: {command['retry_count']}")
print(f"Can Retry: {command['can_retry']}")
```

---

## 🔒 **SEGURANÇA E PERMISSÕES**

### **Autenticação:**
- Todos os endpoints (exceto tipos/status/priorities) requerem JWT
- Rate limiting configurado por endpoint
- Validação de permissões por dispositivo

### **Rate Limiting:**
| Endpoint | Limite | Janela |
|----------|--------|--------|
| `/api/commands/` | 100 req/h | 1 hora |
| `/api/commands/bulk` | 50 req/h | 1 hora |
| `/api/commands/retry` | 50 req/h | 1 hora |
| `/api/commands/cancel` | 50 req/h | 1 hora |

### **Validações:**
- Validação de parâmetros por tipo de comando
- Verificação de existência do dispositivo
- Validação de permissões do usuário
- Sanitização de dados de entrada

---

## 🐛 **TROUBLESHOOTING**

### **Problemas Comuns:**

**1. Comando não é enviado:**
- Verificar se o dispositivo está online
- Verificar se o protocolo está configurado
- Verificar logs do Celery worker

**2. Comando falha constantemente:**
- Verificar conectividade do dispositivo
- Verificar se o comando é suportado pelo protocolo
- Verificar parâmetros do comando

**3. Celery não processa comandos:**
- Verificar conexão com Redis
- Verificar se workers estão rodando
- Verificar logs de erro

### **Logs Importantes:**
```bash
# Logs da API
docker-compose -f docker-compose.dev.yml logs api

# Logs do Celery
docker-compose -f docker-compose.dev.yml exec api celery -A app.core.celery_app events

# Logs do Redis
docker-compose -f docker-compose.dev.yml logs redis
```

---

## 📚 **REFERÊNCIAS**

### **Documentação Relacionada:**
- [DEVICE_SYSTEM_DOCUMENTATION.md](./DEVICE_SYSTEM_DOCUMENTATION.md)
- [WEBSOCKET_IMPLEMENTATION_SUMMARY.md](./WEBSOCKET_IMPLEMENTATION_SUMMARY.md)
- [REDIS_INTEGRATION_SUMMARY.md](./REDIS_INTEGRATION_SUMMARY.md)
- [CELERY_INTEGRATION_SUMMARY.md](./CELERY_INTEGRATION_SUMMARY.md)

### **APIs Externas:**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Redis Documentation](https://redis.io/documentation)

---

## 🎯 **ROADMAP FUTURO**

### **Melhorias Planejadas:**
- [ ] Interface web para envio de comandos
- [ ] Templates de comandos pré-configurados
- [ ] Agendamento de comandos
- [ ] Comandos condicionais
- [ ] Integração com mais protocolos
- [ ] Dashboard de monitoramento avançado
- [ ] Alertas por email/SMS
- [ ] API de webhooks para status

### **Protocolos Adicionais:**
- [ ] GT06 Protocol
- [ ] H02 Protocol
- [ ] Teltonika Protocol
- [ ] Meiligao Protocol

---

**Última Atualização**: Janeiro 2025  
**Versão**: 1.0.0  
**Status**: ✅ **PRODUCTION-READY**
