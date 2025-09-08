# Sistema de Dispositivos - Documentação Completa

## 📋 Visão Geral

O sistema de dispositivos permite gerenciar dispositivos GPS, smartphones e outros equipamentos de rastreamento no Traccar. Cada dispositivo pode ser associado a grupos, pessoas e possui informações específicas como placa, categoria e protocolo.

### ✅ Status do Sistema
- **Dispositivos Registrados**: ✅ Funcionando
- **Dispositivos Desconhecidos**: ✅ Funcionando
- **Sistema de Logs**: ✅ Funcionando (posições sendo salvas)
- **Real Device ID**: ✅ Exibido corretamente
- **Criação de Dispositivos**: ✅ Funcionando
- **Linkagem de Dispositivos**: ✅ Funcionando

## 🏗️ Arquitetura do Sistema

### Backend (Python/FastAPI)
- **Modelo**: `app/models/device.py`
- **API**: `app/api/devices.py`
- **Schemas**: `app/schemas/device.py`
- **Banco**: PostgreSQL com tabela `devices`
- **Protocolos**: Suntech, OsmAnd (ver documentação específica)

### Frontend (React/TypeScript)
- **Hook**: `src/hooks/useDevices.ts`
- **Página**: `src/pages/Devices.tsx`
- **Componente**: `src/components/common/DeviceDialog.tsx`

## 🗄️ Estrutura do Banco de Dados

### Tabela `devices`

```sql
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    unique_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'unknown',
    protocol VARCHAR(50),
    last_update TIMESTAMP WITH TIME ZONE,
    position_id INTEGER,
    phone VARCHAR(50),
    model VARCHAR(255),
    contact VARCHAR(255),
    category VARCHAR(50),
    license_plate VARCHAR(20),           -- NOVO CAMPO
    disabled BOOLEAN DEFAULT FALSE,
    group_id INTEGER REFERENCES groups(id),
    person_id INTEGER REFERENCES persons(id), -- NOVO CAMPO
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    attributes TEXT
);
```

### Relacionamentos
- **groups**: Um dispositivo pode pertencer a um grupo
- **persons**: Um dispositivo pode ser associado a uma pessoa
- **positions**: Um dispositivo pode ter múltiplas posições
- **events**: Um dispositivo pode gerar múltiplos eventos

## 📊 Modelo de Dados

### Device (Backend)
```python
class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    unique_id = Column(String(255), unique=True, index=True, nullable=False)
    status = Column(String(50), default="unknown")
    protocol = Column(String(50))
    last_update = Column(DateTime(timezone=True))
    position_id = Column(Integer, ForeignKey("positions.id"))
    phone = Column(String(50))
    model = Column(String(255))
    contact = Column(String(255))
    category = Column(String(50))
    license_plate = Column(String(20))  # NOVO
    disabled = Column(Boolean, default=False)
    group_id = Column(Integer, ForeignKey("groups.id"))
    person_id = Column(Integer, ForeignKey("persons.id"))  # NOVO
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    attributes = Column(Text)
    
    # Relacionamentos
    positions = relationship("Position", back_populates="device")
    events = relationship("Event", back_populates="device")
    last_position = relationship("Position", foreign_keys=[position_id])
    group = relationship("Group", back_populates="devices")
    person = relationship("Person", back_populates="devices")  # NOVO
```

### Device (Frontend)
```typescript
export interface Device {
  id: number;
  name: string;
  unique_id: string;
  phone?: string;
  model?: string;
  contact?: string;
  category?: string;
  license_plate?: string;  // NOVO
  disabled: boolean;
  group_id?: number;
  person_id?: number;      // NOVO
  status?: string;
  protocol?: string;
  last_update?: string;
  created_at: string;
  group_name?: string;
  person_name?: string;    // NOVO
}
```

## 🔌 API Endpoints

### Base URL
```
http://localhost:8000/api/devices/
```

### Endpoints Disponíveis

#### 1. Listar Dispositivos
```http
GET /api/devices/
Authorization: Bearer <token>
```

**Resposta:**
```json
[
  {
    "id": 1,
    "name": "Carro João",
    "unique_id": "ABC123",
    "phone": "+5511999999999",
    "model": "GT06",
    "contact": "João Silva",
    "category": "car",
    "license_plate": "ABC-1234",
    "disabled": false,
    "group_id": 1,
    "person_id": 2,
    "status": "online",
    "protocol": "gt06",
    "last_update": "2025-01-06T20:25:33Z",
    "created_at": "2025-01-06T20:25:33Z",
    "group_name": "Frota Principal",
    "person_name": "João Silva"
  }
]
```

#### 2. Criar Dispositivo
```http
POST /api/devices/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Novo Dispositivo",
  "unique_id": "UNIQUE123",
  "category": "iphone",
  "license_plate": "XYZ-9876",
  "phone": "+5511888888888",
  "group_id": 1,
  "person_id": 2
}
```

#### 3. Obter Dispositivo Específico
```http
GET /api/devices/{device_id}
Authorization: Bearer <token>
```

#### 4. Atualizar Dispositivo
```http
PUT /api/devices/{device_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Nome Atualizado",
  "license_plate": "NOVA-1234"
}
```

#### 5. Deletar Dispositivo
```http
DELETE /api/devices/{device_id}
Authorization: Bearer <token>
```

## 🎨 Interface do Usuário

### Página de Dispositivos (`/devices`)

#### Funcionalidades Principais
- ✅ **Listagem**: Tabela com todos os dispositivos
- ✅ **Criação**: Formulário para adicionar novos dispositivos
- ✅ **Edição**: Formulário para modificar dispositivos existentes
- ✅ **Exclusão**: Confirmação e remoção de dispositivos
- ✅ **Ativação/Desativação**: Toggle de status do dispositivo
- ✅ **Filtros**: Busca e filtros avançados

#### Estrutura da Tabela
| Coluna | Descrição | Tipo |
|--------|-----------|------|
| Name | Nome do dispositivo | String |
| Unique ID | Identificador único | String |
| Status | Status atual (online/offline/disabled) | Chip |
| Protocol | Protocolo de comunicação | Chip |
| Category | Categoria do dispositivo | Chip |
| License Plate | Placa do veículo | String |
| Group | Grupo associado | Chip |
| Person | Pessoa associada | String |
| Last Update | Última atualização | DateTime |
| Actions | Ações disponíveis | Icons |

#### Filtros Disponíveis
- **Busca**: Por nome ou Unique ID
- **Status**: Online, Offline, Disabled, Enabled
- **Protocolo**: Filtro por protocolo específico
- **Categoria**: Car, Truck, iPhone, Android, etc.
- **Grupo**: Filtro por grupo específico
- **Pessoa**: Filtro por pessoa específica

### Formulário de Dispositivo

#### Campos Obrigatórios
- **Nome**: Nome amigável do dispositivo
- **Unique ID**: Identificador único do dispositivo GPS

#### Campos Opcionais
- **Protocolo**: Protocolo de comunicação (Suntech, GT06, H02, etc.)
- **Categoria**: Tipo do dispositivo (Car, Truck, iPhone, Android, etc.)
- **Modelo**: Modelo do dispositivo
- **Contato**: Pessoa de contato
- **Telefone**: Número de telefone
- **Placa**: Placa do veículo (NOVO)
- **Grupo**: Grupo ao qual pertence
- **Pessoa**: Pessoa associada (NOVO)

#### Categorias Disponíveis
```typescript
const CATEGORY_OPTIONS = [
  { value: 'car', label: 'Car' },
  { value: 'truck', label: 'Truck' },
  { value: 'motorcycle', label: 'Motorcycle' },
  { value: 'van', label: 'Van' },
  { value: 'bus', label: 'Bus' },
  { value: 'boat', label: 'Boat' },
  { value: 'iphone', label: 'iPhone' },      // NOVO
  { value: 'android', label: 'Android' },    // NOVO
  { value: 'other', label: 'Other' }
];
```

#### Protocolos Suportados
```typescript
const PROTOCOL_OPTIONS = [
  { value: 'suntech', label: 'Suntech' },
  { value: 'gt06', label: 'GT06' },
  { value: 'h02', label: 'H02' },
  { value: 'meiligao', label: 'Meiligao' },
  { value: 'teltonika', label: 'Teltonika' },
  { value: 'concox', label: 'Concox' },
  { value: 'queclink', label: 'Queclink' },
  { value: 'nmea', label: 'NMEA' }
];
```

## 🔧 Hook useDevices

### Funcionalidades
```typescript
const {
  devices,           // Lista de dispositivos
  loading,           // Estado de carregamento
  error,             // Erro atual
  fetchDevices,      // Carregar dispositivos
  createDevice,      // Criar dispositivo
  updateDevice,      // Atualizar dispositivo
  deleteDevice,      // Deletar dispositivo
  toggleDeviceStatus // Ativar/desativar dispositivo
} = useDevices();
```

### Exemplo de Uso
```typescript
// Carregar dispositivos
useEffect(() => {
  fetchDevices();
}, [fetchDevices]);

// Criar dispositivo
const handleCreate = async () => {
  const newDevice = await createDevice({
    name: "Novo Dispositivo",
    unique_id: "UNIQUE123",
    category: "iphone",
    license_plate: "ABC-1234"
  });
  
  if (newDevice) {
    console.log("Dispositivo criado:", newDevice);
  }
};

// Atualizar dispositivo
const handleUpdate = async (id: number) => {
  const updated = await updateDevice(id, {
    name: "Nome Atualizado",
    license_plate: "XYZ-9876"
  });
  
  if (updated) {
    console.log("Dispositivo atualizado:", updated);
  }
};
```

## 🚀 Como Usar

### 1. Acessar a Página
```
http://localhost:3000/devices
```

### 2. Criar um Dispositivo
1. Clique em "Add Device"
2. Preencha os campos obrigatórios (Nome e Unique ID)
3. Selecione categoria (ex: iPhone, Android, Car)
4. Adicione placa se for um veículo
5. Associe a um grupo e/ou pessoa se necessário
6. Clique em "Save"

### 3. Editar um Dispositivo
1. Clique no ícone de edição na tabela
2. Modifique os campos desejados
3. Clique em "Save"

### 4. Filtrar Dispositivos
1. Clique em "Filters" para expandir
2. Use os filtros disponíveis:
   - Busca por texto
   - Filtro por status
   - Filtro por protocolo
   - Filtro por categoria
   - Filtro por grupo
   - Filtro por pessoa
3. Clique em "Clear" para limpar filtros

### 5. Gerenciar Status
- **Ativar**: Clique no ícone de ativação
- **Desativar**: Clique no ícone de desativação
- **Deletar**: Clique no ícone de lixeira

## 🔒 Permissões e Segurança

### Autenticação
- Todos os endpoints requerem token JWT
- Token deve ser incluído no header: `Authorization: Bearer <token>`

### Validações
- **Unique ID**: Deve ser único no sistema
- **Nome**: Campo obrigatório
- **Foreign Keys**: Validação de existência de grupos e pessoas

### Erros Comuns
```json
// Unique ID duplicado
{
  "detail": "Device with this unique ID already exists"
}

// Dispositivo não encontrado
{
  "detail": "Device not found"
}

// Token inválido
{
  "detail": "Could not validate credentials"
}
```

## 📈 Status dos Dispositivos

### Estados Possíveis
- **online**: Dispositivo conectado e enviando dados
- **offline**: Dispositivo desconectado
- **unknown**: Status não determinado
- **disabled**: Dispositivo desabilitado pelo usuário

### Indicadores Visuais
- 🟢 **Verde**: Online
- 🔴 **Vermelho**: Offline
- ⚫ **Cinza**: Desabilitado
- ⚪ **Branco**: Status desconhecido

## 🔄 WebSocket Integration

### Atualizações em Tempo Real
O sistema suporta atualizações via WebSocket para:
- Mudanças de status do dispositivo
- Novas posições recebidas
- Eventos gerados pelo dispositivo

### Broadcast de Eventos
```python
# Backend - Broadcast de mudança de status
await websocket_service.broadcast_device_status_update(device)
```

## 🧪 Testes

### Teste da API
```bash
# Obter token
TOKEN=$(curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@traccar.com", "password": "admin123"}' \
  | jq -r '.access_token')

# Listar dispositivos
curl -X GET "http://localhost:8000/api/devices/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Criar dispositivo
curl -X POST "http://localhost:8000/api/devices/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Device",
    "unique_id": "TEST123",
    "category": "iphone",
    "license_plate": "ABC-1234"
  }'
```

### Teste do Frontend
1. Acesse `http://localhost:3000/devices`
2. Verifique se os dispositivos carregam automaticamente
3. Teste criar um novo dispositivo
4. Teste editar um dispositivo existente
5. Teste os filtros
6. Teste ativar/desativar dispositivos

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. "createDevice is not a function"
**Causa**: Hook useDevices não implementado completamente
**Solução**: Verificar se todas as funções CRUD estão exportadas

#### 2. "Could not validate credentials"
**Causa**: Token JWT expirado ou inválido
**Solução**: Fazer login novamente

#### 3. "Device with this unique ID already exists"
**Causa**: Unique ID duplicado
**Solução**: Usar um Unique ID diferente

#### 4. Dispositivos não carregam
**Causa**: Problema na API ou autenticação
**Solução**: Verificar console do navegador e logs da API

### Logs Úteis
```bash
# Logs da API
docker-compose -f docker-compose.dev.yml logs api

# Logs do Frontend
docker-compose -f docker-compose.dev.yml logs frontend

# Logs do Banco
docker-compose -f docker-compose.dev.yml logs postgres
```

## 📚 Referências

### Arquivos Relacionados
- **Backend**: `traccar-python-api/app/models/device.py`
- **API**: `traccar-python-api/app/api/devices.py`
- **Schemas**: `traccar-python-api/app/schemas/device.py`
- **Frontend Hook**: `traccar-react-frontend/src/hooks/useDevices.ts`
- **Página**: `traccar-react-frontend/src/pages/Devices.tsx`
- **Componente**: `traccar-react-frontend/src/components/common/DeviceDialog.tsx`

### Documentação Relacionada
- [Sistema de Grupos](./GROUP_HIERARCHY_SYSTEM.md)
- [Sistema de Pessoas](./USER_MANAGEMENT_DEBUG_GUIDE.md)
- [Guia de Acesso PostgreSQL](./POSTGRESQL_ACCESS_GUIDE.md)

## 🔄 Sistema de Dispositivos Desconhecidos

### Visão Geral
O sistema de dispositivos desconhecidos permite gerenciar dispositivos que se conectam ao servidor mas ainda não foram registrados no sistema.

### Fluxo de Funcionamento
1. **Conexão**: Dispositivo GPS se conecta nas portas 5011 (Suntech) ou 5055 (OsmAnd)
2. **Detecção Automática**: Sistema cria registro em `unknown_devices` automaticamente
3. **Exibição**: Dispositivo aparece na página `/unknown-devices`
4. **Registro**: Usuário pode criar um novo dispositivo ou linkar a um existente

### API Endpoints para Dispositivos Desconhecidos

#### Listar Dispositivos Desconhecidos
```http
GET /api/unknown-devices/
Authorization: Bearer <token>
```

#### Criar Dispositivo a partir de Desconhecido
```http
POST /api/unknown-devices/{unknown_device_id}/create-device
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Nome do Dispositivo",
  "model": "Modelo",
  "contact": "Contato",
  "category": "car",
  "phone": "+5511999999999",
  "license_plate": "ABC-1234"
}
```

#### Linkar a Dispositivo Existente
```http
POST /api/unknown-devices/{unknown_device_id}/register
Authorization: Bearer <token>
Content-Type: application/json

{
  "device_id": 123
}
```

### Interface do Usuário
- **Página**: `http://localhost:3000/unknown-devices`
- **Ações Disponíveis**:
  - 👁️ **Ver Detalhes**: Informações do dispositivo
  - ➕ **Criar Dispositivo**: Criar novo dispositivo registrado
  - 🔗 **Linkar Dispositivo**: Associar a dispositivo existente
  - 🗑️ **Deletar**: Remover dispositivo desconhecido

## 🔧 Correções Recentes Implementadas

### 1. Sistema de Logs para Dispositivos Desconhecidos
- **Arquivo**: `app/protocols/suntech.py`
- **Problema**: Posições não eram salvas para dispositivos desconhecidos
- **Causa**: Método `_parse_legacy_message` não incluía latitude/longitude obrigatórios
- **Solução**: Adicionado parsing de coordenadas no método legacy
- **Status**: ✅ Corrigido

### 2. Real Device ID em Posições
- **Arquivo**: `app/protocols/suntech.py`
- **Problema**: Real Device ID não aparecia nos atributos das posições
- **Causa**: `client_info` não era passado para `_parse_location_message`
- **Solução**: Corrigido passagem de parâmetros e parsing de datetime
- **Status**: ✅ Corrigido

### 3. Validação Pydantic
- **Arquivo**: `app/protocols/suntech.py`
- **Problema**: Erro "Field required" para latitude/longitude
- **Causa**: Campos obrigatórios não estavam sendo preenchidos
- **Solução**: Garantido que todos os campos obrigatórios sejam preenchidos
- **Status**: ✅ Corrigido

### 4. Salvamento Contínuo de Posições
- **Arquivo**: `app/protocols/suntech.py`
- **Problema**: Sistema só salvava posições uma vez (na criação/linkagem)
- **Causa**: Suporte limitado a prefixos numéricos e referências incorretas de variáveis
- **Solução**: Adicionado suporte a prefixos numéricos e corrigido referências de variáveis
- **Status**: ✅ Corrigido

### 5. Suporte a Prefixos Numéricos
- **Arquivo**: `app/protocols/suntech.py`
- **Problema**: Erro "Could not extract device ID from prefix" para prefixos como `47733387`
- **Causa**: Método só suportava formato ST (`ST300STT`)
- **Solução**: Adicionado suporte para prefixos numéricos
- **Status**: ✅ Corrigido

## 📡 Protocolos Suportados

### **Protocolo Suntech**
- **Porta**: 5011 (TCP)
- **Formatos**: Universal (ST) e Legacy (numérico)
- **Status**: ✅ 100% funcional
- **Documentação**: [SUNTECH_PROTOCOL_DOCUMENTATION.md](./SUNTECH_PROTOCOL_DOCUMENTATION.md)
- **Recursos**:
  - Suporte a prefixos ST (`ST300STT`) e numéricos (`47733387`)
  - Salvamento contínuo de posições
  - Real Device ID nos atributos
  - Dispositivos desconhecidos
  - Alarmes e alertas

### **Protocolo OsmAnd**
- **Porta**: 5055 (HTTP)
- **Formato**: HTTP POST
- **Status**: ✅ Implementado
- **Documentação**: [OSMAND_PROTOCOL_IMPLEMENTATION.md](./OSMAND_PROTOCOL_IMPLEMENTATION.md)

## 🎯 Roadmap

### Funcionalidades Futuras
- [ ] **Histórico de Posições**: Visualização de trajetos
- [ ] **Alertas**: Configuração de alertas por dispositivo
- [ ] **Relatórios**: Relatórios de uso e performance
- [ ] **Importação em Lote**: Upload de múltiplos dispositivos
- [ ] **Templates**: Templates para tipos de dispositivo
- [ ] **Geofencing**: Criação de zonas geográficas
- [ ] **Comandos**: Envio de comandos para dispositivos
- [ ] **Manutenção**: Agendamento de manutenção

### Melhorias Técnicas
- [ ] **Cache**: Implementar cache para melhor performance
- [ ] **Paginação**: Paginação para grandes volumes de dados
- [ ] **Busca Avançada**: Busca full-text
- [ ] **Exportação**: Exportar dados em CSV/Excel
- [ ] **Backup**: Sistema de backup automático
- [ ] **Monitoramento**: Métricas de performance
- [ ] **Logs**: Sistema de auditoria completo

---

**Última Atualização**: 06 de Janeiro de 2025
**Versão**: 1.0.0
**Autor**: Sistema Traccar
