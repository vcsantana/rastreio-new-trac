# 🗄️ Guia de Acesso ao PostgreSQL

## 📋 **Configurações do Banco de Dados**

### **PostgreSQL (Docker)**
- **Host:** `localhost` ou `127.0.0.1`
- **Port:** `5432`
- **Database:** `traccar`
- **Username:** `traccar`
- **Password:** `traccar123`

---

## 🚀 **Opções de Acesso**

### **Opção 1: pgAdmin no Docker (Recomendado)**

1. **Iniciar os serviços:**
   ```bash
   cd /Users/vandecarlossantana/Documents/traccar/new
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. **Acessar pgAdmin:**
   - URL: http://localhost:5050
   - Email: `admin@traccar.com`
   - Senha: `admin123`

3. **Adicionar servidor PostgreSQL:**
   - Clique em "Add New Server"
   - **General Tab:**
     - Name: `Traccar PostgreSQL`
   - **Connection Tab:**
     - Host: `postgres` (nome do serviço no Docker)
     - Port: `5432`
     - Database: `traccar`
     - Username: `traccar`
     - Password: `traccar123`

### **Opção 2: pgAdmin Local**

Se você tem pgAdmin instalado localmente:

1. **Configurações de conexão:**
   - Host: `localhost`
   - Port: `5432`
   - Database: `traccar`
   - Username: `traccar`
   - Password: `traccar123`

### **Opção 3: Terminal/CLI**

```bash
# Acessar via Docker
docker exec -it new-postgres-1 psql -U traccar -d traccar

# Comandos úteis no psql:
\dt                    # Listar tabelas
\d table_name          # Descrever tabela
\q                     # Sair
```

---

## 📊 **Tabelas Principais do Traccar**

### **Tabelas de Dispositivos e Posições:**
- `devices` - Dispositivos GPS
- `positions` - Posições dos dispositivos
- `events` - Eventos (alarmes, etc.)
- `users` - Usuários do sistema
- `groups` - Grupos de dispositivos
- `geofences` - Cercas virtuais

### **Consultas Úteis:**

```sql
-- Ver todos os dispositivos
SELECT * FROM devices;

-- Ver últimas posições
SELECT d.name, p.latitude, p.longitude, p.servertime 
FROM positions p 
JOIN devices d ON p.deviceid = d.id 
ORDER BY p.servertime DESC 
LIMIT 10;

-- Ver eventos recentes
SELECT d.name, e.type, e.servertime 
FROM events e 
JOIN devices d ON e.deviceid = d.id 
ORDER BY e.servertime DESC 
LIMIT 10;
```

---

## 🔧 **Comandos Docker Úteis**

```bash
# Ver status dos containers
docker ps

# Ver logs do PostgreSQL
docker logs new-postgres-1

# Parar todos os serviços
docker-compose -f docker-compose.dev.yml down

# Reiniciar apenas o PostgreSQL
docker-compose -f docker-compose.dev.yml restart postgres

# Backup do banco
docker exec new-postgres-1 pg_dump -U traccar traccar > backup.sql

# Restaurar backup
docker exec -i new-postgres-1 psql -U traccar -d traccar < backup.sql
```

---

## 🎯 **Próximos Passos**

1. **Iniciar os serviços** com pgAdmin incluído
2. **Acessar pgAdmin** em http://localhost:5050
3. **Configurar conexão** com o PostgreSQL
4. **Explorar as tabelas** e dados do Traccar
5. **Executar consultas** para análise dos dados

---

## ⚠️ **Notas Importantes**

- O pgAdmin no Docker salva as configurações no volume `pgadmin_data`
- As credenciais padrão do pgAdmin são: `admin@traccar.com` / `admin123`
- O PostgreSQL está configurado para aceitar conexões externas na porta 5432
- Todos os dados são persistidos nos volumes Docker
