# Guia Prático de Gerenciamento de Usuários e Grupos

## 📋 Visão Geral

Este guia prático fornece instruções passo a passo para gerenciar usuários, grupos e permissões no sistema Traccar, incluindo exemplos práticos e comandos úteis.

## 🚀 Início Rápido

### **1. Acessar o Sistema**
```bash
# URL do sistema
http://localhost:3000

# Login como administrador
Email: admin@traccar.com
Senha: admin
```

### **2. Verificar Status Atual**
```bash
# Verificar usuários no banco
docker compose -f docker-compose.dev.yml exec postgres psql -U traccar -d traccar -c "SELECT id, email, name, is_admin, is_active FROM users ORDER BY id;"

# Verificar grupos
docker compose -f docker-compose.dev.yml exec postgres psql -U traccar -d traccar -c "SELECT id, name, parent_id, disabled FROM groups ORDER BY id;"

# Verificar permissões
docker compose -f docker-compose.dev.yml exec postgres psql -U traccar -d traccar -c "SELECT ugp.user_id, u.name, ugp.group_id, g.name FROM user_group_permissions ugp JOIN users u ON ugp.user_id = u.id JOIN groups g ON ugp.group_id = g.id;"
```

## 👥 Gerenciamento de Usuários

### **Criar Novo Usuário**

#### **Via Interface Web**
1. Acesse `http://localhost:3000/users`
2. Clique em "Add User"
3. Preencha os dados:
   - **Name**: Nome completo
   - **Email**: Email único
   - **Password**: Senha segura
   - **Is Admin**: Marcar se for administrador
4. Clique em "Save"

#### **Via API**
```bash
# Criar usuário regular
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "novo@usuario.com",
    "password": "senha123",
    "name": "Novo Usuário",
    "is_admin": false
  }'

# Criar usuário administrador
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@empresa.com",
    "password": "admin123",
    "name": "Admin Empresa",
    "is_admin": true
  }'
```

### **Atualizar Usuário**

#### **Via Interface Web**
1. Acesse `http://localhost:3000/users`
2. Clique no ícone de edição do usuário
3. Modifique os campos necessários
4. Clique em "Save"

#### **Via API**
```bash
# Obter token de admin
TOKEN=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@traccar.com", "password": "admin"}' | jq -r '.access_token')

# Atualizar usuário
curl -X PUT "http://localhost:8000/api/users/5" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nome Atualizado",
    "is_active": true
  }'
```

### **Desativar Usuário**
```bash
# Desativar usuário (não deletar)
curl -X PUT "http://localhost:8000/api/users/5" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'
```

### **Deletar Usuário**
```bash
# Deletar usuário permanentemente
curl -X DELETE "http://localhost:8000/api/users/5" \
  -H "Authorization: Bearer $TOKEN"
```

## 🏢 Gerenciamento de Grupos

### **Criar Novo Grupo**

#### **Via Interface Web**
1. Acesse `http://localhost:3000/groups`
2. Clique em "Add Group"
3. Preencha os dados:
   - **Name**: Nome do grupo
   - **Description**: Descrição opcional
   - **Parent Group**: Grupo pai (opcional)
   - **Person**: Pessoa responsável (opcional)
4. Clique em "Save"

#### **Via API**
```bash
# Criar grupo raiz
curl -X POST "http://localhost:8000/api/groups/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nova Empresa",
    "description": "Grupo para nova empresa cliente",
    "disabled": false
  }'

# Criar grupo filho
curl -X POST "http://localhost:8000/api/groups/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Frota A",
    "description": "Frota principal da empresa",
    "parent_id": 8,
    "disabled": false
  }'
```

### **Estrutura Hierárquica Recomendada**

```
EMPRESA PRINCIPAL
├── FROTA PRINCIPAL
│   ├── VEÍCULOS LEVES
│   └── VEÍCULOS PESADOS
├── FROTA RESERVA
└── FROTA ESPECIAL
    ├── AMBULÂNCIAS
    └── VEÍCULOS DE EMERGÊNCIA
```

### **Atualizar Grupo**
```bash
# Atualizar informações do grupo
curl -X PUT "http://localhost:8000/api/groups/8" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SUPORTE ATUALIZADO",
    "description": "Grupo de suporte técnico atualizado"
  }'
```

### **Desativar Grupo**
```bash
# Desativar grupo (não deletar)
curl -X PUT "http://localhost:8000/api/groups/8" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "disabled": true
  }'
```

## 🔐 Gerenciamento de Permissões

### **Atribuir Permissões de Grupo**

#### **Via Interface Web**
1. Acesse `http://localhost:3000/users`
2. Clique no usuário desejado
3. Vá para a aba "Permissions"
4. Selecione os grupos permitidos
5. Clique em "Save"

#### **Via API**
```bash
# Obter permissões atuais do usuário
curl -X GET "http://localhost:8000/api/users/8/permissions" \
  -H "Authorization: Bearer $TOKEN"

# Atualizar permissões
curl -X PUT "http://localhost:8000/api/users/8/permissions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_permissions": [8, 13, 15],
    "device_permissions": [],
    "managed_users": []
  }'
```

### **Atribuir Permissões de Dispositivo**
```bash
# Atribuir acesso direto a dispositivo específico
curl -X PUT "http://localhost:8000/api/users/8/permissions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_permissions": [15],
    "device_permissions": [12],
    "managed_users": []
  }'
```

### **Gerenciar Usuários Subordinados**
```bash
# Permitir que usuário gerencie outros usuários
curl -X PUT "http://localhost:8000/api/users/8/permissions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_permissions": [15],
    "device_permissions": [],
    "managed_users": [5, 9]
  }'
```

## 📊 Cenários Práticos

### **Cenário 1: Nova Empresa Cliente**

#### **Situação**
Uma nova empresa cliente precisa de acesso ao sistema com:
- 1 gerente (admin)
- 2 operadores (usuários regulares)
- 3 grupos de dispositivos (Frota Principal, Frota Reserva, Frota Especial)

#### **Passos**

1. **Criar Grupo Principal**
```bash
curl -X POST "http://localhost:8000/api/groups/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "EMPRESA ABC",
    "description": "Cliente ABC - Contrato 2025"
  }'
```

2. **Criar Subgrupos**
```bash
# Obter ID do grupo principal (assumindo ID 16)
GROUP_ID=16

# Frota Principal
curl -X POST "http://localhost:8000/api/groups/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Frota Principal\",
    \"description\": \"Veículos principais da empresa\",
    \"parent_id\": $GROUP_ID
  }"

# Frota Reserva
curl -X POST "http://localhost:8000/api/groups/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Frota Reserva\",
    \"description\": \"Veículos de backup\",
    \"parent_id\": $GROUP_ID
  }"

# Frota Especial
curl -X POST "http://localhost:8000/api/groups/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Frota Especial\",
    \"description\": \"Veículos especiais\",
    \"parent_id\": $GROUP_ID
  }"
```

3. **Criar Usuários**
```bash
# Gerente (admin)
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "gerente@empresaabc.com",
    "password": "gerente123",
    "name": "João Silva - Gerente",
    "is_admin": true
  }'

# Operador 1
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "operador1@empresaabc.com",
    "password": "op123",
    "name": "Maria Santos - Operador",
    "is_admin": false
  }'

# Operador 2
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "operador2@empresaabc.com",
    "password": "op456",
    "name": "Pedro Costa - Operador",
    "is_admin": false
  }'
```

4. **Atribuir Permissões**
```bash
# Operador 1 - acesso a Frota Principal
curl -X PUT "http://localhost:8000/api/users/[ID_OPERADOR1]/permissions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_permissions": [17]  // ID da Frota Principal
  }'

# Operador 2 - acesso a Frota Reserva
curl -X PUT "http://localhost:8000/api/users/[ID_OPERADOR2]/permissions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_permissions": [18]  // ID da Frota Reserva
  }'
```

### **Cenário 2: Reorganização de Grupos**

#### **Situação**
Uma empresa precisa reorganizar sua estrutura de grupos:
- Mover alguns dispositivos para um novo grupo
- Reatribuir permissões de usuários
- Manter histórico de mudanças

#### **Passos**

1. **Criar Novo Grupo**
```bash
curl -X POST "http://localhost:8000/api/groups/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nova Estrutura",
    "description": "Grupo reorganizado",
    "parent_id": 8
  }'
```

2. **Mover Dispositivos**
```bash
# Atualizar dispositivo para novo grupo
curl -X PUT "http://localhost:8000/api/devices/12" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": 19  // ID do novo grupo
  }'
```

3. **Reatribuir Permissões**
```bash
# Atualizar permissões do usuário
curl -X PUT "http://localhost:8000/api/users/8/permissions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_permissions": [15, 19]  // Grupos antigo e novo
  }'
```

## 🔍 Monitoramento e Auditoria

### **Verificar Acessos de Usuário**
```sql
-- Usuários e seus grupos acessíveis
SELECT 
    u.name as usuario,
    u.email,
    u.is_admin,
    COUNT(ugp.group_id) as grupos_diretos,
    STRING_AGG(g.name, ', ') as grupos_acessiveis
FROM users u
LEFT JOIN user_group_permissions ugp ON u.id = ugp.user_id
LEFT JOIN groups g ON ugp.group_id = g.id
GROUP BY u.id, u.name, u.email, u.is_admin
ORDER BY u.is_admin DESC, u.name;
```

### **Verificar Dispositivos por Usuário**
```sql
-- Dispositivos acessíveis por usuário
SELECT 
    u.name as usuario,
    d.name as dispositivo,
    d.unique_id,
    g.name as grupo,
    CASE 
        WHEN u.is_admin THEN 'Admin'
        WHEN udp.device_id IS NOT NULL THEN 'Direto'
        WHEN ugp.group_id IS NOT NULL THEN 'Grupo'
        ELSE 'Sem Acesso'
    END as tipo_acesso
FROM users u
CROSS JOIN devices d
LEFT JOIN user_device_permissions udp ON u.id = udp.user_id AND d.id = udp.device_id
LEFT JOIN user_group_permissions ugp ON u.id = ugp.user_id AND d.group_id = ugp.group_id
WHERE u.is_admin = true 
   OR udp.device_id IS NOT NULL 
   OR ugp.group_id IS NOT NULL
ORDER BY u.name, d.name;
```

### **Relatório de Permissões**
```sql
-- Relatório completo de permissões
SELECT 
    u.name as usuario,
    u.email,
    u.is_admin,
    u.is_active,
    COUNT(DISTINCT ugp.group_id) as grupos,
    COUNT(DISTINCT udp.device_id) as dispositivos_diretos,
    COUNT(DISTINCT umu.managed_user_id) as usuarios_gerenciados,
    u.created_at
FROM users u
LEFT JOIN user_group_permissions ugp ON u.id = ugp.user_id
LEFT JOIN user_device_permissions udp ON u.id = udp.user_id
LEFT JOIN user_managed_users umu ON u.id = umu.user_id
GROUP BY u.id, u.name, u.email, u.is_admin, u.is_active, u.created_at
ORDER BY u.is_admin DESC, u.created_at DESC;
```

## 🚨 Troubleshooting

### **Problema: Usuário não consegue ver dispositivos**

#### **Diagnóstico**
```bash
# 1. Verificar se usuário existe e está ativo
docker compose -f docker-compose.dev.yml exec postgres psql -U traccar -d traccar -c "SELECT id, name, email, is_active FROM users WHERE email = 'usuario@exemplo.com';"

# 2. Verificar permissões de grupo
docker compose -f docker-compose.dev.yml exec postgres psql -U traccar -d traccar -c "SELECT ugp.user_id, ugp.group_id, g.name FROM user_group_permissions ugp JOIN groups g ON ugp.group_id = g.id WHERE ugp.user_id = [ID_USUARIO];"

# 3. Verificar dispositivos e grupos
docker compose -f docker-compose.dev.yml exec postgres psql -U traccar -d traccar -c "SELECT d.id, d.name, d.group_id, g.name as grupo FROM devices d LEFT JOIN groups g ON d.group_id = g.id;"
```

#### **Soluções**
1. **Usuário sem permissões**: Atribuir permissões de grupo
2. **Dispositivos sem grupo**: Mover dispositivos para grupos ou atribuir permissão direta
3. **Usuário inativo**: Ativar usuário
4. **Token expirado**: Fazer login novamente

### **Problema: Erro de permissão ao criar grupo**

#### **Diagnóstico**
```bash
# Verificar se usuário tem permissão para criar grupos
curl -X GET "http://localhost:8000/api/users/me" \
  -H "Authorization: Bearer $TOKEN"
```

#### **Soluções**
1. **Usuário não é admin**: Usar conta de administrador
2. **Grupo pai não existe**: Verificar ID do grupo pai
3. **Nome duplicado**: Usar nome único para o grupo

### **Problema: Herança de permissões não funciona**

#### **Diagnóstico**
```bash
# Verificar hierarquia de grupos
docker compose -f docker-compose.dev.yml exec postgres psql -U traccar -d traccar -c "SELECT id, name, parent_id FROM groups ORDER BY parent_id, id;"
```

#### **Soluções**
1. **Referência circular**: Verificar se não há loops na hierarquia
2. **Grupo pai inativo**: Ativar grupo pai
3. **Permissão não atribuída**: Atribuir permissão no grupo pai

## 📚 Comandos Úteis

### **Backup de Permissões**
```bash
# Backup completo de usuários e permissões
docker compose -f docker-compose.dev.yml exec postgres pg_dump -U traccar -d traccar \
  --table=users \
  --table=groups \
  --table=user_group_permissions \
  --table=user_device_permissions \
  --table=user_managed_users \
  > backup_usuarios_$(date +%Y%m%d_%H%M%S).sql
```

### **Restaurar Permissões**
```bash
# Restaurar backup
docker compose -f docker-compose.dev.yml exec -T postgres psql -U traccar -d traccar < backup_usuarios_20250106_120000.sql
```

### **Limpeza de Dados**
```bash
# Remover usuários inativos há mais de 90 dias
docker compose -f docker-compose.dev.yml exec postgres psql -U traccar -d traccar -c "
DELETE FROM users 
WHERE is_active = false 
  AND updated_at < NOW() - INTERVAL '90 days';"
```

### **Estatísticas do Sistema**
```bash
# Estatísticas gerais
docker compose -f docker-compose.dev.yml exec postgres psql -U traccar -d traccar -c "
SELECT 
    'Usuários' as tipo,
    COUNT(*) as total,
    COUNT(CASE WHEN is_active THEN 1 END) as ativos,
    COUNT(CASE WHEN is_admin THEN 1 END) as admins
FROM users
UNION ALL
SELECT 
    'Grupos' as tipo,
    COUNT(*) as total,
    COUNT(CASE WHEN NOT disabled THEN 1 END) as ativos,
    COUNT(CASE WHEN parent_id IS NULL THEN 1 END) as raiz
FROM groups
UNION ALL
SELECT 
    'Dispositivos' as tipo,
    COUNT(*) as total,
    COUNT(CASE WHEN NOT disabled THEN 1 END) as ativos,
    COUNT(CASE WHEN group_id IS NOT NULL THEN 1 END) as com_grupo
FROM devices;"
```

---

**Última Atualização**: 06 de Janeiro de 2025  
**Versão**: 1.0.0  
**Status**: ✅ **GUIA COMPLETO E FUNCIONAL**
