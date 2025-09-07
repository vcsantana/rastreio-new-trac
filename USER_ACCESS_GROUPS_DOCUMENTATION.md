# Sistema de Usuários, Acessos e Grupos - Documentação Completa

## 📋 Visão Geral

O sistema Traccar implementa um modelo robusto de controle de acesso baseado em usuários, grupos hierárquicos e permissões granulares. Este documento detalha a estrutura completa do sistema de autenticação, autorização e gerenciamento de grupos.

## 🏗️ Arquitetura do Sistema

### **Componentes Principais**
- **Usuários**: Entidades que acessam o sistema
- **Grupos**: Organizações hierárquicas de recursos
- **Permissões**: Controle de acesso a recursos específicos
- **Hierarquia**: Sistema de herança de permissões

## 👥 Sistema de Usuários

### **Estrutura da Tabela `users`**

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Configurações adicionais
    phone VARCHAR(20),
    map VARCHAR(128),
    latitude VARCHAR(20) DEFAULT '0',
    longitude VARCHAR(20) DEFAULT '0',
    zoom INTEGER DEFAULT 0,
    coordinate_format VARCHAR(128),
    expiration_time TIMESTAMP WITH TIME ZONE,
    device_limit INTEGER DEFAULT -1,  -- -1 = ilimitado
    user_limit INTEGER DEFAULT 0,     -- 0 = sem direitos de gerenciamento
    device_readonly BOOLEAN DEFAULT FALSE,
    limit_commands BOOLEAN DEFAULT FALSE,
    disable_reports BOOLEAN DEFAULT FALSE,
    fixed_email BOOLEAN DEFAULT FALSE,
    poi_layer VARCHAR(512),
    attributes TEXT  -- JSON para atributos adicionais
);
```

### **Tipos de Usuários**

#### **1. Administradores (`is_admin = true`)**
- ✅ **Acesso Total**: Todos os recursos do sistema
- ✅ **Funcionalidades Completas**: Reports, logs, settings, etc.
- ✅ **Gerenciamento**: Criar, editar e deletar qualquer recurso
- ✅ **Controle de Usuários**: Gerenciar outros usuários e permissões

#### **2. Usuários Regulares (`is_admin = false`)**
- 🔒 **Acesso Limitado**: Apenas recursos dos grupos permitidos
- 🔒 **Funcionalidades Restritas**: Sem acesso a funcionalidades administrativas
- 🔒 **Gerenciamento Restrito**: Apenas recursos dos seus grupos

### **Usuários Atuais no Sistema**

| ID | Email | Nome | Admin | Ativo | Criado em |
|----|-------|------|-------|-------|-----------|
| 2 | admin@traccar.com | Admin User | ✅ | ✅ | 2025-09-05 |
| 5 | teste@example.com | Usuário Teste | ❌ | ✅ | 2025-09-05 |
| 7 | gerente@gerente.com | GERENTE PROTEGE | ✅ | ✅ | 2025-09-06 |
| 8 | vandecarlos.santana@gmail.com | VANDECARLOS CAVALCANTI DE SANTANA | ❌ | ✅ | 2025-09-06 |
| 9 | test@test.com | Test User | ❌ | ✅ | 2025-09-06 |
| 10 | admin2@test.com | Admin Test | ✅ | ✅ | 2025-09-06 |

## 🏢 Sistema de Grupos

### **Estrutura da Tabela `groups`**

```sql
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    disabled BOOLEAN DEFAULT FALSE,
    person_id INTEGER REFERENCES persons(id),
    parent_id INTEGER REFERENCES groups(id),  -- Hierarquia
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### **Hierarquia de Grupos**

#### **Estrutura Atual**
```
SUPORTE (ID: 8) - Grupo Raiz
├── CLEINTE A (ID: 13)
│   └── CLEINTE AA (ID: 14)
└── CLEINTE B (ID: 15)
```

#### **Grupos no Sistema**

| ID | Nome | Descrição | Pai | Nível | Status |
|----|------|-----------|-----|-------|--------|
| 8 | SUPORTE | GRUPO ADM DE TODOS DEVICE | - | 0 | ✅ Ativo |
| 13 | CLEINTE A | TESTE | 8 | 1 | ✅ Ativo |
| 14 | CLEINTE AA | - | 13 | 2 | ✅ Ativo |
| 15 | CLEINTE B | - | 8 | 1 | ✅ Ativo |

### **Características dos Grupos**

#### **1. Hierarquia**
- **Grupos Raiz**: Sem pai (`parent_id = null`)
- **Grupos Filhos**: Herdam de um grupo pai
- **Níveis**: Cada grupo tem um nível hierárquico (0 = raiz, 1 = primeiro nível, etc.)

#### **2. Herança de Permissões**
- Usuários com permissão em um grupo automaticamente têm acesso a todos os grupos filhos
- A herança é recursiva (grupos filhos de grupos filhos também são acessíveis)
- Administradores têm acesso a todos os grupos independentemente da hierarquia

#### **3. Validações de Segurança**
- Prevenção de referências circulares
- Validação de permissões para criação de grupos filhos
- Verificação de existência de grupos pai

## 🔐 Sistema de Permissões

### **Tabelas de Permissões**

#### **1. Permissões de Grupo (`user_group_permissions`)**
```sql
CREATE TABLE user_group_permissions (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, group_id)
);
```

#### **2. Permissões de Dispositivo (`user_device_permissions`)**
```sql
CREATE TABLE user_device_permissions (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, device_id)
);
```

#### **3. Gerenciamento de Usuários (`user_managed_users`)**
```sql
CREATE TABLE user_managed_users (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    managed_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, managed_user_id)
);
```

### **Permissões Atuais no Sistema**

#### **Permissões de Grupo**
| Usuário | Email | Grupo | Nome do Grupo |
|---------|-------|-------|---------------|
| 2 | admin@traccar.com | 8 | SUPORTE |
| 8 | vandecarlos.santana@gmail.com | 15 | CLEINTE B |

#### **Análise de Acesso**
- **Admin User (ID: 2)**: Tem acesso ao grupo SUPORTE e todos os seus filhos (CLEINTE A, CLEINTE AA, CLEINTE B)
- **VANDECARLOS (ID: 8)**: Tem acesso apenas ao grupo CLEINTE B

## 📱 Recursos e Associações

### **Dispositivos e Grupos**

| Dispositivo | Unique ID | Grupo | Nome do Grupo | Pessoa |
|-------------|-----------|-------|---------------|--------|
| Test Device | TEST123 | - | - | - |
| 47733387-iPhone | 47733387 | 15 | CLEINTE B | - |

### **Análise de Acesso aos Dispositivos**

#### **Usuário Admin (ID: 2)**
- ✅ **Test Device**: Acesso (sem grupo - admin vê todos)
- ✅ **47733387-iPhone**: Acesso (grupo CLEINTE B - herda de SUPORTE)

#### **Usuário VANDECARLOS (ID: 8)**
- ❌ **Test Device**: Sem acesso (sem grupo e usuário não tem permissão global)
- ✅ **47733387-iPhone**: Acesso (grupo CLEINTE B - permissão direta)

#### **Usuários sem Permissões (IDs: 5, 7, 9, 10)**
- ❌ **Test Device**: Sem acesso
- ❌ **47733387-iPhone**: Sem acesso

## 🔧 API Endpoints

### **Autenticação**

#### **Login**
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Resposta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### **Registro**
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "password123",
  "name": "New User",
  "is_admin": false
}
```

### **Gerenciamento de Usuários**

#### **Listar Usuários**
```http
GET /api/users/
Authorization: Bearer <token>
```

#### **Obter Usuário Específico**
```http
GET /api/users/{user_id}
Authorization: Bearer <token>
```

#### **Atualizar Usuário**
```http
PUT /api/users/{user_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Updated Name",
  "is_active": true
}
```

### **Gerenciamento de Grupos**

#### **Listar Grupos**
```http
GET /api/groups/
Authorization: Bearer <token>
```

**Resposta:**
```json
[
  {
    "id": 8,
    "name": "SUPORTE",
    "description": "GRUPO ADM DE TODOS DEVICE",
    "parent_id": null,
    "parent_name": null,
    "level": 0,
    "children_count": 2,
    "disabled": false,
    "created_at": "2025-09-06T19:20:59.038177Z"
  }
]
```

#### **Criar Grupo**
```http
POST /api/groups/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Novo Grupo",
  "description": "Descrição do grupo",
  "parent_id": 8,
  "disabled": false
}
```

### **Permissões**

#### **Obter Permissões do Usuário**
```http
GET /api/users/{user_id}/permissions
Authorization: Bearer <token>
```

**Resposta:**
```json
{
  "user_id": 8,
  "group_permissions": [
    {
      "group_id": 15,
      "group_name": "CLEINTE B",
      "level": 1
    }
  ],
  "device_permissions": [],
  "managed_users": []
}
```

#### **Atualizar Permissões**
```http
PUT /api/users/{user_id}/permissions
Authorization: Bearer <token>
Content-Type: application/json

{
  "group_permissions": [15, 13],
  "device_permissions": [12],
  "managed_users": [9]
}
```

## 🎯 Regras de Negócio

### **1. Controle de Acesso**

#### **Usuários Admin**
- ✅ Acesso total a todos os recursos
- ✅ Todas as funcionalidades administrativas
- ✅ Gerenciamento completo do sistema
- ✅ Não sujeitos a restrições de grupo

#### **Usuários Regulares**
- 🔒 Acesso limitado aos recursos dos grupos permitidos
- 🔒 Sem acesso a funcionalidades administrativas
- 🔒 Gerenciamento restrito aos recursos permitidos
- 🔒 Sujeitos a restrições de grupo

### **2. Herança de Permissões**

#### **Algoritmo de Herança**
1. **Usuários Admin**: Acesso a todos os grupos
2. **Usuários Regulares**: 
   - Acesso direto aos grupos com permissão explícita
   - Acesso automático a todos os grupos filhos (recursivo)

#### **Exemplo Prático**
```
Usuário com permissão no grupo SUPORTE (ID: 8):
├── Acesso direto: SUPORTE
├── Acesso herdado: CLEINTE A (filho de SUPORTE)
├── Acesso herdado: CLEINTE AA (filho de CLEINTE A)
└── Acesso herdado: CLEINTE B (filho de SUPORTE)
```

### **3. Validações de Segurança**

#### **Criação de Grupos**
- Nome do grupo deve ser único
- Grupo pai deve existir
- Usuário deve ter permissão para criar grupos sob o grupo pai especificado
- Prevenção de referências circulares

#### **Atribuição de Permissões**
- Usuário deve ter permissão para gerenciar o usuário alvo
- Grupos devem existir
- Dispositivos devem existir
- Validação de integridade referencial

## 🧪 Cenários de Teste

### **Cenário 1: Usuário Admin**
```bash
# Login como admin
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@traccar.com", "password": "admin"}' | jq -r '.access_token')

# Listar todos os dispositivos (deve retornar todos)
curl -X GET "http://localhost:8000/api/devices/" \
  -H "Authorization: Bearer $TOKEN" | jq 'length'
# Resultado esperado: 2 (todos os dispositivos)
```

### **Cenário 2: Usuário com Permissão de Grupo**
```bash
# Login como usuário com permissão
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "vandecarlos.santana@gmail.com", "password": "password"}' | jq -r '.access_token')

# Listar dispositivos (deve retornar apenas do grupo CLEINTE B)
curl -X GET "http://localhost:8000/api/devices/" \
  -H "Authorization: Bearer $TOKEN" | jq 'length'
# Resultado esperado: 1 (apenas dispositivo do grupo CLEINTE B)
```

### **Cenário 3: Usuário sem Permissões**
```bash
# Login como usuário sem permissões
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "test123"}' | jq -r '.access_token')

# Listar dispositivos (deve retornar lista vazia)
curl -X GET "http://localhost:8000/api/devices/" \
  -H "Authorization: Bearer $TOKEN" | jq 'length'
# Resultado esperado: 0 (lista vazia - sem permissões)
```

## 📊 Queries SQL Úteis

### **1. Usuários e Suas Permissões**
```sql
SELECT 
    u.id,
    u.name,
    u.email,
    u.is_admin,
    u.is_active,
    COUNT(ugp.group_id) as group_permissions_count,
    STRING_AGG(g.name, ', ') as accessible_groups
FROM users u
LEFT JOIN user_group_permissions ugp ON u.id = ugp.user_id
LEFT JOIN groups g ON ugp.group_id = g.id
GROUP BY u.id, u.name, u.email, u.is_admin, u.is_active
ORDER BY u.id;
```

### **2. Hierarquia de Grupos**
```sql
WITH RECURSIVE group_hierarchy AS (
    -- Grupos raiz
    SELECT id, name, parent_id, 0 as level, name as path
    FROM groups 
    WHERE parent_id IS NULL
    
    UNION ALL
    
    -- Grupos filhos
    SELECT g.id, g.name, g.parent_id, gh.level + 1, gh.path || ' > ' || g.name
    FROM groups g
    JOIN group_hierarchy gh ON g.parent_id = gh.id
)
SELECT id, name, parent_id, level, path
FROM group_hierarchy
ORDER BY level, name;
```

### **3. Dispositivos por Grupo e Usuário**
```sql
SELECT 
    d.id,
    d.name,
    d.unique_id,
    g.name as group_name,
    p.name as person_name,
    COUNT(udp.user_id) as user_permissions_count
FROM devices d
LEFT JOIN groups g ON d.group_id = g.id
LEFT JOIN persons p ON d.person_id = p.id
LEFT JOIN user_device_permissions udp ON d.id = udp.device_id
GROUP BY d.id, d.name, d.unique_id, g.name, p.name
ORDER BY d.id;
```

### **4. Usuários com Acesso a Dispositivos Específicos**
```sql
SELECT 
    u.name as user_name,
    u.email,
    d.name as device_name,
    d.unique_id,
    g.name as group_name,
    CASE 
        WHEN u.is_admin THEN 'Admin Access'
        WHEN udp.device_id IS NOT NULL THEN 'Direct Device Permission'
        WHEN ugp.group_id IS NOT NULL THEN 'Group Permission'
        ELSE 'No Access'
    END as access_type
FROM users u
CROSS JOIN devices d
LEFT JOIN user_device_permissions udp ON u.id = udp.user_id AND d.id = udp.device_id
LEFT JOIN user_group_permissions ugp ON u.id = ugp.user_id AND d.group_id = ugp.group_id
WHERE u.is_admin = true 
   OR udp.device_id IS NOT NULL 
   OR ugp.group_id IS NOT NULL
ORDER BY d.name, u.name;
```

## 🔍 Monitoramento e Auditoria

### **Logs de Acesso**
```sql
-- Usuários ativos por período
SELECT 
    DATE(created_at) as date,
    COUNT(*) as new_users,
    COUNT(CASE WHEN is_admin THEN 1 END) as new_admins
FROM users 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### **Permissões por Usuário**
```sql
-- Resumo de permissões
SELECT 
    u.name,
    u.email,
    u.is_admin,
    COUNT(DISTINCT ugp.group_id) as group_permissions,
    COUNT(DISTINCT udp.device_id) as device_permissions,
    COUNT(DISTINCT umu.managed_user_id) as managed_users
FROM users u
LEFT JOIN user_group_permissions ugp ON u.id = ugp.user_id
LEFT JOIN user_device_permissions udp ON u.id = udp.user_id
LEFT JOIN user_managed_users umu ON u.id = umu.user_id
GROUP BY u.id, u.name, u.email, u.is_admin
ORDER BY u.is_admin DESC, u.name;
```

## 🚀 Melhorias Futuras

### **Funcionalidades Planejadas**
- [ ] **Permissões Granulares**: Controle específico por ação (criar, editar, deletar, visualizar)
- [ ] **Grupos Temporários**: Permissões com data de expiração
- [ ] **Auditoria Completa**: Log de todas as ações por usuário
- [ ] **Notificações**: Alertas de tentativas de acesso negado
- [ ] **SSO Integration**: Integração com sistemas de autenticação externos
- [ ] **Multi-tenant**: Suporte a múltiplas organizações

### **Melhorias Técnicas**
- [ ] **Cache de Permissões**: Otimização de performance com Redis
- [ ] **Validação Frontend**: Verificações adicionais no cliente
- [ ] **Testes Automatizados**: Cobertura completa de cenários
- [ ] **Documentação API**: Swagger atualizado com permissões
- [ ] **Backup Automático**: Sistema de backup das permissões

## 📚 Referências

### **Arquivos Relacionados**
- **Backend**: `traccar-python-api/app/models/user.py`
- **Grupos**: `traccar-python-api/app/models/group.py`
- **Permissões**: `traccar-python-api/app/models/user_permission.py`
- **API Usuários**: `traccar-python-api/app/api/users.py`
- **API Grupos**: `traccar-python-api/app/api/groups.py`
- **Frontend**: `traccar-react-frontend/src/hooks/useUsers.ts`

### **Documentação Relacionada**
- [Sistema de Permissões](./USER_PERMISSIONS_SYSTEM.md)
- [Sistema de Grupos Hierárquicos](./GROUP_HIERARCHY_SYSTEM.md)
- [Sistema de Dispositivos](./DEVICE_SYSTEM_DOCUMENTATION.md)

---

**Última Atualização**: 06 de Janeiro de 2025  
**Versão**: 1.0.0  
**Status**: ✅ **SISTEMA COMPLETO E FUNCIONANDO**
